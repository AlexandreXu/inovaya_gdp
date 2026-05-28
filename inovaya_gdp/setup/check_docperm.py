"""
Vérifie dans quelle table les permissions custom ont été écrites.
bench --site inovaya.localhost execute inovaya_gdp.setup.check_docperm.run
"""
import frappe


def run():
    roles = ("Responsable GdP", "Collaborateur Projet")
    dts   = ("Project", "Task", "Timesheet")

    print("\n── tabDocPerm ──────────────────────────────────────────────")
    rows = frappe.db.sql(
        """SELECT parent, role, permlevel, `read`, `write`, `create`
           FROM `tabDocPerm`
           WHERE role IN %(roles)s AND parent IN %(dts)s
           ORDER BY parent, role""",
        {"roles": roles, "dts": dts},
        as_dict=True,
    )
    if rows:
        for r in rows:
            print(f"  {r.parent:<12} {r.role:<25} pl={r.permlevel}"
                  f"  r={r.read} w={r.write} c={r['create']}")
    else:
        print("  (vide)")

    print("\n── tabCustom DocPerm ───────────────────────────────────────")
    rows2 = frappe.db.sql(
        """SELECT parent, role, permlevel, `read`, `write`, `create`
           FROM `tabCustom DocPerm`
           WHERE role IN %(roles)s AND parent IN %(dts)s
           ORDER BY parent, role""",
        {"roles": roles, "dts": dts},
        as_dict=True,
    )
    if rows2:
        for r in rows2:
            print(f"  {r.parent:<12} {r.role:<25} pl={r.permlevel}"
                  f"  r={r.read} w={r.write} c={r['create']}")
    else:
        print("  (vide)")

    # Vérifier aussi le get_all standard (qui suit reset_perms_cache)
    print("\n── frappe.get_all DocPerm (ORM) ────────────────────────────")
    rows3 = frappe.get_all(
        "DocPerm",
        filters={"parent": ["in", list(dts)], "role": ["in", list(roles)]},
        fields=["parent", "role", "permlevel", "read", "write", "create"],
        order_by="parent",
    )
    if rows3:
        for r in rows3:
            print(f"  {r.parent:<12} {r.role:<25} pl={r.permlevel}"
                  f"  r={r.read} w={r.write} c={r['create']}")
    else:
        print("  (vide)")
