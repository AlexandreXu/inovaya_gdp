"""
Fix permissions B10 — Direction Générale read-only sur Impact Projet InovaYa.
bench --site inovaya.localhost execute inovaya_gdp.setup.fix_b10_perms.run
"""
import frappe


def run():
    print("\n=== FIX B10 — Permissions Direction Générale ===")
    # Corriger : Direction Générale = read uniquement
    frappe.db.sql("""
        UPDATE `tabDocPerm`
        SET `write`=0, `create`=0, `delete`=0, `submit`=0, `cancel`=0, `amend`=0
        WHERE parent='Impact Projet InovaYa' AND role='Direction Generale'
    """)
    frappe.db.commit()
    print("  ✅ Direction Générale → read-only")

    # Vérification
    perms = frappe.db.sql(
        "SELECT role, `read`, `write`, `create`, `delete` FROM `tabDocPerm` WHERE parent='Impact Projet InovaYa'",
        as_dict=True,
    )
    for p in perms:
        print(f"  🔑 {p.role} — r={p.read} w={p.write} c={p.create} d={p.delete}")
    print()
