"""
Diagnostic B06 — Alimentation auto Timesheet draft lors d'une assignation.
Teste la fonction _create_draft_timesheets_b06 de overrides/task.py.
bench --site inovaya.localhost execute inovaya_gdp.setup.diag_b06.run
"""
import frappe
import json


def run():
    print("\n=== DIAGNOSTIC B06 — Timesheet draft auto ===")

    # ── 1. Hooks Task ──────────────────────────────────────────────────────
    print("\n[1] HOOKS Task")
    hooks = frappe.get_hooks("doc_events", app_name="inovaya_gdp")
    for ev in ["before_save", "after_save"]:
        h = hooks.get("Task", {}).get(ev)
        if h:
            handler = h[0] if isinstance(h, list) else h
            print(f"  ✅ {ev} → {handler}")
        else:
            print(f"  ❌ {ev} manquant")

    # ── 2. Trouver une tâche et un employé de test ─────────────────────────
    task = frappe.db.sql("""
        SELECT name, subject, project, exp_start_date, exp_end_date, expected_time,
               inovaya_hours_per_day
        FROM `tabTask`
        WHERE is_template = 0
          AND exp_start_date IS NOT NULL
          AND exp_end_date IS NOT NULL
          AND status NOT IN ('Completed', 'Cancelled')
        ORDER BY name LIMIT 1
    """, as_dict=True)[0]

    emp = frappe.db.get_value("Employee", "HR-EMP-00001",
                               ["name", "employee_name", "user_id"], as_dict=True)
    print(f"\n[2] Tâche : [{task.name}] {task.subject} ({task.exp_start_date}→{task.exp_end_date})")
    print(f"    Employé : {emp.employee_name} ({emp.user_id})")

    # ── 3. Compter les TS avant ──────────────────────────────────────────
    ts_before = frappe.db.sql("""
        SELECT td.parent FROM `tabTimesheet Detail` td
        INNER JOIN `tabTimesheet` ts ON ts.name = td.parent
        WHERE td.task = %s AND ts.employee = %s AND ts.docstatus = 0
    """, (task.name, emp.name))
    print(f"\n[3] Timesheets draft existantes avant test : {len(ts_before)}")

    # ── 4. Appeler la vraie fonction B06 ──────────────────────────────────
    from inovaya_gdp.overrides.task import _create_draft_timesheets_b06

    # Construire un pseudo-doc task
    doc = frappe.get_doc("Task", task.name)
    doc._b06_new_users = [emp.user_id]  # Forcer l'assignation

    print(f"\n[4] Appel _create_draft_timesheets_b06([{emp.user_id}])")
    _create_draft_timesheets_b06(doc, [emp.user_id])

    # ── 5. Vérifier la création ──────────────────────────────────────────
    ts_after = frappe.db.sql("""
        SELECT td.parent, ts.employee_name, td.hours, td.from_time, td.to_time, td.description
        FROM `tabTimesheet Detail` td
        INNER JOIN `tabTimesheet` ts ON ts.name = td.parent
        WHERE td.task = %s AND ts.employee = %s AND ts.docstatus = 0
        ORDER BY ts.creation DESC LIMIT 3
    """, (task.name, emp.name), as_dict=True)

    if ts_after:
        for t in ts_after:
            print(f"  ✅ {t.parent} | {t.employee_name} | {t.hours}h | {str(t.from_time)[:16]}→{str(t.to_time)[:16]}")
    else:
        print("  ❌ Aucune Timesheet draft créée")

    # ── 6. Test idempotence (2ème appel) ──────────────────────────────────
    print(f"\n[5] Test idempotence — 2ème appel")
    count_before = len(ts_after)
    _create_draft_timesheets_b06(doc, [emp.user_id])
    ts_after2 = frappe.db.sql("""
        SELECT td.parent FROM `tabTimesheet Detail` td
        INNER JOIN `tabTimesheet` ts ON ts.name = td.parent
        WHERE td.task = %s AND ts.employee = %s AND ts.docstatus = 0
    """, (task.name, emp.name))
    count_after = len(ts_after2)
    if count_after == count_before:
        print(f"  ✅ Idempotent — {count_after} Timesheet(s), pas de doublon")
    else:
        print(f"  ❌ Doublon créé ({count_before} → {count_after})")

    # ── Rollback ──────────────────────────────────────────────────────────
    frappe.db.rollback()
    print("\n  → Rollback effectué (état propre)")
    print("\n=== FIN DIAGNOSTIC B06 ===\n")
