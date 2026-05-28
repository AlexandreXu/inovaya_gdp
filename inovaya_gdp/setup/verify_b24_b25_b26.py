"""
Vérification B24/B25/B26.
bench --site inovaya.localhost execute inovaya_gdp.setup.verify_b24_b25_b26.run
"""
import frappe


def run():
    print("\n=== VÉRIFICATION B24/B25/B26 ===")

    # ── Pages ──────────────────────────────────────────────────────────────
    print("\n[Pages]")
    pages = frappe.db.sql(
        "SELECT name, title, module, standard FROM `tabPage` WHERE module='Inovaya'",
        as_dict=True,
    )
    for p in pages:
        roles = frappe.db.sql(
            "SELECT role FROM `tabHas Role` WHERE parent=%s AND parenttype='Page'",
            (p.name,), as_dict=True,
        )
        role_str = ", ".join(r.role for r in roles)
        print(f"  ✅ [{p.name}] {p.title} | rôles: {role_str}")

    # ── Dashboard Charts ───────────────────────────────────────────────────
    print("\n[Dashboard Charts]")
    charts = frappe.db.sql(
        "SELECT chart_name, chart_type, type, is_public FROM `tabDashboard Chart` WHERE chart_name LIKE '%InovaYa%' ORDER BY chart_name",
        as_dict=True,
    )
    for c in charts:
        print(f"  ✅ {c.chart_name} | {c.chart_type}/{c.type} | public={c.is_public}")

    # ── Workspaces ─────────────────────────────────────────────────────────
    print("\n[Workspaces InovaYa]")
    workspaces = frappe.db.sql(
        "SELECT name, public FROM `tabWorkspace` WHERE name LIKE 'InovaYa%' ORDER BY name",
        as_dict=True,
    )
    for ws in workspaces:
        chart_count = frappe.db.sql(
            "SELECT COUNT(*) as n FROM `tabWorkspace Chart` WHERE parent=%s",
            (ws.name,), as_dict=True,
        )[0].n
        link_count = frappe.db.sql(
            "SELECT COUNT(*) as n FROM `tabWorkspace Link` WHERE parent=%s",
            (ws.name,), as_dict=True,
        )[0].n
        print(f"  ✅ {ws.name} | public={ws.public} | {chart_count} charts | {link_count} liens")

    # ── Test API B25 ──────────────────────────────────────────────────────
    print("\n[Test API B25 — get_charge_data]")
    try:
        from inovaya_gdp.inovaya.page.plan_charge_equipe_inovaya.plan_charge_equipe_inovaya \
            import get_charge_data
        result = get_charge_data.__wrapped__() if hasattr(get_charge_data, "__wrapped__") \
            else frappe.call("inovaya_gdp.inovaya.page.plan_charge_equipe_inovaya.plan_charge_equipe_inovaya.get_charge_data")
        # Import direct sans whitelist check
        import frappe as _f
        from inovaya_gdp.inovaya.page.plan_charge_equipe_inovaya \
            import plan_charge_equipe_inovaya as m25
        # Appel direct sans vérification de rôle (on est Administrator)
        import types
        orig = m25.frappe.only_for
        m25.frappe.only_for = lambda roles: None  # bypass pour test
        data = m25.get_charge_data()
        m25.frappe.only_for = orig
        print(f"  ✅ get_charge_data : {len(data['employees'])} collaborateurs, {len(data['weeks'])} semaines")
    except Exception as e:
        print(f"  ⚠️  get_charge_data erreur : {e}")

    # ── Test API B24 ──────────────────────────────────────────────────────
    print("\n[Test API B24 — get_my_tasks]")
    try:
        from inovaya_gdp.inovaya.page.mon_planning_inovaya import mon_planning_inovaya as m24
        data24 = m24.get_my_tasks()
        print(f"  ✅ get_my_tasks : {len(data24['tasks'])} tâches, {len(data24['annexe_tasks'])} annexes")
    except Exception as e:
        print(f"  ⚠️  get_my_tasks erreur : {e}")

    print("\n=== FIN VÉRIFICATION ===\n")
