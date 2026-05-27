"""
Fix ciblé jeu d'essai :
1. Holiday List InovaYa 2026 → Leave Application Inès (B23)
2. Purchase Order Pompe doseuse (UOM conversion)

Usage : bench --site inovaya.localhost execute inovaya_gdp.setup.demo_fix.run
"""
import frappe
from frappe.utils import today, getdate, add_days

def run():
    today_d = getdate(today())
    company = (frappe.db.get_single_value("Global Defaults", "default_company")
               or frappe.db.get_all("Company", limit=1, pluck="name")[0])

    # ── FIX 1 : Holiday List ─────────────────────────────────────────────────
    print("\n=== FIX 1 : HOLIDAY LIST ===")
    HL_NAME = "InovaYa 2026"
    if not frappe.db.exists("Holiday List", HL_NAME):
        hl = frappe.get_doc({
            "doctype": "Holiday List",
            "holiday_list_name": HL_NAME,
            "from_date": "2026-01-01",
            "to_date":   "2026-12-31",
            "holidays": [],   # pas de jours fériés codés — calcul sur jours ouvrés seulement
        })
        hl.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"  ✅ Holiday List créée : {hl.name}")
    else:
        print(f"  ✅ Holiday List existante : {HL_NAME}")

    # Définir comme liste par défaut pour la company
    cur_hl = frappe.db.get_value("Company", company, "default_holiday_list")
    if cur_hl != HL_NAME:
        frappe.db.set_value("Company", company, "default_holiday_list", HL_NAME)
        frappe.db.commit()
        print(f"  ✅ Company {company} → default_holiday_list = {HL_NAME}")

    # ── FIX 2 : Leave Application Inès ──────────────────────────────────────
    print("\n=== FIX 2 : LEAVE APPLICATION INÈS ===")
    ines_emp = frappe.db.get_value("Employee", {"user_id": "ines.faure@inovaya.com"}, "name")
    if not ines_emp:
        print("  ❌ Employee Inès introuvable")
    else:
        # Nettoyer les LAs existantes
        for la_name in frappe.db.get_all("Leave Application",
                                          filters={"employee": ines_emp, "docstatus": ["!=", 2]},
                                          pluck="name"):
            try:
                la_doc = frappe.get_doc("Leave Application", la_name)
                if la_doc.docstatus == 1:
                    la_doc.cancel()
                frappe.delete_doc("Leave Application", la_name, ignore_permissions=True, force=True)
                print(f"  🗑 LA supprimée : {la_name}")
            except Exception as e:
                print(f"  ⚠ Impossible de supprimer {la_name} : {e}")
        frappe.db.commit()

        try:
            la = frappe.get_doc({
                "doctype": "Leave Application",
                "employee": ines_emp, "employee_name": "Inès Faure",
                "leave_type": "Congés payés",
                "from_date": str(add_days(today_d, 14)),
                "to_date":   str(add_days(today_d, 18)),
                "status": "Approved", "posting_date": str(today_d), "half_day": 0,
            })
            la.flags.ignore_validate = la.flags.ignore_mandatory = True
            la.insert(ignore_permissions=True)
            frappe.flags.in_test = False   # Permettre à B23 de se déclencher
            la.submit()
            frappe.flags.in_test = False
            frappe.db.commit()
            print(f"  ✅ Leave Application soumise : {la.name}")
            print(f"     Période : J+14 → J+18 ({add_days(today_d,14)} → {add_days(today_d,18)})")

            # Vérifier si B23 a détecté un conflit (Inès a TASK-2026-00112)
            from inovaya_gdp.overrides.leave_application import _find_conflicting_tasks, _get_user_email
            user_email = _get_user_email(ines_emp)
            conflicts  = _find_conflicting_tasks(user_email, getdate(add_days(today_d, 14)),
                                                  getdate(add_days(today_d, 18)))
            if conflicts:
                print(f"  ✅ B23 : {len(conflicts)} conflit(s) détecté(s) pour Inès :")
                for c in conflicts:
                    print(f"     - [{c.project}] {c.subject} ({c.start_date} → {c.end_date})")
            else:
                print("  ⚠ B23 : aucun conflit détecté (vérifier les tâches Inès)")
        except Exception as e:
            print(f"  ❌ Leave Application Inès : {e}")

    # ── FIX 3 : Purchase Order ───────────────────────────────────────────────
    print("\n=== FIX 3 : PURCHASE ORDER ===")

    tee026_name = None
    found = frappe.db.get_all("Project", filters={"project_name": ["like", "TEE-026%"]}, pluck="name")
    if found: tee026_name = found[0]

    # Nettoyer PO FournEau SARL existants
    for po_name in frappe.db.get_all("Purchase Order",
                                      filters={"supplier": "FournEau SARL"}, pluck="name"):
        try:
            po_doc = frappe.get_doc("Purchase Order", po_name)
            if po_doc.docstatus == 1: po_doc.cancel()
            frappe.delete_doc("Purchase Order", po_name, ignore_permissions=True, force=True)
            print(f"  🗑 PO supprimé : {po_name}")
        except Exception as e:
            print(f"  ⚠ Impossible de supprimer {po_name} : {e}")
    frappe.db.commit()

    item_code = "POMPE-DOSE-001"
    uom       = frappe.db.get_value("Item", item_code, "stock_uom") or "Nos"

    try:
        po = frappe.get_doc({
            "doctype": "Purchase Order",
            "supplier": "FournEau SARL",
            "project":  tee026_name,
            "schedule_date": str(add_days(today_d, 35)),
            "currency": "EUR",
            "items": [{
                "item_code": item_code, "item_name": "Pompe doseuse",
                "qty": 1, "rate": 8500,
                "uom": uom, "stock_uom": uom,
                "uom_conversion_factor": 1.0,
                "schedule_date": str(add_days(today_d, 35)),
                "conversion_factor": 1.0,
            }],
        })
        po.flags.ignore_mandatory = True
        po.flags.ignore_validate  = True
        po.set_missing_values()     # laisser ERPNext calculer les totaux
        po.insert(ignore_permissions=True)
        po.submit()
        frappe.db.commit()
        print(f"  ✅ Purchase Order soumis : {po.name} — 8 500 € / FournEau SARL")
    except Exception as e:
        print(f"  ❌ Purchase Order : {e}")

    # ── Récapitulatif final ──────────────────────────────────────────────────
    print("\n" + "=" * 62)
    print("SOCLE DÉMO INOVAYA — ÉTAT APRÈS FIXES")
    print("=" * 62)
    ines_emp2  = ines_emp or ""
    la_count   = frappe.db.count("Leave Application", {"employee": ines_emp2, "docstatus": 1})
    po_count   = frappe.db.count("Purchase Order",    {"supplier": "FournEau SARL", "docstatus": 1})

    def chk(c): return "✅" if c else "❌"
    print(f"Congé Inès (soumis)   : {chk(la_count>0)} {'Oui' if la_count else 'Non'}")
    print(f"Purchase Order 8500€  : {chk(po_count>0)} {'Oui' if po_count else 'Non'}")
    print(f"Holiday List InovaYa  : {chk(frappe.db.exists('Holiday List', HL_NAME))} {HL_NAME}")

    if la_count and po_count:
        print("\n✅ Jeu d'essai socle COMPLET — tous les items présents.")
    else:
        print("\n⚠ Certains items manquants — vérifier les erreurs ci-dessus.")
