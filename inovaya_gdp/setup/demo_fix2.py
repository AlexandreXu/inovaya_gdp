"""
Fix 2 — Ciblé :
1. Assigner Holiday List directement sur Employee Inès + force-delete LA existante
2. Ajouter company sur Purchase Order

Usage : bench --site inovaya.localhost execute inovaya_gdp.setup.demo_fix2.run
"""
import frappe
from frappe.utils import today, getdate, add_days

def run():
    today_d = getdate(today())
    company = (frappe.db.get_single_value("Global Defaults", "default_company")
               or frappe.db.get_all("Company", limit=1, pluck="name")[0])
    HL_NAME = "InovaYa 2026"

    # ── FIX 1 : Holiday List sur l'Employee Inès directement ─────────────────
    print("\n=== FIX 1 : HOLIDAY LIST SUR EMPLOYEE INÈS ===")
    ines_emp = frappe.db.get_value("Employee", {"user_id": "ines.faure@inovaya.com"}, "name")
    if not ines_emp:
        print("  ❌ Employee Inès introuvable")
        return

    # Assigner la Holiday List sur l'Employee + la company (double sécurité)
    frappe.db.set_value("Employee", ines_emp, "holiday_list", HL_NAME)
    frappe.db.set_value("Company",  company,  "default_holiday_list", HL_NAME)
    frappe.db.commit()
    print(f"  ✅ Employee {ines_emp} → holiday_list = {HL_NAME}")
    print(f"  ✅ Company {company} → default_holiday_list = {HL_NAME}")

    # Force-delete les LAs existantes via SQL (bypass hrms validation)
    existing_las = frappe.db.get_all("Leave Application",
                                      filters={"employee": ines_emp}, pluck="name")
    for la_name in existing_las:
        # Supprimer les dépendances child tables d'abord
        frappe.db.sql("DELETE FROM `tabLeave Application` WHERE name = %s", la_name)
        print(f"  🗑 LA force-supprimée : {la_name}")
    frappe.db.commit()

    # ── FIX 2 : Leave Application Inès (B23) ─────────────────────────────────
    print("\n=== FIX 2 : LEAVE APPLICATION INÈS ===")
    try:
        la = frappe.get_doc({
            "doctype": "Leave Application",
            "employee": ines_emp, "employee_name": "Inès Faure",
            "leave_type": "Congés payés",
            "from_date": str(add_days(today_d, 14)),
            "to_date":   str(add_days(today_d, 18)),
            "status": "Approved", "posting_date": str(today_d), "half_day": 0,
        })
        la.flags.ignore_validate  = True
        la.flags.ignore_mandatory = True
        la.insert(ignore_permissions=True)
        frappe.flags.in_test = False   # Laisser B23 se déclencher
        la.submit()
        frappe.flags.in_test = False
        frappe.db.commit()
        print(f"  ✅ Leave Application soumise : {la.name}")

        # Vérifier B23
        from inovaya_gdp.overrides.leave_application import _find_conflicting_tasks, _get_user_email
        ue       = _get_user_email(ines_emp)
        conflicts = _find_conflicting_tasks(ue, getdate(add_days(today_d, 14)),
                                             getdate(add_days(today_d, 18)))
        if conflicts:
            print(f"  ✅ B23 : {len(conflicts)} conflit(s) détecté(s) :")
            for c in conflicts:
                print(f"     - [{c.project}] {c.subject} ({c.start_date} → {c.end_date})")
        else:
            print("  ⚠ B23 : aucun conflit (vérifier tâche Inès)")
    except Exception as e:
        print(f"  ❌ Leave Application : {e}")

    # ── FIX 3 : Purchase Order avec company ──────────────────────────────────
    print("\n=== FIX 3 : PURCHASE ORDER ===")

    tee026_name = None
    found = frappe.db.get_all("Project", filters={"project_name": ["like", "TEE-026%"]}, pluck="name")
    if found: tee026_name = found[0]

    # Nettoyer
    for po_name in frappe.db.get_all("Purchase Order", filters={"supplier": "FournEau SARL"},
                                      pluck="name"):
        try:
            pd = frappe.get_doc("Purchase Order", po_name)
            if pd.docstatus == 1: pd.cancel()
            frappe.delete_doc("Purchase Order", po_name, ignore_permissions=True, force=True)
            print(f"  🗑 PO supprimé : {po_name}")
        except Exception as e:
            print(f"  ⚠ PO {po_name} : {e}")
    frappe.db.commit()

    item_code = "POMPE-DOSE-001"
    uom       = frappe.db.get_value("Item", item_code, "stock_uom") or "Nos"

    try:
        po = frappe.get_doc({
            "doctype": "Purchase Order",
            "company": company,
            "supplier": "FournEau SARL",
            "project":  tee026_name,
            "schedule_date": str(add_days(today_d, 35)),
            "currency": "EUR",
            "buying_price_list": frappe.db.get_value("Price List",
                                                      {"buying": 1}, "name") or "Standard Buying",
            "items": [{
                "item_code": item_code, "item_name": "Pompe doseuse",
                "qty": 1, "rate": 8500,
                "uom": uom, "stock_uom": uom,
                "uom_conversion_factor": 1.0,
                "conversion_factor": 1.0,
                "schedule_date": str(add_days(today_d, 35)),
            }],
        })
        po.flags.ignore_mandatory = True
        po.flags.ignore_validate  = True
        po.insert(ignore_permissions=True)
        po.submit()
        frappe.db.commit()
        print(f"  ✅ Purchase Order soumis : {po.name} — 8 500 € / FournEau SARL")
    except Exception as e:
        print(f"  ❌ Purchase Order : {e}")

    # ── Récapitulatif ────────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    la_ok = frappe.db.count("Leave Application", {"employee": ines_emp, "docstatus": 1})
    po_ok = frappe.db.count("Purchase Order",    {"supplier": "FournEau SARL", "docstatus": 1})

    def chk(c): return "✅" if c else "❌"
    print(f"Congé Inès (soumis)   : {chk(la_ok)} {'Oui' if la_ok else 'Non'}")
    print(f"Purchase Order 8500€  : {chk(po_ok)} {'Oui' if po_ok else 'Non'}")

    if la_ok and po_ok:
        print("\n✅ JEU D'ESSAI SOCLE COMPLET — PRÊT POUR LA DÉMO")
    else:
        print("\n⚠ Certains items manquants.")
