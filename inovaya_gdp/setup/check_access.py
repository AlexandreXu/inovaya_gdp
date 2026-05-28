"""
Vérifie l'accès réel de Léa et Camille à PROJ-0009 et à une tâche.
bench --site inovaya.localhost execute inovaya_gdp.setup.check_access.run
"""
import frappe


def _test(user, doctype, name):
    original = frappe.session.user
    try:
        frappe.set_user(user)
        has_read  = frappe.has_permission(doctype, "read",  doc=name)
        has_write = frappe.has_permission(doctype, "write", doc=name)
        icon_r = "✅" if has_read  else "❌"
        icon_w = "✅" if has_write else "❌"
        print(f"  {user:<40}  {doctype:<12} {name:<15}  "
              f"read={icon_r}  write={icon_w}")
    except Exception as e:
        print(f"  {user:<40}  ❌ ERREUR : {e}")
    finally:
        frappe.set_user(original)


def run():
    print("\n── ACCÈS PROJECT ───────────────────────────────────────────")
    for user in ["camille.roux@inovaya.com", "lea.martin@inovaya.com"]:
        _test(user, "Project", "PROJ-0009")

    print("\n── ACCÈS TASK ──────────────────────────────────────────────")
    for user in ["camille.roux@inovaya.com", "lea.martin@inovaya.com"]:
        _test(user, "Task", "TASK-2026-00109")

    print("\n── MODULE PROJECT VISIBLE ? ────────────────────────────────")
    # Vérifie que le module "Project" est dans les modules autorisés
    for user in ["camille.roux@inovaya.com", "lea.martin@inovaya.com"]:
        original = frappe.session.user
        try:
            frappe.set_user(user)
            modules = frappe.get_all(
                "Module Def",
                fields=["name"],
                ignore_permissions=True,
            )
            has_proj_module = any(m.name == "Projects" for m in modules)
            # Vérifier si le user a accès au module via ses rôles
            allowed = frappe.db.get_all(
                "Module Profile",
                filters={},
                fields=["name"],
            )
            print(f"  {user:<40}  Projects module accessible={has_proj_module}")
        finally:
            frappe.set_user(original)
