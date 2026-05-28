"""
Installation minimale de softia_core.
Pas de données démo — chaque prospect crée ses propres fixtures.
"""
import frappe


def after_install():
    """Appelé après bench install-app softia_core."""
    frappe.logger().info("[softia_core] Installation terminée.")
    frappe.msgprint(
        "softia_core installé. Configurez System Settings (softia_app_name, "
        "softia_daily_hours_threshold, softia_weekly_hours_threshold, "
        "softia_default_hourly_rate, softia_hr_role, softia_importance_roles).",
        title="softia_core",
        indicator="green",
    )


def after_migrate():
    """Appelé après bench migrate."""
    frappe.logger().info("[softia_core] Migration terminée.")
