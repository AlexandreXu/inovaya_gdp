"""Vérification finale du jeu d'essai socle."""
import frappe
from frappe.utils import today, getdate, add_days

def run():
    today_d = getdate(today())

    print("\n" + "=" * 65)
    print("VÉRIFICATION FINALE — JEU D'ESSAI SOCLE INOVAYA")
    print("=" * 65)

    def chk(c): return "✅" if c else "❌"

    # Users
    emails = ["marc.aubry@inovaya.com", "camille.roux@inovaya.com",
              "lea.martin@inovaya.com", "thomas.bel@inovaya.com", "ines.faure@inovaya.com"]
    u_count = sum(1 for e in emails if frappe.db.get_value("User", e, "enabled") == 1)
    print(f"\nUsers actifs          : {chk(u_count==5)} {u_count}/5")
    for e in emails:
        r = frappe.db.get_value("User", e, ["full_name", "enabled"], as_dict=True)
        print(f"  {'✅' if r and r.enabled else '❌'} {e}")

    # Employees
    emp_count = sum(1 for e in emails
                    if frappe.db.get_value("Employee", {"user_id": e, "status": "Active"}, "name"))
    print(f"\nEmployees actifs      : {chk(emp_count==5)} {emp_count}/5")

    # Inès → Marc
    ines_emp  = frappe.db.get_value("Employee", {"user_id": "ines.faure@inovaya.com"}, "name")
    marc_emp  = frappe.db.get_value("Employee", {"user_id": "marc.aubry@inovaya.com"},  "name")
    reports_ok = ines_emp and marc_emp and \
                 frappe.db.get_value("Employee", ines_emp, "reports_to") == marc_emp
    print(f"Inès reports_to Marc  : {chk(reports_ok)}")

    # Projets
    proj_map = {}
    for code in ["TEE-026", "IND-014", "DIG-003"]:
        found = frappe.db.get_all("Project",
                                   filters={"project_name": ["like", f"{code}%"]}, pluck="name")
        proj_map[code] = found[0] if found else None
    proj_count = sum(1 for v in proj_map.values() if v)
    print(f"\nProjets               : {chk(proj_count==3)} {proj_count}/3 {list(proj_map.values())}")

    # TEE-026 tâches
    tee026 = proj_map.get("TEE-026")
    if tee026:
        tasks_tee = frappe.db.get_all("Task", filters={"project": tee026},
                                       fields=["name", "subject", "_assign", "is_milestone"],
                                       order_by="creation")
        print(f"\nTâches TEE-026        : {chk(len(tasks_tee)>=5)} {len(tasks_tee)} tâches")
        for t in tasks_tee:
            import json as _json
            assignees = _json.loads(t._assign or "[]")
            ms = " [JALON]" if t.is_milestone else ""
            print(f"  {t.name} | {t.subject[:35]} | {', '.join(assignees)}{ms}")

        # Jalons
        jalons = frappe.db.get_all("Jalon Facturation InovaYa", filters={"project": tee026},
                                    fields=["name", "label", "amount", "status"])
        total_jalons = sum(j.amount or 0 for j in jalons)
        print(f"\nJalons TEE-026        : {chk(len(jalons)==3)} {len(jalons)}/3 — total={total_jalons}€")
        for j in jalons:
            print(f"  {j.name} | {j.label} | {j.amount}€")

        # Budget
        budget = frappe.db.get_all("Budget Detaille InovaYa",
                                    filters={"parent": tee026, "parenttype": "Project"},
                                    fields=["budget_category", "amount_planned", "amount_actual"])
        total_planned = sum(b.amount_planned or 0 for b in budget)
        print(f"\nBudget ventilé TEE    : {chk(len(budget)==3)} {len(budget)}/3 — prévu={total_planned}€")
        for b in budget:
            print(f"  {b.budget_category} : {b.amount_planned}€ prévu / {b.amount_actual}€ réalisé")

    # Annexe Task
    at = frappe.db.count("Annexe Task", {"subject": "Réunion qualité pôle"})
    print(f"\nAnnexe Task Léa       : {chk(at>0)} {'Oui' if at else 'Non'}")

    # Timesheet
    ts = frappe.db.count("Timesheet", {"title": "DEMO-TS-Lea", "docstatus": 1})
    print(f"Timesheet Léa (7h)    : {chk(ts>0)} {'Oui' if ts else 'Non'}")

    # Purchase Order
    po = frappe.db.count("Purchase Order", {"supplier": "FournEau SARL", "docstatus": 1})
    print(f"Purchase Order 8500€  : {chk(po>0)} {'Oui' if po else 'Non'}")

    # Leave Application
    la = frappe.db.count("Leave Application", {"employee": ines_emp or "", "docstatus": 1}) if ines_emp else 0
    print(f"Congé Inès (soumis)   : {chk(la>0)} {'Oui' if la else 'Non'}")

    # B23 dry_run
    print(f"\nB23 dry_run (détection conflit Inès) :")
    try:
        from inovaya_gdp.overrides.leave_application import dry_run
        if ines_emp:
            dry_run(ines_emp, str(add_days(today_d, 14)), str(add_days(today_d, 18)))
        else:
            print("  ⚠ Employee Inès introuvable")
    except Exception as e:
        print(f"  ❌ dry_run : {e}")

    # Mots de passe
    print(f"\nComptes démo (pass: Demo2026!) :")
    for e in ["camille.roux@inovaya.com", "lea.martin@inovaya.com", "marc.aubry@inovaya.com"]:
        ok_u = frappe.db.get_value("User", e, "enabled") == 1
        print(f"  {chk(ok_u)} {e}")

    # Verdict final
    all_checks = (u_count == 5 and emp_count == 5 and proj_count == 3 and
                  (len(tasks_tee) >= 5 if tee026 else False) and
                  (len(jalons) == 3 if tee026 else False) and
                  (len(budget) == 3 if tee026 else False) and
                  at > 0 and ts > 0 and po > 0)
    print(f"\n{'='*65}")
    print(f"{'✅ JEU D ESSAI COMPLET — PRÊT POUR LA DÉMO' if all_checks else '⚠ JEU D ESSAI PARTIEL — voir erreurs ci-dessus'}")
    print(f"{'='*65}")
