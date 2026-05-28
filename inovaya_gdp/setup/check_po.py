"""Vérifie le champ project sur le PO FournEau SARL."""
import frappe

def run():
    rows = frappe.db.sql("""
        SELECT name, supplier, grand_total, docstatus, project
        FROM `tabPurchase Order`
        WHERE supplier = 'FournEau SARL'
    """, as_dict=True)
    print("Purchase Orders FournEau SARL :")
    for r in rows:
        print(f"  {r.name} | docstatus={r.docstatus} | project={r.project!r} | total={r.grand_total}€")
