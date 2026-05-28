"""
Diagnostic B22 — Synchronisation absences ↔ planning (flag inovaya_conflit_absence).
bench --site inovaya.localhost execute inovaya_gdp.setup.diag_b22.run
"""
import frappe
import unittest.mock as mock


def run():
    print("\n" + "="*65)
    print("  DIAGNOSTIC B22 — Flag inovaya_conflit_absence sur Task")
    print("="*65)

    # ── 1. Vérifier que le champ existe ──────────────────────────────────
    print("\n[1] CHAMP CUSTOM inovaya_conflit_absence")
    cf = frappe.db.get_value(
        "Custom Field",
        "Task-inovaya_conflit_absence",
        ["fieldname", "label", "fieldtype", "read_only"],
        as_dict=True,
    )
    if cf:
        print(f"  ✅ {cf.fieldname} | {cf.label} | {cf.fieldtype} | read_only={cf.read_only}")
    else:
        print("  ❌ Champ introuvable en base — relancer bench migrate")
        return

    # ── 2. Hooks enregistrés ──────────────────────────────────────────────
    print("\n[2] HOOKS Leave Application")
    hooks = frappe.get_hooks("doc_events", app_name="inovaya_gdp")
    la_hooks = hooks.get("Leave Application", {})
    for event, handler in la_hooks.items():
        h = handler[0] if isinstance(handler, list) else handler
        expected = {
            "on_submit": "inovaya_gdp.overrides.leave_application.on_submit",
            "on_cancel": "inovaya_gdp.overrides.leave_application.on_cancel",
        }
        flag = "✅" if expected.get(event) == h else "⚠️"
        print(f"  {flag} {event} → {h}")
    if "on_cancel" not in la_hooks:
        print("  ❌ on_cancel manquant !")

    # ── 3. État initial du flag sur les tâches ────────────────────────────
    print("\n[3] ÉTAT ACTUEL flag inovaya_conflit_absence (avant test)")
    tasks_with_flag = frappe.db.sql(
        "SELECT name, subject FROM `tabTask` WHERE inovaya_conflit_absence = 1",
        as_dict=True,
    )
    if tasks_with_flag:
        for t in tasks_with_flag:
            print(f"  ⚠️ [{t.name}] {t.subject} — déjà marqué")
    else:
        print("  ✅ Aucune tâche marquée (état propre)")

    # ── 4. Simulation on_submit ──────────────────────────────────────────
    print("\n[4] SIMULATION on_submit (Leave Application Inès Faure)")
    la = frappe.db.get_value(
        "Leave Application",
        {"employee_name": "Inès Faure", "docstatus": 1},
        ["name", "employee"],
        as_dict=True,
    )
    if not la:
        print("  ❌ Aucune Leave Application soumise pour Inès Faure.")
        return

    doc = frappe.get_doc("Leave Application", la.name)
    from inovaya_gdp.overrides.leave_application import on_submit as _on_submit

    sent = []
    with mock.patch("frappe.sendmail", side_effect=lambda **kw: sent.append(kw)):
        _on_submit(doc)

    # Vérifier que les tâches en conflit sont maintenant marquées
    from inovaya_gdp.overrides.leave_application import _get_user_email, _find_conflicting_tasks
    from frappe.utils import getdate
    user_email = _get_user_email(la.employee)
    tasks = _find_conflicting_tasks(
        user_email,
        getdate(doc.from_date),
        getdate(doc.to_date),
    )

    print(f"  Tâches en conflit détectées : {len(tasks)}")
    for t in tasks:
        flag_val = frappe.db.get_value("Task", t.name, "inovaya_conflit_absence")
        flag_ok = "✅" if flag_val else "❌"
        print(f"  {flag_ok} [{t.name}] {t.subject} — inovaya_conflit_absence={flag_val}")

    if sent:
        print(f"  ✅ Mail simulé → {sent[0].get('recipients')}")
    else:
        print("  ⚠️  Aucun mail (pas de destinataires ou pas de conflit)")

    # ── 5. Simulation on_cancel ──────────────────────────────────────────
    print("\n[5] SIMULATION on_cancel (réinitialisation)")
    from inovaya_gdp.overrides.leave_application import on_cancel as _on_cancel
    _on_cancel(doc)

    # Vérifier que les flags ont été réinitialisés
    print("  État après on_cancel :")
    for t in tasks:
        flag_val = frappe.db.get_value("Task", t.name, "inovaya_conflit_absence")
        flag_ok = "✅ réinitialisé" if not flag_val else "❌ toujours marqué"
        print(f"  {flag_ok} [{t.name}] {t.subject} — inovaya_conflit_absence={flag_val}")

    # ── 6. Remettre l'état propre ─────────────────────────────────────────
    frappe.db.rollback()
    print("\n[6] ROLLBACK — état DB restauré (aucun flag en production)")

    print("\n" + "="*65 + "\n")
