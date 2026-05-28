"""
Setup B08 — Créer le rapport en DB (SQL direct) + seeder des verticales.
bench --site inovaya.localhost execute inovaya_gdp.setup.setup_b08.run
"""
import frappe
from frappe.utils import now_datetime


def _create_report_direct(name, ref_doctype, module="InovaYa", roles=None):
    """
    Insère un rapport Script Report standard directement en SQL
    (sans passer par la validation ORM qui bloque en non-developer mode).
    """
    if frappe.db.exists("Report", name):
        # S'assurer que is_standard est correct
        frappe.db.sql(
            "UPDATE `tabReport` SET is_standard='Yes', disabled=0 WHERE name=%s",
            (name,),
        )
        frappe.db.commit()
        print(f"  ↻  Report '{name}' déjà existant — mis à jour")
        return

    now = str(now_datetime())
    frappe.db.sql("""
        INSERT INTO `tabReport`
            (name, creation, modified, modified_by, owner, docstatus,
             report_name, ref_doctype, report_type, is_standard, module,
             disabled, add_total_row, prepared_report)
        VALUES
            (%(name)s, %(now)s, %(now)s, 'Administrator', 'Administrator', 0,
             %(name)s, %(ref_doctype)s, 'Script Report', 'Yes', %(module)s,
             0, 1, 0)
    """, {"name": name, "now": now, "ref_doctype": ref_doctype, "module": module})

    if roles:
        for role in roles:
            frappe.db.sql("""
                INSERT INTO `tabHas Role`
                    (name, creation, modified, modified_by, owner,
                     parent, parentfield, parenttype, role)
                VALUES
                    (%(rname)s, %(now)s, %(now)s, 'Administrator', 'Administrator',
                     %(parent)s, 'roles', 'Report', %(role)s)
            """, {"rname": f"{name}-{role}", "now": now, "parent": name, "role": role})

    frappe.db.commit()
    print(f"  ✅ Report '{name}' créé en DB")


def run():
    print("\n=== SETUP B08 — Heures par Verticale ===")

    # ── 1. Créer le rapport en DB ─────────────────────────────────────────
    _create_report_direct(
        name="Heures par Verticale InovaYa",
        ref_doctype="Timesheet",
        roles=["Chef de Projet", "Manager InovaYa", "Responsable GdP",
               "Responsable Operations", "Direction Generale", "System Manager"],
    )

    # ── 2. Seeder des verticales sur les tâches de démo ──────────────────
    verticales = [
        "Traitement Eau Industriel",
        "TEE Collectivités",
        "R&D",
        "Digital",
        "Transversal",
    ]

    tasks = frappe.db.sql("""
        SELECT name FROM `tabTask`
        WHERE is_template = 0
          AND (inovaya_task_vertical IS NULL OR inovaya_task_vertical = '')
        ORDER BY name
        LIMIT 20
    """, as_dict=True)

    print(f"\n  Tâches à seeder : {len(tasks)}")
    for i, t in enumerate(tasks):
        v = verticales[i % len(verticales)]
        frappe.db.set_value("Task", t.name, "inovaya_task_vertical", v, update_modified=False)
    frappe.db.commit()
    print(f"  ✅ {len(tasks)} tâches mises à jour avec une verticale")

    # ── 3. Vérifier la requête principale ────────────────────────────────
    print("\n  Test requête B08 :")
    rows = frappe.db.sql("""
        SELECT
            ts.employee_name,
            COALESCE(NULLIF(t.inovaya_task_vertical, ''), '(non renseignée)') AS verticale,
            ROUND(SUM(td.hours), 2) AS heures_realisees,
            COUNT(td.name) AS nb_saisies
        FROM `tabTimesheet Detail` td
        INNER JOIN `tabTimesheet` ts ON ts.name = td.parent AND ts.docstatus = 1
        LEFT JOIN `tabTask` t ON t.name = td.task
        GROUP BY ts.employee, ts.employee_name,
                 COALESCE(NULLIF(t.inovaya_task_vertical, ''), '(non renseignée)')
        ORDER BY ts.employee_name, verticale
    """, as_dict=True)

    if rows:
        for r in rows:
            print(f"    {(r.employee_name or 'N/A'):<22} | {r.verticale:<32} | {r.heures_realisees}h ({r.nb_saisies} saisies)")
    else:
        print("  ⚠️  Aucune ligne — vérifier les Timesheets soumises")

    # ── 4. Vérifier le rapport en DB ─────────────────────────────────────
    r = frappe.db.get_value("Report", "Heures par Verticale InovaYa",
                             ["name", "is_standard", "ref_doctype"], as_dict=True)
    if r:
        print(f"\n  ✅ Rapport en DB : {r.name} | is_standard={r.is_standard} | ref={r.ref_doctype}")

    print("\n=== FIN SETUP B08 ===\n")
