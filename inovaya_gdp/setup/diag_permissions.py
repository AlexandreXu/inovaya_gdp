"""
Diagnostic complet :
  1. Rôles de Léa et Camille
  2. Permissions des rôles custom sur Project / Task / Timesheet
  3. Desk Access des deux comptes
  4. Custom Field Task-inovaya_eisenhower_info (exists, in_list_view)
  5. Valeurs eisenhower_info sur les tâches de PROJ-0009

bench --site inovaya.localhost execute inovaya_gdp.setup.diag_permissions.run
"""
import frappe


def _sep(t):
    print(f"\n{'='*65}\n{t}\n{'='*65}")


def run():
    # ── 1. RÔLES ────────────────────────────────────────────────────────
    _sep("1 — RÔLES UTILISATEURS")
    for email in ["camille.roux@inovaya.com", "lea.martin@inovaya.com"]:
        roles = [r for r in frappe.get_roles(email) if r not in ("All", "Guest")]
        desk  = frappe.db.get_value("User", email, ["user_type", "enabled"], as_dict=True)
        print(f"\n  {email}")
        print(f"    user_type : {desk.user_type if desk else '???'}")
        print(f"    enabled   : {desk.enabled   if desk else '???'}")
        print(f"    rôles     : {', '.join(sorted(roles))}")

    # ── 2. PERMISSIONS RÔLES CUSTOM ────────────────────────────────────
    _sep("2 — PERMISSIONS DocType sur Project / Task / Timesheet")
    custom_roles = ["Responsable GdP", "Collaborateur Projet"]
    doctypes     = ["Project", "Task", "Timesheet"]

    for role in custom_roles:
        print(f"\n  Rôle : {role}")
        perms = frappe.db.get_all(
            "DocPerm",
            filters={"parent": ["in", doctypes], "role": role},
            fields=["parent", "permlevel", "read", "write", "create", "delete"],
            order_by="parent",
        )
        if not perms:
            print("    ❌ AUCUNE permission trouvée sur ces DocTypes")
        else:
            for p in perms:
                print(f"    {p.parent:<12} permlevel={p.permlevel}  "
                      f"read={p.read} write={p.write} create={p.create} delete={p.delete}")

    # ── 3. USER HAS ROLE "System Manager" ou au moins un rôle actif ? ───
    _sep("3 — ACCÈS DESK (user_type = 'System User' ?)")
    for email in ["camille.roux@inovaya.com", "lea.martin@inovaya.com"]:
        ut = frappe.db.get_value("User", email, "user_type")
        print(f"  {email} → user_type={ut!r}  "
              f"({'✅ Desk OK' if ut == 'System User' else '❌ Pas d accès Desk'})")

    # ── 4. CUSTOM FIELD eisenhower_info ─────────────────────────────────
    _sep("4 — CUSTOM FIELD Task-inovaya_eisenhower_info")
    exists = frappe.db.exists("Custom Field", "Task-inovaya_eisenhower_info")
    print(f"  exists         : {exists!r}")
    if exists:
        cf = frappe.db.get_value(
            "Custom Field", "Task-inovaya_eisenhower_info",
            ["fieldtype", "label", "in_list_view", "hidden", "read_only", "insert_after"],
            as_dict=True,
        )
        print(f"  label          : {cf.label}")
        print(f"  fieldtype      : {cf.fieldtype}")
        print(f"  in_list_view   : {cf.in_list_view}  {'✅' if cf.in_list_view else '❌ manquant'}")
        print(f"  hidden         : {cf.hidden}")
        print(f"  read_only      : {cf.read_only}")
        print(f"  insert_after   : {cf.insert_after}")
    else:
        print("  ❌ Champ introuvable — migration probablement pas faite")

    # ── 5. VALEURS eisenhower_info sur PROJ-0009 ─────────────────────────
    _sep("5 — VALEURS inovaya_eisenhower_info sur PROJ-0009")
    tasks = frappe.get_all(
        "Task",
        filters={"project": "PROJ-0009"},
        fields=["name", "subject", "inovaya_eisenhower_info", "inovaya_importance",
                "exp_end_date", "priority"],
        order_by="name",
    )
    if not tasks:
        print("  ❌ Aucune tâche trouvée pour PROJ-0009")
    else:
        for t in tasks:
            q = t.inovaya_eisenhower_info or "—"
            i = t.inovaya_importance     or "—"
            print(f"  {t.name}  {t.subject[:30]:<30}  imp={i:<6}  quadrant={q}")
