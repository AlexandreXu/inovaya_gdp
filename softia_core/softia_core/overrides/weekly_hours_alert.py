import datetime
import frappe
from frappe.utils import getdate, nowdate


def _get_app_name():
    return frappe.db.get_single_value("System Settings", "softia_app_name") or "Softia ERP"


def _get_week_bounds(reference_date=None):
    d = getdate(reference_date or nowdate())
    monday = d - datetime.timedelta(days=d.weekday())
    sunday = monday + datetime.timedelta(days=6)
    return monday, sunday


def _get_rh_emails():
    """Retourne les emails des utilisateurs ayant le rôle softia_hr_role (System Settings)."""
    hr_role = frappe.db.get_single_value("System Settings", "softia_hr_role") or "HR Manager"
    rh_users = frappe.get_all(
        "Has Role",
        filters={"role": hr_role, "parenttype": "User"},
        pluck="parent",
    )
    emails = []
    for uid in rh_users:
        email = frappe.db.get_value("User", uid, "email")
        if email:
            emails.append(email)
    return emails


def _get_manager_email(employee_id):
    if not employee_id:
        return None
    reports_to = frappe.db.get_value("Employee", employee_id, "reports_to")
    if not reports_to:
        frappe.logger().warning("[B07] Employé %s sans reports_to.", employee_id)
        return None
    manager_user = frappe.db.get_value("Employee", reports_to, "user_id")
    if not manager_user:
        frappe.logger().warning("[B07] Manager %s sans user_id.", reports_to)
        return None
    return frappe.db.get_value("User", manager_user, "email")


def _build_email_body(employee_name, total_hours, threshold, week_start, week_end, projects):
    app_name = _get_app_name()
    projects_html = "".join("<li>" + p + "</li>" for p in projects) if projects \
                    else "<li>(aucun projet renseigné)</li>"
    excess = round(total_hours - threshold, 2)
    return (
        "<p>Bonjour,</p>"
        "<p>Le collaborateur <strong>" + employee_name + "</strong> "
        "a dépassé le seuil hebdomadaire d'heures de travail.</p>"
        "<table style='border-collapse:collapse;font-family:sans-serif;font-size:14px;'>"
        "<tr><td style='padding:4px 12px 4px 0;color:#555;'>Semaine</td>"
        "<td><strong>" + str(week_start) + " → " + str(week_end) + "</strong></td></tr>"
        "<tr><td style='padding:4px 12px 4px 0;color:#555;'>Heures réalisées</td>"
        "<td><strong>" + str(total_hours) + " h</strong></td></tr>"
        "<tr><td style='padding:4px 12px 4px 0;color:#555;'>Seuil configuré</td>"
        "<td>" + str(threshold) + " h</td></tr>"
        "<tr><td style='padding:4px 12px 4px 0;color:#555;'>Dépassement</td>"
        "<td style='color:#c0392b;font-weight:bold;'>+" + str(excess) + " h</td></tr>"
        "</table>"
        "<p><strong>Projets concernés :</strong></p>"
        "<ul>" + projects_html + "</ul>"
        "<hr style='border:none;border-top:1px solid #eee;margin-top:24px;'/>"
        "<p style='color:#999;font-size:12px;'>Ce message est généré automatiquement par "
        + app_name + " (B07).<br>"
        "Merci de vérifier la situation avec le collaborateur concerné.</p>"
    )


def run(dry_run=False, reference_date=None):
    """B07 — Alertes hebdomadaires dépassement heures. Scheduler weekly ou bench execute."""
    threshold = float(
        frappe.db.get_single_value("System Settings", "softia_weekly_hours_threshold") or 39.0
    )
    week_start, week_end = _get_week_bounds(reference_date)
    frappe.logger().info("[B07] Analyse %s → %s | seuil=%.1fh", week_start, week_end, threshold)
    if dry_run:
        print(f"\n[B07] Semaine analysée : {week_start} → {week_end} | seuil={threshold}h")

    rows = frappe.db.sql(
        """
        SELECT ts.employee, ts.employee_name,
               SUM(tsd.hours) AS total_hours,
               GROUP_CONCAT(DISTINCT NULLIF(tsd.project,'') ORDER BY tsd.project SEPARATOR '||') AS projects_raw
        FROM `tabTimesheet Detail` tsd
        INNER JOIN `tabTimesheet` ts ON ts.name = tsd.parent
        WHERE ts.docstatus = 1
          AND DATE(tsd.from_time) >= %(week_start)s
          AND DATE(tsd.from_time) <= %(week_end)s
          AND tsd.hours > 0
        GROUP BY ts.employee, ts.employee_name
        HAVING total_hours > %(threshold)s
        ORDER BY total_hours DESC
        """,
        {"week_start": week_start, "week_end": week_end, "threshold": threshold},
        as_dict=True,
    )

    if not rows:
        msg = f"[B07] Aucun dépassement détecté pour la semaine {week_start} → {week_end}."
        frappe.logger().info(msg)
        if dry_run:
            print(msg)
        return

    rh_emails = _get_rh_emails()
    app_name  = _get_app_name()
    alerts_sent = 0

    for row in rows:
        employee_id   = row.employee
        employee_name = row.employee_name or employee_id or "(sans nom)"
        total_hours   = round(float(row.total_hours), 2)
        projects      = [p.strip() for p in (row.projects_raw or "").split("||") if p.strip()]
        manager_email = _get_manager_email(employee_id)
        recipients = list(rh_emails)
        if manager_email and manager_email not in recipients:
            recipients.append(manager_email)
        if dry_run:
            print(f"\n  --- Alerte (dry_run) ---")
            print(f"  Collaborateur : {employee_name} ({employee_id})")
            print(f"  Heures        : {total_hours}h (seuil={threshold}h, +{round(total_hours-threshold,2)}h)")
            print(f"  Destinataires : {recipients}")
            continue
        if not recipients:
            continue
        subject = (f"[{app_name}] Dépassement heures hebdomadaires — "
                   f"{employee_name} ({total_hours}h / seuil {threshold}h)")
        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=_build_email_body(employee_name, total_hours, threshold,
                                      week_start, week_end, projects),
            now=True,
        )
        alerts_sent += 1

    if not dry_run:
        frappe.logger().info("[B07] %d alerte(s) envoyée(s).", alerts_sent)
