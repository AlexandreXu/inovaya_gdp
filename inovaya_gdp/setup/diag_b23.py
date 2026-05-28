"""
Diagnostic B23 — Alertes congé vs tâches.
bench --site inovaya.localhost execute inovaya_gdp.setup.diag_b23.run
"""
import frappe


def run():
    print("\n" + "="*65)
    print("  DIAGNOSTIC B23 — Congé Inès Faure vs Tâches projet")
    print("="*65)

    # ── 1. Données Leave Application d'Inès ─────────────────────────────
    la = frappe.db.get_value(
        "Leave Application",
        {"employee_name": "Inès Faure", "docstatus": 1},
        ["name", "employee", "employee_name", "from_date", "to_date", "leave_type"],
        as_dict=True,
    )
    if not la:
        print("  ❌ Aucune Leave Application soumise pour Inès Faure.")
        return

    print(f"\n[1] LEAVE APPLICATION : {la.name}")
    print(f"  Employée   : {la.employee_name} ({la.employee})")
    print(f"  Congé      : {la.from_date} → {la.to_date}")
    print(f"  Type       : {la.leave_type}")

    # ── 2. Résolution user_id ────────────────────────────────────────────
    from inovaya_gdp.overrides.leave_application import (
        _get_user_email,
        _get_manager_email,
        _find_conflicting_tasks,
        _get_project_owner_email,
    )

    user_email    = _get_user_email(la.employee)
    manager_email = _get_manager_email(la.employee)

    print(f"\n[2] RÉSOLUTION EMAILS")
    print(f"  User email    : {user_email or '❌ INTROUVABLE'}")
    print(f"  Manager email : {manager_email or '❌ INTROUVABLE'}")

    # ── 3. Tâches en conflit ─────────────────────────────────────────────
    print(f"\n[3] TÂCHES EN CONFLIT ({la.from_date} → {la.to_date})")
    tasks = _find_conflicting_tasks(
        user_email,
        frappe.utils.getdate(la.from_date),
        frappe.utils.getdate(la.to_date),
    )

    if not tasks:
        print("  ⚠️  Aucune tâche en conflit trouvée.")
        print("  → Vérification directe SQL :")
        rows = frappe.db.sql(
            """
            SELECT name, subject, project, DATE(exp_start_date) s, DATE(exp_end_date) e, _assign
            FROM `tabTask`
            WHERE is_template = 0
              AND status NOT IN ('Completed','Cancelled')
              AND exp_start_date IS NOT NULL
            ORDER BY exp_start_date
            LIMIT 20
            """,
            as_dict=True,
        )
        for r in rows:
            flag = "🎯" if r.get("_assign") and user_email in (r.get("_assign") or "") else "  "
            print(f"  {flag} [{r.project or 'sans projet'}] {r.subject}  {r.s}→{r.e}  assign={r._assign}")
    else:
        for t in tasks:
            print(f"  ✅ [{t.project or 'sans projet'}] {t.subject}  ({t.start_date} → {t.end_date})")

    # ── 4. Destinataires ─────────────────────────────────────────────────
    print(f"\n[4] DESTINATAIRES")
    recipients = set()
    if manager_email:
        recipients.add(manager_email)
    for t in tasks:
        if t.project:
            oe = _get_project_owner_email(t.project)
            if oe:
                recipients.add(oe)
    print(f"  {sorted(recipients) or '❌ Aucun destinataire'}")

    # ── 5. Vérification hook enregistré ──────────────────────────────────
    print(f"\n[5] HOOKS doc_events Leave Application")
    hooks = frappe.get_hooks("doc_events", app_name="inovaya_gdp")
    la_hooks = hooks.get("Leave Application", {})
    for event, handler in la_hooks.items():
        h = handler[0] if isinstance(handler, list) else handler
        print(f"  ✅ {event} → {h}")
    if not la_hooks:
        print("  ❌ Aucun hook Leave Application enregistré !")

    # ── 6. Simulation on_submit ──────────────────────────────────────────
    print(f"\n[6] SIMULATION on_submit (sans envoi mail réel)")
    doc = frappe.get_doc("Leave Application", la.name)
    from inovaya_gdp.overrides.leave_application import on_submit as _on_submit
    import unittest.mock as mock
    sent = []
    with mock.patch("frappe.sendmail", side_effect=lambda **kw: sent.append(kw)):
        try:
            _on_submit(doc)
            if sent:
                print(f"  ✅ Mail simulé → {sent[0].get('recipients')}")
                print(f"  Subject : {sent[0].get('subject')}")
            else:
                print(f"  ⚠️  on_submit exécuté sans sendmail (pas de conflit ou pas de destinataire)")
        except Exception as e:
            print(f"  ❌ Exception : {e}")

    print("\n" + "="*65 + "\n")
