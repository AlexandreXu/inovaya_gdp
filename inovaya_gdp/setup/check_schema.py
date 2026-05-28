"""
Vérification schéma pour B06/B20.
bench --site inovaya.localhost execute inovaya_gdp.setup.check_schema.run
"""
import frappe


def run():
    print("\n=== CUSTOM FIELDS inovaya_ ===")
    rows = frappe.db.sql(
        "SELECT dt, fieldname, label, fieldtype FROM `tabCustom Field` WHERE fieldname LIKE 'inovaya_%' ORDER BY dt, fieldname",
        as_dict=True,
    )
    for r in rows:
        print(f"  {r.dt:<35} {r.fieldname:<35} {r.fieldtype}")

    print("\n=== BUDGET DETAILLE INOVAYA (exemples) ===")
    brows = frappe.db.sql(
        "SELECT parent, category, amount_planned, amount_actual FROM `tabBudget Detaille InovaYa` LIMIT 15",
        as_dict=True,
    )
    for b in brows:
        print(f"  parent={b.parent} | cat='{b.category}' | planned={b.amount_planned} | actual={b.amount_actual}")

    print("\n=== TASK expected_time ===")
    tasks = frappe.db.sql(
        "SELECT name, subject, expected_time FROM `tabTask` WHERE is_template=0 AND expected_time > 0 LIMIT 5",
        as_dict=True,
    )
    for t in tasks:
        print(f"  {t.name} | {t.subject} | expected_time={t.expected_time}h")

    print("\n=== TIMESHEET DETAIL avec task et employee ===")
    td = frappe.db.sql("""
        SELECT td.name, td.task, td.project, td.hours, td.from_time,
               ts.employee, ts.employee_name, ts.docstatus
        FROM `tabTimesheet Detail` td
        JOIN `tabTimesheet` ts ON ts.name = td.parent
        ORDER BY td.from_time DESC
        LIMIT 8
    """, as_dict=True)
    for r in td:
        print(f"  task={r.task} | emp={r.employee_name} | h={r.hours} | docstatus={r.docstatus} | from={str(r.from_time)[:10]}")

    print()
