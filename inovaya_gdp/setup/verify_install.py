"""
Vérification post-install InovaYa GdP.
Équivalent d'un check après bench install-app inovaya_gdp sur site propre.
bench --site inovaya.localhost execute inovaya_gdp.setup.verify_install.run
"""
import frappe


def _check(label, count, expected_min, details=None):
    ok = count >= expected_min
    icon = "✅" if ok else "❌"
    detail_str = f" ({', '.join(details)})" if details else ""
    print(f"  {icon} {label} : {count}{detail_str}")
    return ok


def run():
    print("\n" + "=" * 60)
    print("  VÉRIFICATION INSTALLATION InovaYa GdP")
    print("=" * 60)
    errors = []

    # ── 1. Rôles ──────────────────────────────────────────────────────────────
    print("\n[1] Rôles InovaYa")
    expected_roles = [
        "Collaborateur Projet", "Chef de Projet", "Manager InovaYa",
        "Responsable GdP", "Responsable Operations", "Direction Generale",
        "Finance InovaYa", "Logistique Achats", "RH InovaYa",
    ]
    existing_roles = [
        r.name for r in frappe.db.get_all("Role", filters={"name": ["in", expected_roles]})
    ]
    for role in expected_roles:
        found = role in existing_roles
        print(f"  {'✅' if found else '❌'} {role}")
        if not found:
            errors.append(f"Rôle manquant : {role}")

    # ── 2. Custom Fields ───────────────────────────────────────────────────────
    print("\n[2] Custom Fields (inovaya_*)")
    cf_count = frappe.db.count("Custom Field", filters={"fieldname": ["like", "inovaya_%"]})
    cf_names = frappe.db.get_all("Custom Field",
        filters={"fieldname": ["like", "inovaya_%"]},
        fields=["fieldname", "dt"])
    if not _check("Custom Fields inovaya_*", cf_count, 1):
        errors.append("Aucun custom field inovaya_*")
    for cf in cf_names:
        print(f"     • {cf.dt}.{cf.fieldname}")

    # ── 3. Project Types ───────────────────────────────────────────────────────
    print("\n[3] Project Types")
    expected_pt = ["IND", "CLIENT TEE", "R&D", "Digital", "Interne"]
    existing_pt = [r.name for r in frappe.db.get_all("Project Type",
        filters={"name": ["in", expected_pt]})]
    for pt in expected_pt:
        found = pt in existing_pt
        print(f"  {'✅' if found else '❌'} {pt}")
        if not found:
            errors.append(f"Project Type manquant : {pt}")

    # ── 4. Task Templates ──────────────────────────────────────────────────────
    print("\n[4] Task Templates (InovaYa-*)")
    tt_count = frappe.db.count("Task", filters={"name": ["like", "InovaYa-%"], "is_template": 1})
    if not _check("Task templates", tt_count, 1):
        errors.append("Aucun task template InovaYa-*")

    # ── 5. Project Templates ───────────────────────────────────────────────────
    print("\n[5] Project Templates (InovaYa -)")
    tmpl_count = frappe.db.count("Project Template", filters={"name": ["like", "InovaYa -%"]})
    tmpls = frappe.db.get_all("Project Template", filters={"name": ["like", "InovaYa -%"]}, fields=["name"])
    if not _check("Project Templates", tmpl_count, 1):
        errors.append("Aucun project template InovaYa -")
    for t in tmpls:
        print(f"     • {t.name}")

    # ── 6. DocTypes custom ─────────────────────────────────────────────────────
    print("\n[6] DocTypes custom InovaYa (5 attendus)")
    expected_dt = [
        "Annexe Task",
        "Budget Detaille InovaYa",
        "Jalon Facturation InovaYa",
        "Impact Projet InovaYa",
        "Demande Transport InovaYa",
    ]
    for dt in expected_dt:
        exists = frappe.db.exists("DocType", dt)
        print(f"  {'✅' if exists else '❌'} {dt}")
        if not exists:
            errors.append(f"DocType manquant : {dt}")

    # ── 7. Pages Frappe ────────────────────────────────────────────────────────
    print("\n[7] Pages Frappe InovaYa (2 attendues)")
    expected_pages = [
        "plan-charge-equipe-inovaya",
        "mon-planning-inovaya",
    ]
    for pg in expected_pages:
        exists = frappe.db.exists("Page", pg)
        page_title = frappe.db.get_value("Page", pg, "title") if exists else None
        print(f"  {'✅' if exists else '❌'} {pg} ({page_title or 'N/A'})")
        if not exists:
            errors.append(f"Page manquante : {pg}")

    # ── 8. Workspaces ─────────────────────────────────────────────────────────
    print("\n[8] Workspaces InovaYa")
    expected_ws = ["InovaYa Pôle GdP", "InovaYa Direction"]
    all_ws = frappe.db.get_all("Workspace", filters={"name": ["like", "InovaYa%"]},
        fields=["name", "public"])
    ws_names = {w.name for w in all_ws}
    for ws in expected_ws:
        found = ws in ws_names
        print(f"  {'✅' if found else '❌'} {ws}")
        if not found:
            errors.append(f"Workspace manquant : {ws}")
    for w in sorted(all_ws, key=lambda x: x.name):
        if w.name not in expected_ws:
            print(f"  ✅ {w.name} (autre workspace)")

    # ── 9. Dashboard Charts ────────────────────────────────────────────────────
    print("\n[9] Dashboard Charts InovaYa (4 attendus)")
    expected_charts = [
        "Projets par Type InovaYa",
        "Charge Équipe InovaYa",
        "Budget Réalisé InovaYa",
        "Budget Prévu InovaYa",
    ]
    for chart in expected_charts:
        exists = frappe.db.exists("Dashboard Chart", chart)
        print(f"  {'✅' if exists else '❌'} {chart}")
        if not exists:
            errors.append(f"Dashboard Chart manquant : {chart}")

    # ── 10. Hooks doc_events ───────────────────────────────────────────────────
    print("\n[10] Hooks doc_events")
    hooks = frappe.get_hooks("doc_events", app_name="inovaya_gdp")
    expected_events = {
        "Project": ["before_save"],
        "Task": ["before_save", "after_save"],
        "Purchase Order": ["before_save", "on_update", "on_submit"],
        "Leave Application": ["on_submit", "on_cancel"],
        "Jalon Facturation InovaYa": ["on_update"],
    }
    for doctype, events in expected_events.items():
        dt_hooks = hooks.get(doctype, {})
        for ev in events:
            handler = dt_hooks.get(ev)
            found = bool(handler)
            print(f"  {'✅' if found else '❌'} {doctype}.{ev}")
            if not found:
                errors.append(f"Hook manquant : {doctype}.{ev}")

    # ── 11. Scheduler events ───────────────────────────────────────────────────
    print("\n[11] Scheduler events")
    sched = frappe.get_hooks("scheduler_events", app_name="inovaya_gdp")
    for freq, handlers in [("weekly", 1), ("daily", 1)]:
        h = sched.get(freq, [])
        ok = len(h) >= handlers
        print(f"  {'✅' if ok else '❌'} {freq} : {len(h)} handler(s)")
        if not ok:
            errors.append(f"Scheduler {freq} manquant")

    # ── BILAN ─────────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    if not errors:
        print("  ✅ INSTALLATION VALIDE — Prêt pour Frappe Cloud")
    else:
        print(f"  ❌ {len(errors)} ERREUR(S) DÉTECTÉE(S) :")
        for e in errors:
            print(f"     • {e}")
    print("=" * 60 + "\n")

    return len(errors) == 0
