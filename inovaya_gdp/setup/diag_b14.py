"""
Diagnostic B14 — Alertes retard commande → impact planning.
bench --site inovaya.localhost execute inovaya_gdp.setup.diag_b14.run
"""
import frappe
import unittest.mock as mock
from frappe.utils import getdate, add_days


def run():
    print("\n=== DIAGNOSTIC B14 — Alertes retard PO ===")

    # ── 1. Hooks enregistrés ───────────────────────────────────────────────
    print("\n[1] HOOKS Purchase Order")
    hooks = frappe.get_hooks("doc_events", app_name="inovaya_gdp")
    po_hooks = hooks.get("Purchase Order", {})
    for ev in ["before_save", "on_update", "on_submit"]:
        h = po_hooks.get(ev)
        handler = (h[0] if isinstance(h, list) else h) if h else None
        flag = "✅" if handler else "❌"
        print(f"  {flag} {ev} → {handler or 'MANQUANT'}")

    # ── 2. Préparer les données de test ────────────────────────────────────
    print("\n[2] PRÉPARATION DONNÉES DE TEST")

    # Trouver PO et tâche de démo
    po = frappe.db.get_value("Purchase Order", {"docstatus": 1},
                              ["name", "supplier_name", "schedule_date", "inovaya_linked_task"],
                              as_dict=True)
    if not po:
        print("  ❌ Aucun Purchase Order soumis en base")
        return
    print(f"  PO : {po.name} | {po.supplier_name} | schedule={po.schedule_date}")

    # Trouver une tâche avec projet et dates
    task = frappe.db.sql("""
        SELECT name, subject, project, exp_end_date
        FROM `tabTask`
        WHERE is_template=0 AND project IS NOT NULL
          AND exp_end_date IS NOT NULL AND status NOT IN ('Completed','Cancelled')
        ORDER BY name LIMIT 1
    """, as_dict=True)
    if not task:
        print("  ❌ Aucune tâche avec projet trouvée")
        return
    task = task[0]
    print(f"  Tâche test : [{task.name}] {task.subject} | projet={task.project} | exp_end={task.exp_end_date}")

    # ── 3. Simuler le PO avec inovaya_linked_task et date en retard ────────
    print("\n[3] SIMULATION before_save + on_update")
    from inovaya_gdp.overrides.purchase_order import before_save as _before_save, on_update as _on_update

    doc = frappe.get_doc("Purchase Order", po.name)
    doc.inovaya_linked_task = task.name
    # Nouvelle date de livraison = exp_end_date + 15 jours (retard)
    new_schedule_date = str(add_days(getdate(task.exp_end_date), 15))
    doc.schedule_date = new_schedule_date
    print(f"  schedule_date simulée : {new_schedule_date} (retard de 15j vs {task.exp_end_date})")

    _before_save(doc)
    alert_data = getattr(doc, "_b14_alert_data", None)
    if alert_data:
        print(f"  ✅ _b14_alert_data calculé")
        print(f"     Retard : {alert_data['new_date']} > {alert_data['task_end']}")
    else:
        print("  ❌ _b14_alert_data est None")
        return

    # Appeler on_update avec mock sendmail
    sent = []
    with mock.patch("frappe.sendmail", side_effect=lambda **kw: sent.append(kw)):
        _on_update(doc)

    if sent:
        print(f"\n  ✅ Email simulé → {sent[0].get('recipients')}")
        print(f"  Subject : {sent[0].get('subject')}")
    else:
        print("  ⚠️  Aucun mail (vérifier les destinataires)")

    # ── 4. Test cas "pas de retard" (pas d'alerte attendue) ───────────────
    print("\n[4] TEST CAS SANS RETARD (date = exp_end_date)")
    doc2 = frappe.get_doc("Purchase Order", po.name)
    doc2.inovaya_linked_task = task.name
    doc2.schedule_date = str(task.exp_end_date)  # Même date → pas de retard
    _before_save(doc2)
    alert2 = getattr(doc2, "_b14_alert_data", None)
    if alert2 is None:
        print("  ✅ Pas d'alerte (schedule_date == task.exp_end_date)")
    else:
        print("  ❌ Alerte incorrecte pour une date non en retard")

    # ── 5. Test cas sans inovaya_linked_task ──────────────────────────────
    print("\n[5] TEST CAS SANS TÂCHE LIÉE")
    doc3 = frappe.get_doc("Purchase Order", po.name)
    doc3.inovaya_linked_task = None
    doc3.schedule_date = new_schedule_date
    _before_save(doc3)
    alert3 = getattr(doc3, "_b14_alert_data", None)
    if alert3 is None:
        print("  ✅ Pas d'alerte sans tâche liée (comportement correct)")
    else:
        print("  ❌ Alerte incorrecte sans tâche liée")

    print("\n=== FIN DIAGNOSTIC B14 ===\n")
