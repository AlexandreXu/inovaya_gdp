"""
Jeu d'essai socle InovaYa GdP
Usage : bench --site inovaya.localhost execute inovaya_gdp.setup.demo_data.run
"""
import json
import frappe
from frappe.utils import today, getdate, add_days
from frappe.utils.password import update_password


errors = []

def _ok(msg):   print(f"  ✅ {msg}")
def _warn(msg): print(f"  ⚠  {msg}")
def _fail(msg, exc=None):
    txt = f"  ❌ {msg}" + (f" — {exc}" if exc else "")
    print(txt); errors.append(msg)


# ─────────────────────────────────────────────────────────────────────────────
def _ensure_user(email, first, last, roles):
    """Crée ou récupère un User et configure ses rôles + mot de passe."""
    if frappe.db.exists("User", email):
        user = frappe.get_doc("User", email)
    else:
        user = frappe.get_doc({
            "doctype": "User", "email": email,
            "first_name": first, "last_name": last,
            "full_name": f"{first} {last}",
            "send_welcome_email": 0, "enabled": 1,
        })
        user.insert(ignore_permissions=True)
        _ok(f"User créé : {email}")

    existing_roles = {r.role for r in user.roles}
    changed = False
    for role in roles:
        if role not in existing_roles and frappe.db.exists("Role", role):
            user.append("roles", {"role": role}); changed = True
    if changed:
        user.save(ignore_permissions=True)

    try:
        update_password(email, "Demo2026!")
    except Exception as e:
        _warn(f"Mot de passe {email} : {e}")

    return True


def _ensure_employee(email, first, last, gender, company, dept, reports_to_emp):
    """Crée ou retourne l'Employee lié à l'email."""
    existing = frappe.db.get_value("Employee", {"user_id": email}, "name")
    if existing:
        _ok(f"Employee existant : {existing} ({first} {last})")
        return existing

    emp_doc = {
        "doctype": "Employee",
        "first_name": first, "last_name": last,
        "employee_name": f"{first} {last}",
        "user_id": email, "company": company,
        "status": "Active", "gender": gender,
        "date_of_joining": str(getdate(today())),
        "department": dept,
    }
    if reports_to_emp:
        emp_doc["reports_to"] = reports_to_emp

    emp = frappe.get_doc(emp_doc)
    emp.flags.ignore_mandatory = True
    emp.insert(ignore_permissions=True)
    _ok(f"Employee créé : {emp.name} ({first} {last})")
    return emp.name


# ─────────────────────────────────────────────────────────────────────────────
def run():
    global errors
    errors = []

    today_d = getdate(today())
    frappe.flags.in_test = True

    # ── 1. Société ──────────────────────────────────────────────────────────
    print("\n=== 1. SOCIÉTÉ ===")
    company = (frappe.db.get_single_value("Global Defaults", "default_company")
               or frappe.db.get_all("Company", limit=1, pluck="name")[0])
    _ok(f"Company : {company}")

    # ── 2. Département ──────────────────────────────────────────────────────
    print("\n=== 2. DÉPARTEMENT ===")
    dept_name = "Pôle GdP"
    dept_full = frappe.db.get_value("Department", {"department_name": dept_name}, "name")
    if not dept_full:
        try:
            dept = frappe.get_doc({"doctype": "Department",
                                   "department_name": dept_name, "company": company})
            dept.insert(ignore_permissions=True)
            dept_full = dept.name
            _ok(f"Département créé : {dept_full}")
        except Exception as e:
            _fail("Département", e); dept_full = dept_name
    else:
        _ok(f"Département existant : {dept_full}")
    frappe.db.commit()

    # ── 3. Users + Employees ────────────────────────────────────────────────
    print("\n=== 3. USERS + EMPLOYEES ===")

    # Marc en premier (Inès a reports_to=Marc)
    users_spec = [
        ("marc.aubry@inovaya.com",   "Marc",   "Aubry",  ["Manager InovaYa"],      "Male",   None),
        ("camille.roux@inovaya.com", "Camille","Roux",   ["Responsable GdP"],      "Female", None),
        ("lea.martin@inovaya.com",   "Léa",    "Martin", ["Collaborateur Projet"], "Female", None),
        ("thomas.bel@inovaya.com",   "Thomas", "Bel",    ["Collaborateur Projet"], "Male",   None),
        ("ines.faure@inovaya.com",   "Inès",   "Faure",  ["Collaborateur Projet"], "Female", "marc.aubry@inovaya.com"),
    ]

    emp_map = {}  # email → Employee.name
    for email, first, last, roles, gender, mgr_email in users_spec:
        try:
            _ensure_user(email, first, last, roles)
            mgr_emp = emp_map.get(mgr_email) if mgr_email else None
            emp_name = _ensure_employee(email, first, last, gender, company, dept_full, mgr_emp)
            emp_map[email] = emp_name
        except Exception as e:
            _fail(f"User/Employee {email}", e)

    # Fix reports_to Inès → Marc si nécessaire
    ines_emp = emp_map.get("ines.faure@inovaya.com")
    marc_emp  = emp_map.get("marc.aubry@inovaya.com")
    if ines_emp and marc_emp:
        cur = frappe.db.get_value("Employee", ines_emp, "reports_to")
        if cur != marc_emp:
            frappe.db.set_value("Employee", ines_emp, "reports_to", marc_emp)
            _ok(f"Inès reports_to → {marc_emp}")
    frappe.db.commit()

    # ── 4. Leave Type + Allocation ──────────────────────────────────────────
    print("\n=== 4. LEAVE TYPE + ALLOCATION ===")
    LT_NAME = "Congés payés"
    if not frappe.db.exists("Leave Type", LT_NAME):
        try:
            lt = frappe.get_doc({"doctype": "Leave Type", "leave_type_name": LT_NAME,
                                  "max_leaves_allowed": 25, "is_carry_forward": 0})
            lt.insert(ignore_permissions=True)
            _ok(f"Leave Type créé : {LT_NAME}")
        except Exception as e:
            _fail("Leave Type", e)
    else:
        _ok(f"Leave Type existant : {LT_NAME}")

    if ines_emp:
        existing_alloc = frappe.db.get_all(
            "Leave Allocation",
            filters={"employee": ines_emp, "leave_type": LT_NAME, "docstatus": ["!=", 2]},
            pluck="name",
        )
        if not existing_alloc:
            try:
                alloc = frappe.get_doc({
                    "doctype": "Leave Allocation", "employee": ines_emp,
                    "employee_name": "Inès Faure", "leave_type": LT_NAME,
                    "from_date": "2026-01-01", "to_date": "2026-12-31",
                    "new_leaves_allocated": 25,
                })
                alloc.flags.ignore_validate = alloc.flags.ignore_mandatory = True
                alloc.insert(ignore_permissions=True)
                alloc.submit()
                _ok(f"Leave Allocation soumise pour Inès ({alloc.name})")
            except Exception as e:
                _fail("Leave Allocation Inès", e)
        else:
            _ok(f"Leave Allocation existante Inès : {existing_alloc[0]}")
    frappe.db.commit()

    # ── 5. Customer AquaNeo ─────────────────────────────────────────────────
    print("\n=== 5. CUSTOMER AquaNeo ===")
    if not frappe.db.exists("Customer", "AquaNeo"):
        try:
            cg   = frappe.db.get_value("Customer Group", {"is_group": 0}, "name") or "All Customer Groups"
            terr = frappe.db.get_value("Territory", {"is_group": 0}, "name") or "All Territories"
            cust = frappe.get_doc({
                "doctype": "Customer", "customer_name": "AquaNeo",
                "customer_type": "Company", "customer_group": cg, "territory": terr,
            })
            cust.insert(ignore_permissions=True)
            _ok("Customer créé : AquaNeo")
        except Exception as e:
            _fail("Customer AquaNeo", e)
    else:
        _ok("Customer existant : AquaNeo")
    frappe.db.commit()

    # ── 6. Templates TEE-01 à TEE-05 ────────────────────────────────────────
    print("\n=== 6. TEMPLATES TEE-01 À TEE-05 ===")
    tee_updates = {
        "InovaYa-TEE-01": ("Diagnostic & relevé site",    0, 7),
        "InovaYa-TEE-02": ("Conception procédé P&ID",     0, 14),
        "InovaYa-TEE-03": ("Chiffrage & validation",      0, 7),
        "InovaYa-TEE-04": ("Réalisation / assemblage",    0, 21),
        "InovaYa-TEE-05": ("Mise en service (jalon)",     1, 14),
    }
    for tname, (subj, ms, dur) in tee_updates.items():
        if frappe.db.exists("Task", tname):
            frappe.db.set_value("Task", tname, "subject", subj, update_modified=False)
            frappe.db.set_value("Task", tname, "is_milestone", ms, update_modified=False)
            frappe.db.set_value("Task", tname, "duration", dur, update_modified=False)
            _ok(f"{tname} → {subj}")
        else:
            try:
                nt = frappe.get_doc({"doctype": "Task", "subject": subj,
                                      "is_template": 1, "is_milestone": ms, "duration": dur})
                nt.name = tname
                nt.insert(ignore_permissions=True)
                _ok(f"{tname} créé : {subj}")
            except Exception as e:
                _fail(f"Template {tname}", e)

    # Réduire le Project Template à TEE-01..05
    try:
        tmpl_doc = frappe.get_doc("Project Template", "InovaYa - CLIENT TEE")
        tee_keep = set(tee_updates.keys())
        # Identifier le champ de lien (task_id ou autre)
        task_field = None
        if tmpl_doc.tasks:
            sample = tmpl_doc.tasks[0].as_dict()
            for f in ("task_id", "task", "subject"):
                if f in sample:
                    task_field = f; break
        if task_field:
            orig = len(tmpl_doc.tasks)
            tmpl_doc.tasks = [t for t in tmpl_doc.tasks
                              if getattr(t, task_field, None) in tee_keep]
            tmpl_doc.save(ignore_permissions=True)
            _ok(f"Template CLIENT TEE : {orig} → {len(tmpl_doc.tasks)} tâches")
        else:
            _warn("Champ task_field introuvable dans Project Template Task")
    except Exception as e:
        _fail("Réduction Project Template TEE", e)
    frappe.db.commit()

    # ── 7. Projet TEE-026 ───────────────────────────────────────────────────
    print("\n=== 7. PROJET TEE-026 ===")
    for n in frappe.db.get_all("Project", filters={"project_name": ["like", "TEE-026%"]}, pluck="name"):
        for t in frappe.db.get_all("Task", filters={"project": n}, pluck="name"):
            frappe.delete_doc("Task", t, ignore_permissions=True, force=True)
        for j in frappe.db.get_all("Jalon Facturation InovaYa",
                                    filters={"project": n}, pluck="name"):
            try:
                dj = frappe.get_doc("Jalon Facturation InovaYa", j)
                if dj.docstatus == 1: dj.cancel()
            except Exception:
                pass
            frappe.delete_doc("Jalon Facturation InovaYa", j, ignore_permissions=True, force=True)
        frappe.delete_doc("Project", n, ignore_permissions=True, force=True)
    frappe.db.commit()

    tee026_name = None
    try:
        proj_tee = frappe.get_doc({
            "doctype": "Project",
            "project_name": "TEE-026 — Unité de traitement effluents",
            "project_type": "CLIENT TEE",
            "customer": "AquaNeo",
            "expected_start_date": str(today_d),
            "status": "Open",
        })
        proj_tee.insert(ignore_permissions=True)
        frappe.db.commit()
        tee026_name = proj_tee.name
        _ok(f"Projet créé : {tee026_name} | template={proj_tee.project_template}")
    except Exception as e:
        _fail("Projet TEE-026", e)

    task_count_tee = 0
    if tee026_name:
        tee_tasks = frappe.db.get_all(
            "Task",
            filters={"project": tee026_name, "is_template": 0},
            fields=["name", "subject", "template_task", "is_milestone"],
            order_by="creation",
        )
        print(f"  {len(tee_tasks)} tâches auto-générées :")
        for t in tee_tasks:
            print(f"    {t.name} | {t.subject} | ms={t.is_milestone}")

        tee_by_tmpl = {t.template_task: t.name for t in tee_tasks}
        tee_by_subj = {t.subject: t.name for t in tee_tasks}

        # Assignments : (tmpl_key, email, start_off, end_off, hpd, importance)
        assignments = [
            ("InovaYa-TEE-01", "camille.roux@inovaya.com",  0,  7, 1.0, "Basse"),
            ("InovaYa-TEE-02", "thomas.bel@inovaya.com",    7, 21, 4.0, "Haute"),
            ("InovaYa-TEE-03", "camille.roux@inovaya.com", 14, 21, 2.0, "Basse"),
            ("InovaYa-TEE-04", "lea.martin@inovaya.com",   21, 42, 6.0, "Basse"),
            ("InovaYa-TEE-05", "lea.martin@inovaya.com",   42, 56, 6.0, "Basse"),
        ]
        for tmpl_key, email, s_off, e_off, hpd, imp in assignments:
            t_name = tee_by_tmpl.get(tmpl_key)
            if not t_name:
                subj = tee_updates.get(tmpl_key, ("",))[0]
                t_name = tee_by_subj.get(subj)
            if not t_name:
                _warn(f"Tâche pour {tmpl_key} introuvable")
            else:
                ms_val = tee_updates.get(tmpl_key, ("", 0))[1]
                frappe.db.set_value("Task", t_name, {
                    "exp_start_date": str(add_days(today_d, s_off)),
                    "exp_end_date":   str(add_days(today_d, e_off)),
                    "inovaya_hours_per_day": hpd,
                    "inovaya_importance": imp,
                    "is_milestone": ms_val,
                }, update_modified=False)
                frappe.db.set_value("Task", t_name, "_assign",
                                    json.dumps([email]), update_modified=False)
                _ok(f"Assigné : {t_name} ({tmpl_key}) → {email}")
                task_count_tee += 1

        # Tâche Inès (conflit congé B23)
        try:
            t_ines = frappe.get_doc({
                "doctype": "Task", "subject": "Essais terrain Inès",
                "project": tee026_name, "status": "Open",
                "exp_start_date": str(add_days(today_d, 14)),
                "exp_end_date":   str(add_days(today_d, 21)),
                "inovaya_hours_per_day": 7.0, "inovaya_importance": "Haute",
            })
            t_ines.insert(ignore_permissions=True)
            frappe.db.set_value("Task", t_ines.name, "_assign",
                                json.dumps(["ines.faure@inovaya.com"]), update_modified=False)
            _ok(f"Tâche Inès : {t_ines.name}")
        except Exception as e:
            _fail("Tâche Inès", e)
        frappe.db.commit()

        # Budget ventilé
        for old in frappe.db.get_all("Budget Detaille InovaYa",
                                      filters={"parent": tee026_name, "parenttype": "Project"},
                                      pluck="name"):
            frappe.delete_doc("Budget Detaille InovaYa", old, ignore_permissions=True, force=True)
        for cat, planned, actual in [
            ("Matériel",             70000, 0),
            ("Prestations externes", 30000, 0),
            ("ETPs",                 20000, 6200),
        ]:
            try:
                bd = frappe.get_doc({
                    "doctype": "Budget Detaille InovaYa",
                    "parent": tee026_name, "parenttype": "Project",
                    "parentfield": "inovaya_budget_details",
                    "budget_category": cat,
                    "amount_planned": planned, "amount_actual": actual,
                })
                bd.insert(ignore_permissions=True)
                _ok(f"Budget {cat} : {planned}€")
            except Exception as e:
                _fail(f"Budget {cat}", e)
        frappe.db.commit()

        # Jalons de facturation
        for label, amount, offset in [
            ("Acompte 30% — démarrage",  36000,  7),
            ("Conception validée 40%",    48000, 28),
            ("Réception finale 30%",      36000, 56),
        ]:
            try:
                jal = frappe.get_doc({
                    "doctype": "Jalon Facturation InovaYa",
                    "project": tee026_name, "label": label,
                    "amount": amount, "status": "A venir",
                    "expected_date": str(add_days(today_d, offset)),
                })
                jal.insert(ignore_permissions=True)
                _ok(f"Jalon : {label} — {amount}€")
            except Exception as e:
                _fail(f"Jalon {label}", e)
        frappe.db.commit()

    # ── 8. Projet IND-014 ───────────────────────────────────────────────────
    print("\n=== 8. PROJET IND-014 (conflit B05) ===")
    for n in frappe.db.get_all("Project", filters={"project_name": ["like", "IND-014%"]}, pluck="name"):
        for t in frappe.db.get_all("Task", filters={"project": n}, pluck="name"):
            frappe.delete_doc("Task", t, ignore_permissions=True, force=True)
        frappe.delete_doc("Project", n, ignore_permissions=True, force=True)
    frappe.db.commit()

    try:
        proj_ind = frappe.get_doc({
            "doctype": "Project",
            "project_name": "IND-014 — Optimisation ligne fabrication",
            "project_type": "IND", "expected_start_date": str(today_d), "status": "Open",
        })
        proj_ind.insert(ignore_permissions=True)
        frappe.db.commit()
        _ok(f"Projet créé : {proj_ind.name}")

        t_ind = frappe.get_doc({
            "doctype": "Task", "subject": "Fabrication module IND",
            "project": proj_ind.name, "status": "Open",
            "exp_start_date": str(add_days(today_d, 21)),
            "exp_end_date":   str(add_days(today_d, 28)),
            "inovaya_hours_per_day": 8.0, "inovaya_importance": "Haute",
        })
        t_ind.insert(ignore_permissions=True)
        frappe.db.set_value("Task", t_ind.name, "_assign",
                            json.dumps(["lea.martin@inovaya.com"]), update_modified=False)
        frappe.db.commit()
        _ok(f"Tâche conflit : {t_ind.name} (Léa 8h/j — conflit TEE 6h/j)")
    except Exception as e:
        _fail("Projet IND-014", e)

    # ── 9. Projet DIG-003 ───────────────────────────────────────────────────
    print("\n=== 9. PROJET DIG-003 (Kanban) ===")
    for n in frappe.db.get_all("Project", filters={"project_name": ["like", "DIG-003%"]}, pluck="name"):
        for t in frappe.db.get_all("Task", filters={"project": n}, pluck="name"):
            frappe.delete_doc("Task", t, ignore_permissions=True, force=True)
        frappe.delete_doc("Project", n, ignore_permissions=True, force=True)
    frappe.db.commit()

    try:
        proj_dig = frappe.get_doc({
            "doctype": "Project",
            "project_name": "DIG-003 — Portail client digital",
            "project_type": "Digital", "expected_start_date": str(today_d), "status": "Open",
        })
        proj_dig.insert(ignore_permissions=True)
        frappe.db.commit()
        _ok(f"Projet créé : {proj_dig.name}")

        for subj, status, email in [
            ("Cadrage UX",             "Open",           "thomas.bel@inovaya.com"),
            ("Développement frontend", "Working",         "thomas.bel@inovaya.com"),
            ("Recette interne",        "Pending Review",  "thomas.bel@inovaya.com"),
            ("Mise en production",     "Open",            "marc.aubry@inovaya.com"),
        ]:
            tk = frappe.get_doc({
                "doctype": "Task", "subject": subj, "project": proj_dig.name,
                "status": status,
                "exp_start_date": str(today_d),
                "exp_end_date":   str(add_days(today_d, 30)),
                "inovaya_hours_per_day": 4.0, "inovaya_importance": "Basse",
            })
            tk.insert(ignore_permissions=True)
            frappe.db.set_value("Task", tk.name, "_assign",
                                json.dumps([email]), update_modified=False)
            _ok(f"Kanban : {subj} [{status}]")
        frappe.db.commit()
    except Exception as e:
        _fail("Projet DIG-003", e)

    # ── 10. Annexe Task ─────────────────────────────────────────────────────
    print("\n=== 10. ANNEXE TASK (Léa) ===")
    for n in frappe.db.get_all("Annexe Task", filters={"subject": "Réunion qualité pôle"},
                                pluck="name"):
        frappe.delete_doc("Annexe Task", n, ignore_permissions=True, force=True)
    frappe.db.commit()

    annexe_ok = False
    try:
        at = frappe.get_doc({
            "doctype": "Annexe Task", "subject": "Réunion qualité pôle",
            "assigned_to": "lea.martin@inovaya.com", "status": "Open",
            "exp_start_date": str(today_d), "exp_end_date": str(add_days(today_d, 7)),
            "inovaya_hours_per_day": 0.5, "inovaya_importance": "Basse",
        })
        at.flags.ignore_mandatory = True
        at.insert(ignore_permissions=True)
        frappe.db.commit()
        _ok(f"Annexe Task : {at.name}")
        annexe_ok = True
    except Exception as e:
        _fail("Annexe Task", e)

    # ── 11. Timesheet Léa ───────────────────────────────────────────────────
    print("\n=== 11. TIMESHEET LÉA (7h) ===")
    lea_emp = emp_map.get("lea.martin@inovaya.com")
    ts_ok   = False

    realisation_task = None
    if tee026_name:
        realisation_task = frappe.db.get_value(
            "Task", {"project": tee026_name, "subject": "Réalisation / assemblage"}, "name"
        )
        if not realisation_task:
            # Fallback : template TEE-04
            realisation_task = frappe.db.get_value(
                "Task", {"project": tee026_name, "template_task": "InovaYa-TEE-04"}, "name"
            )

    if lea_emp and realisation_task:
        for ts in frappe.db.get_all("Timesheet", filters={"title": "DEMO-TS-Lea"}, pluck="name"):
            doc_ts = frappe.get_doc("Timesheet", ts)
            if doc_ts.docstatus == 1:
                try: doc_ts.cancel()
                except Exception: pass
            frappe.delete_doc("Timesheet", ts, ignore_permissions=True, force=True)
        frappe.db.commit()

        act_type = (frappe.db.get_all("Activity Type", limit=1, pluck="name") or ["Execution"])[0]
        try:
            ts = frappe.get_doc({
                "doctype": "Timesheet", "title": "DEMO-TS-Lea", "employee": lea_emp,
                "time_logs": [{
                    "activity_type": act_type,
                    "from_time": f"{today_d} 09:00:00",
                    "to_time":   f"{today_d} 16:00:00",
                    "hours": 7.0, "task": realisation_task,
                    "project": tee026_name, "is_billable": 0,
                }],
            })
            ts.flags.ignore_mandatory = ts.flags.ignore_validate = True
            ts.insert(ignore_permissions=True)
            ts.submit()
            frappe.db.commit()
            _ok(f"Timesheet soumise : {ts.name} (7h → {realisation_task})")
            ts_ok = True
        except Exception as e:
            _fail("Timesheet Léa", e)
    else:
        _warn(f"Timesheet ignorée — lea_emp={lea_emp}, task={realisation_task}")

    # ── 12. Purchase Order ──────────────────────────────────────────────────
    print("\n=== 12. PURCHASE ORDER ===")
    po_ok = False

    if not frappe.db.exists("Supplier", "FournEau SARL"):
        try:
            sg  = frappe.db.get_value("Supplier Group", {"is_group": 0}, "name") or "All Supplier Groups"
            sup = frappe.get_doc({"doctype": "Supplier", "supplier_name": "FournEau SARL",
                                   "supplier_group": sg, "supplier_type": "Company"})
            sup.insert(ignore_permissions=True)
            frappe.db.commit()
            _ok("Fournisseur créé : FournEau SARL")
        except Exception as e:
            _fail("Fournisseur FournEau SARL", e)
    else:
        _ok("Fournisseur existant : FournEau SARL")

    item_code = "POMPE-DOSE-001"
    if not frappe.db.exists("Item", item_code):
        try:
            ig   = frappe.db.get_value("Item Group", {"is_group": 0}, "name") or "All Item Groups"
            item = frappe.get_doc({
                "doctype": "Item", "item_code": item_code, "item_name": "Pompe doseuse",
                "item_group": ig, "stock_uom": "Nos", "is_stock_item": 0,
            })
            item.insert(ignore_permissions=True)
            frappe.db.commit()
            _ok("Item créé : Pompe doseuse")
        except Exception as e:
            _fail("Item Pompe doseuse", e)
    else:
        _ok("Item existant : Pompe doseuse")

    for po in frappe.db.get_all("Purchase Order",
                                 filters={"supplier": "FournEau SARL",
                                          "project": tee026_name or ""},
                                 pluck="name"):
        try:
            dpo = frappe.get_doc("Purchase Order", po)
            if dpo.docstatus == 1: dpo.cancel()
            frappe.delete_doc("Purchase Order", po, ignore_permissions=True, force=True)
        except Exception:
            pass
    frappe.db.commit()

    try:
        uom = frappe.db.get_value("Item", item_code, "stock_uom") or "Nos"
        po = frappe.get_doc({
            "doctype": "Purchase Order",
            "supplier": "FournEau SARL", "project": tee026_name,
            "schedule_date": str(add_days(today_d, 35)),
            "currency": "EUR",
            "items": [{
                "item_code": item_code, "item_name": "Pompe doseuse",
                "qty": 1, "rate": 8500, "uom": uom,
                "schedule_date": str(add_days(today_d, 35)),
            }],
        })
        po.flags.ignore_mandatory = po.flags.ignore_validate = True
        po.insert(ignore_permissions=True)
        po.submit()
        frappe.db.commit()
        _ok(f"Purchase Order soumis : {po.name} — 8 500 € / FournEau SARL")
        po_ok = True
    except Exception as e:
        _fail("Purchase Order", e)

    # ── 13. Leave Application Inès (B23) ────────────────────────────────────
    print("\n=== 13. LEAVE APPLICATION INÈS (B23) ===")
    leave_ok = False; b23_ok = False

    if ines_emp:
        for la in frappe.db.get_all("Leave Application",
                                     filters={"employee": ines_emp, "docstatus": ["!=", 2]},
                                     pluck="name"):
            try:
                dla = frappe.get_doc("Leave Application", la)
                if dla.docstatus == 1: dla.cancel()
                frappe.delete_doc("Leave Application", la, ignore_permissions=True, force=True)
            except Exception:
                pass
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
            # Laisser B23 s'exécuter (retirer in_test)
            frappe.flags.in_test = False
            la.submit()
            frappe.flags.in_test = True
            frappe.db.commit()
            _ok(f"Leave Application soumise : {la.name}")
            leave_ok = True; b23_ok = True
        except Exception as e:
            _fail("Leave Application Inès", e)
    else:
        _warn("Leave Application ignorée — Employee Inès introuvable")

    frappe.flags.in_test = False  # Reset final

    # ── Récapitulatif ────────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    print("SOCLE DÉMO INOVAYA — RÉCAPITULATIF FINAL")
    print("=" * 62)

    total_u = sum(1 for us in ["marc.aubry@inovaya.com", "camille.roux@inovaya.com",
                                "lea.martin@inovaya.com", "thomas.bel@inovaya.com",
                                "ines.faure@inovaya.com"]
                  if frappe.db.exists("User", us))
    total_e = len([v for v in emp_map.values() if v])

    proj_found = []
    for pn in ["TEE-026", "IND-014", "DIG-003"]:
        found = frappe.db.get_all("Project", filters={"project_name": ["like", f"{pn}%"]},
                                   pluck="name")
        if found: proj_found.append(found[0])

    tasks_tee  = frappe.db.count("Task", {"project": tee026_name}) if tee026_name else 0
    jalons_tee = frappe.db.count("Jalon Facturation InovaYa", {"project": tee026_name}) if tee026_name else 0
    budget_tee = frappe.db.count("Budget Detaille InovaYa",
                                  {"parent": tee026_name, "parenttype": "Project"}) if tee026_name else 0
    ts_count   = frappe.db.count("Timesheet", {"title": "DEMO-TS-Lea", "docstatus": 1})
    po_count   = frappe.db.count("Purchase Order", {"supplier": "FournEau SARL", "docstatus": 1})
    la_count   = frappe.db.count("Leave Application", {"employee": ines_emp or "", "docstatus": 1}) if ines_emp else 0
    at_count   = frappe.db.count("Annexe Task", {"subject": "Réunion qualité pôle"})

    def chk(c): return "✅" if c else "❌"

    print(f"Users créés           : {total_u}/5")
    print(f"Employees créés       : {total_e}/5")
    print(f"Projets créés         : {len(proj_found)}/3  {proj_found}")
    print(f"Tâches TEE-026        : {tasks_tee} (5 normales + 1 tâche Inès)")
    print(f"Jalons TEE-026        : {chk(jalons_tee==3)} {jalons_tee}/3 — total prévu 120 000 €")
    print(f"Budget ventilé TEE    : {chk(budget_tee==3)} {budget_tee}/3 catégories")
    print(f"Annexe Task Léa       : {chk(at_count>0)} {'Oui' if at_count else 'Non'}")
    print(f"Congé Inès (soumis)   : {chk(la_count>0)} {'Oui' if la_count else 'Non'}")
    print(f"B23 alerte B23        : {chk(b23_ok)} {'déclenchée' if b23_ok else 'Non'}")
    print(f"Timesheet Léa 7h      : {chk(ts_count>0)} {'Oui' if ts_count else 'Non'}")
    print(f"Purchase Order 8500€  : {chk(po_count>0)} {'Oui' if po_count else 'Non'}")
    print(f"Mot de passe démo     : Demo2026!")

    if errors:
        print(f"\n⚠  {len(errors)} erreur(s) :")
        for msg in errors: print(f"   - {msg}")
    else:
        print("\n✅ Jeu d'essai créé sans erreur !")
