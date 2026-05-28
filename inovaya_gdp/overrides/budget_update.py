"""
B20 — Alimentation du budget ETPs par les heures réelles des Timesheets soumises.

Déclenchement : Scheduled Job quotidien (scheduler_events["daily"]).
Peut aussi être appelé manuellement :
    bench --site inovaya.localhost execute inovaya_gdp.overrides.budget_update.run

Logique :
  1. Lire inovaya_default_hourly_rate dans System Settings (global, €/h).
  2. Pour chaque projet ayant des Timesheets soumises :
     total_coût = SUM(td.hours) × rate
  3. Mettre à jour amount_actual sur la ligne category='ETPs' du Budget Detaille InovaYa.

Contrainte métier (Phase 1) :
  - Un seul taux horaire global (System Settings).
    Si les taux varient par collaborateur → Phase 3 (B20b, taux par Employee).
  - Seuls les projets ayant une ligne ETPs dans Budget Detaille InovaYa sont mis à jour.
    Les autres sont ignorés (pas de création automatique de ligne).
  - Seules les Timesheets soumises (docstatus=1) sont prises en compte.
"""
import frappe
from frappe import _


def run():
    """
    Point d'entrée unique : scheduler quotidien OU appel manuel via bench execute.
    Retourne le nombre de projets mis à jour.
    """
    if frappe.flags.in_import or frappe.flags.in_migrate:
        return

    rate = _get_hourly_rate()
    if rate <= 0:
        frappe.logger().warning(
            "[B20] inovaya_default_hourly_rate = %s dans System Settings — "
            "mise à jour budget annulée.",
            rate,
        )
        return 0

    # Heures réalisées par projet (Timesheets soumises)
    rows = frappe.db.sql(
        """
        SELECT td.project, ROUND(SUM(td.hours), 4) AS total_hours
        FROM `tabTimesheet Detail` td
        INNER JOIN `tabTimesheet` ts
            ON ts.name = td.parent
            AND ts.docstatus = 1
        WHERE td.project IS NOT NULL
          AND td.project != ''
        GROUP BY td.project
        """,
        as_dict=True,
    )

    if not rows:
        frappe.logger().info("[B20] Aucune Timesheet soumise avec projet — rien à mettre à jour.")
        return 0

    updated = 0
    for r in rows:
        # Vérifier qu'une ligne ETPs existe pour ce projet avant de mettre à jour
        exists = frappe.db.sql(
            "SELECT name FROM `tabBudget Detaille InovaYa` WHERE parent=%s AND category='ETPs' LIMIT 1",
            (r.project,),
        )
        if not exists:
            frappe.logger().debug(
                "[B20] Projet=%s : pas de ligne 'ETPs' dans Budget Detaille InovaYa — skip.",
                r.project,
            )
            continue

        amount = round(r.total_hours * rate, 2)
        frappe.db.sql(
            """
            UPDATE `tabBudget Detaille InovaYa`
            SET amount_actual = %s,
                modified       = NOW(),
                modified_by    = 'Administrator'
            WHERE parent   = %s
              AND category = 'ETPs'
            """,
            (amount, r.project),
        )
        updated += 1
        frappe.logger().info(
            "[B20] Budget ETPs projet=%s : %.2fh × %.2f€/h = %.2f€ (amount_actual mis à jour).",
            r.project, r.total_hours, rate, amount,
        )

    frappe.db.commit()
    frappe.logger().info("[B20] %d projet(s) mis à jour.", updated)
    return updated


def _get_hourly_rate():
    """Lit inovaya_default_hourly_rate depuis System Settings (défaut 0)."""
    val = frappe.db.get_single_value("System Settings", "inovaya_default_hourly_rate")
    try:
        return float(val) if val else 0.0
    except (TypeError, ValueError):
        return 0.0
