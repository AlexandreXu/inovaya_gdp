"""Vérifie le schéma tabTimesheet et tabTimesheet Detail pour le projet TEE-026."""
import frappe

def run():
    # Colonnes de tabTimesheet
    ts_cols = frappe.db.sql("DESCRIBE `tabTimesheet`", as_dict=True)
    print("tabTimesheet — colonnes :")
    for c in ts_cols:
        print(f"  {c.Field}")

    print()
    tsd_cols = frappe.db.sql("DESCRIBE `tabTimesheet Detail`", as_dict=True)
    print("tabTimesheet Detail — colonnes :")
    for c in tsd_cols:
        print(f"  {c.Field}")

    # Chercher la timesheet démo
    ts = frappe.db.sql("""
        SELECT ts.name, ts.title, ts.docstatus,
               tsd.project AS tsd_project, tsd.hours
        FROM `tabTimesheet` ts
        JOIN `tabTimesheet Detail` tsd ON tsd.parent = ts.name
        WHERE ts.title = 'DEMO-TS-Lea'
    """, as_dict=True)
    print(f"\nTimesheet DEMO-TS-Lea :")
    for row in ts:
        print(f"  {row}")
