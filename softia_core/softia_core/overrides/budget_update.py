"""
B20 — Alimentation budget ETPs par heures réelles Timesheets soumises.
DocType cible : "Budget Detaille Projet" (renommé depuis "Budget Detaille InovaYa").
"""
import frappe


def run():
    if frappe.flags.in_import or frappe.flags.in_migrate:
        return

    rate = _get_hourly_rate()
    if rate <= 0:
        frappe.logger().warning("[B20] softia_default_hourly_rate = %s — annulé.", rate)
        return 0

    rows = frappe.db.sql(
        """
        SELECT td.project, ROUND(SUM(td.hours), 4) AS total_hours
        FROM `tabTimesheet Detail` td
        INNER JOIN `tabTimesheet` ts ON ts.name = td.parent AND ts.docstatus = 1
        WHERE td.project IS NOT NULL AND td.project != ''
        GROUP BY td.project
        """,
        as_dict=True,
    )
    if not rows:
        frappe.logger().info("[B20] Aucune Timesheet soumise avec projet.")
        return 0

    updated = 0
    for r in rows:
        exists = frappe.db.sql(
            "SELECT name FROM `tabBudget Detaille Projet` "
            "WHERE parent=%s AND category='ETPs' LIMIT 1",
            (r.project,),
        )
        if not exists:
            continue
        amount = round(r.total_hours * rate, 2)
        frappe.db.sql(
            """
            UPDATE `tabBudget Detaille Projet`
            SET amount_actual = %s, modified = NOW(), modified_by = 'Administrator'
            WHERE parent = %s AND category = 'ETPs'
            """,
            (amount, r.project),
        )
        updated += 1
        frappe.logger().info("[B20] Budget ETPs projet=%s : %.2f€.", r.project, amount)

    frappe.db.commit()
    frappe.logger().info("[B20] %d projet(s) mis à jour.", updated)
    return updated


def _get_hourly_rate():
    val = frappe.db.get_single_value("System Settings", "softia_default_hourly_rate")
    try:
        return float(val) if val else 0.0
    except (TypeError, ValueError):
        return 0.0
