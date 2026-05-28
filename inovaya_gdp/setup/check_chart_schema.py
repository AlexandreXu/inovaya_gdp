"""
Vérification schéma Dashboard Chart v16.
bench --site inovaya.localhost execute inovaya_gdp.setup.check_chart_schema.run
"""
import frappe


def run():
    print("\n=== DASHBOARD CHART — SCHEMA ===")
    cols = frappe.db.sql("DESCRIBE `tabDashboard Chart`", as_dict=True)
    for c in cols:
        print(f"  {c['Field']} ({c['Type']})")

    print("\n=== DASHBOARD CHART — EXISTANTS ===")
    charts = frappe.db.sql(
        "SELECT * FROM `tabDashboard Chart` LIMIT 3", as_dict=True
    )
    for c in charts:
        print(f"  {c}")
