"""
Vérification complète de l'état WSL — source de vérité.
bench --site inovaya.localhost execute inovaya_gdp.setup.check_wsl_state.run
"""
import glob
import frappe


def run():
    print("\n" + "="*65)
    print("  VÉRIFICATION WSL — SOURCE DE VÉRITÉ")
    print("="*65)

    # ── 1. Overrides Python ──────────────────────────────────────────
    print("\n[1] OVERRIDES")
    overrides = {
        "task":                "inovaya_gdp.overrides.task",
        "project":             "inovaya_gdp.overrides.project",
        "jalon_facturation":   "inovaya_gdp.overrides.jalon_facturation",
        "leave_application":   "inovaya_gdp.overrides.leave_application",
        "weekly_hours_alert":  "inovaya_gdp.overrides.weekly_hours_alert",
    }
    all_ok = True
    for name, module_path in overrides.items():
        try:
            mod = frappe.get_module(module_path)
            print(f"  ✅ {name:<25} {module_path}")
        except Exception as e:
            print(f"  ❌ {name:<25} ERREUR : {e}")
            all_ok = False

    # ── 2. Rapports ──────────────────────────────────────────────────
    print("\n[2] RAPPORTS (Script Reports)")
    import os
    base = "/home/alexandre/frappe-bench-inovaya/apps/inovaya_gdp/inovaya_gdp/inovaya/report"
    reports = sorted(glob.glob(f"{base}/*/")) if os.path.isdir(base) else []
    print(f"  Rapports présents : {len(reports)}")
    for r in reports:
        name = r.split("/")[-2]
        py_ok = os.path.exists(f"{r}{name}.py")
        js_ok = os.path.exists(f"{r}{name}.js")
        db_ok = frappe.db.exists("Report", frappe.unscrub(name))
        flag = "✅" if py_ok and js_ok else "⚠️"
        db_flag = "✅ DB" if db_ok else "❌ PAS EN DB"
        print(f"  {flag} {name}  py={py_ok} js={js_ok}  {db_flag}")

    # ── 3. Hooks enregistrés ─────────────────────────────────────────
    print("\n[3] DOC_EVENTS ENREGISTRÉS")
    hooks = frappe.get_hooks("doc_events", app_name="inovaya_gdp")
    for doctype, events in hooks.items():
        for event, handler in events.items():
            h = handler[0] if isinstance(handler, list) else handler
            print(f"  {doctype:<30} {event:<15} → {h}")

    # ── 4. Fixtures en DB ─────────────────────────────────────────────
    print("\n[4] FIXTURES EN BASE")
    checks = {
        "Rôles InovaYa":          frappe.db.count("Role", {"name": ["like", "%Projet%"]}),
        "Custom Fields inovaya_":  frappe.db.count("Custom Field", {"fieldname": ["like", "inovaya_%"]}),
        "Project Types":           frappe.db.count("Project Type", {"name": ["in", ["IND", "CLIENT TEE", "R&D", "Digital", "Interne"]]}),
        "Task templates (InovaYa-%)": frappe.db.count("Task", {"name": ["like", "InovaYa-%"], "is_template": 1}),
        "Project Templates (InovaYa -%):": frappe.db.count("Project Template", {"name": ["like", "InovaYa -%"]}),
        "DocTypes custom":         frappe.db.count("DocType", {"name": ["in", ["Annexe Task", "Budget Detaille InovaYa", "Jalon Facturation InovaYa"]]}),
        "Custom DocPerms":         frappe.db.count("Custom DocPerm", {"role": ["in", ["Responsable GdP", "Collaborateur Projet"]]}),
    }
    for k, v in checks.items():
        flag = "✅" if v > 0 else "❌"
        print(f"  {flag} {k:<45} = {v}")

    # ── 5. Données démo ───────────────────────────────────────────────
    print("\n[5] DONNÉES DÉMO")
    print(f"  Projets : {frappe.db.count('Project')}")
    print(f"  Tâches  : {frappe.db.count('Task', {'is_template': 0})}")
    print(f"  Users actifs : {frappe.db.count('User', {'enabled': 1, 'user_type': 'System User'})}")
    po = frappe.db.count("Purchase Order", {"docstatus": 1})
    ts = frappe.db.count("Timesheet", {"docstatus": 1})
    print(f"  PO soumis : {po}  |  Timesheets soumis : {ts}")

    print("\n" + "="*65)
    print("  WSL = SOURCE DE VÉRITÉ" if all_ok else "  ⚠️  VÉRIFIER LES OVERRIDES EN ERREUR")
    print("="*65 + "\n")
