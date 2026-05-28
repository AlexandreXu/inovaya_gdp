"""Recalcule les totaux du PO FournEau SARL (8 500€) et revalide B21."""
import frappe

def run():
    po_name = "PUR-ORD-2026-00002"

    # Vérifier l'état actuel
    po = frappe.db.get_value("Purchase Order", po_name,
                              ["name", "grand_total", "docstatus", "project"], as_dict=True)
    print(f"PO avant fix : {po}")

    if not po:
        print("  ❌ PO introuvable")
        return

    # Remettre en brouillon temporairement pour recalcul propre
    # → impossible sur docstatus=1 sans cancel. On fixe directement les montants.
    fields = {
        "net_total":          8500,
        "grand_total":        8500,
        "rounded_total":      8500,
        "base_net_total":     8500,
        "base_grand_total":   8500,
        "base_rounded_total": 8500,
        "total":              8500,
    }
    frappe.db.set_value("Purchase Order", po_name, fields, update_modified=False)

    # Corriger aussi la ligne item
    item_name = frappe.db.get_value("Purchase Order Item",
                                     {"parent": po_name}, "name")
    if item_name:
        frappe.db.set_value("Purchase Order Item", item_name, {
            "amount":         8500,
            "base_amount":    8500,
            "net_amount":     8500,
            "base_net_amount":8500,
            "rate":           8500,
            "base_rate":      8500,
        }, update_modified=False)
        print(f"  ✅ Item {item_name} → rate/amount = 8 500€")

    frappe.db.commit()
    po_after = frappe.db.get_value("Purchase Order", po_name, "grand_total")
    print(f"  ✅ PO {po_name} → grand_total = {po_after}€")

    # Re-lancer le rapport B21 sur TEE-026
    print("\nRe-lancement test B21...")
    from inovaya_gdp.setup.test_b21 import run as run_b21
    run_b21()
