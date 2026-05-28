"""
Diagnostic B20 — Budget ETPs depuis Timesheets.
bench --site inovaya.localhost execute inovaya_gdp.setup.diag_b20.run
"""
import frappe


def run():
    print("\n=== DIAGNOSTIC B20 — Budget ETPs ===")

    # 1. Taux horaire
    from inovaya_gdp.overrides.budget_update import _get_hourly_rate
    rate = _get_hourly_rate()
    print(f"[1] Taux horaire System Settings : {rate} €/h")
    if rate <= 0:
        print("  ⚠️  Taux = 0 — seeder un taux dans System Settings")
        # Seeder pour le test
        frappe.db.set_single_value("System Settings", "inovaya_default_hourly_rate", 75.0)
        frappe.db.commit()
        rate = 75.0
        print(f"  → Taux seedé : {rate} €/h")

    # 2. Timesheets soumises par projet
    print("\n[2] Heures soumises par projet :")
    rows = frappe.db.sql("""
        SELECT td.project, ROUND(SUM(td.hours), 2) AS total_hours
        FROM `tabTimesheet Detail` td
        INNER JOIN `tabTimesheet` ts ON ts.name = td.parent AND ts.docstatus = 1
        WHERE td.project IS NOT NULL AND td.project != ''
        GROUP BY td.project
    """, as_dict=True)
    for r in rows:
        print(f"  {r.project} : {r.total_hours}h → {round(r.total_hours * rate, 2)} €")
    if not rows:
        print("  ⚠️  Aucune Timesheet soumise avec projet")

    # 3. État Budget Detaille avant
    print("\n[3] Budget ETPs avant mise à jour :")
    budget_rows = frappe.db.sql(
        "SELECT parent, category, amount_planned, amount_actual FROM `tabBudget Detaille InovaYa` WHERE category='ETPs'",
        as_dict=True,
    )
    for b in budget_rows:
        print(f"  {b.parent} | planned={b.amount_planned} | actual={b.amount_actual}")

    # 4. Exécuter B20
    print("\n[4] Exécution budget_update.run() :")
    from inovaya_gdp.overrides.budget_update import run as _b20_run
    updated = _b20_run()
    print(f"  Résultat : {updated} projet(s) mis à jour")

    # 5. État Budget Detaille après
    print("\n[5] Budget ETPs après mise à jour :")
    budget_rows2 = frappe.db.sql(
        "SELECT parent, category, amount_planned, amount_actual FROM `tabBudget Detaille InovaYa` WHERE category='ETPs'",
        as_dict=True,
    )
    for b in budget_rows2:
        flag = "✅" if b.amount_actual and b.amount_actual > 0 else "⚠️"
        print(f"  {flag} {b.parent} | planned={b.amount_planned} | actual={b.amount_actual}")

    print("\n=== FIN DIAGNOSTIC B20 ===\n")
