import datetime

import frappe
from frappe.utils import getdate, nowdate


# ---------------------------------------------------------------------------
# B07 — Alerte dépassement heures hebdomadaires
# ---------------------------------------------------------------------------

def _get_week_bounds(reference_date=None):
    """
    Retourne (lundi, dimanche) de la semaine contenant reference_date.
    Par défaut : semaine en cours.  Retourne des objets datetime.date.
    """
    d = getdate(reference_date or nowdate())
    monday = d - datetime.timedelta(days=d.weekday())   # weekday() : 0 = lundi
    sunday = monday + datetime.timedelta(days=6)
    return monday, sunday


def _get_rh_emails():
    """Retourne la liste des emails des utilisateurs ayant le rôle RH InovaYa."""
    rh_users = frappe.get_all(
        "Has Role",
        filters={"role": "RH InovaYa", "parenttype": "User"},
        pluck="parent",
    )
    emails = []
    for uid in rh_users:
        email = frappe.db.get_value("User", uid, "email")
        if email:
            emails.append(email)
    return emails


def _get_manager_email(employee_id):
    """
    Résout l'email du manager direct (Employee.reports_to → Employee.user_id → User.email).
    Retourne None si la chaîne est incomplète, en loggant un warning à chaque rupture.
    """
    if not employee_id:
        return None

    reports_to = frappe.db.get_value("Employee", employee_id, "reports_to")
    if not reports_to:
        frappe.logger().warning(
            "[B07] Employé %s sans reports_to — manager non notifié.", employee_id
        )
        return None

    manager_user = frappe.db.get_value("Employee", reports_to, "user_id")
    if not manager_user:
        frappe.logger().warning(
            "[B07] Manager %s (reports_to de %s) sans user_id — email ignoré.",
            reports_to,
            employee_id,
        )
        return None

    email = frappe.db.get_value("User", manager_user, "email")
    if not email:
        frappe.logger().warning(
            "[B07] Utilisateur %s (manager de %s) sans email — ignoré.",
            manager_user,
            employee_id,
        )
    return email


def _build_email_body(employee_name, total_hours, threshold, week_start, week_end, projects):
    """Construit le corps HTML du mail d'alerte."""
    projects_html = "".join(
        "<li>" + p + "</li>" for p in projects
    ) if projects else "<li>(aucun projet renseigné)</li>"

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
        "<p style='color:#999;font-size:12px;'>"
        "Ce message est généré automatiquement par InovaYa GdP (B07).<br>"
        "Merci de vérifier la situation avec le collaborateur concerné."
        "</p>"
    )


def run(dry_run=False, reference_date=None):
    """
    B07 — Calcul hebdomadaire des heures et envoi des alertes.

    Paramètres
    ----------
    dry_run : bool
        Si True, affiche les alertes en console sans envoyer de mail.
        Utile pour les tests et la validation manuelle.
    reference_date : str | date | None
        Date de référence pour déterminer la semaine à analyser.
        Format 'YYYY-MM-DD' ou objet date.  Par défaut : aujourd'hui.

    Appelé automatiquement par le scheduler Frappe (événement ``weekly``).
    """
    threshold = float(
        frappe.db.get_single_value("System Settings", "inovaya_weekly_hours_threshold")
        or 39.0
    )
    week_start, week_end = _get_week_bounds(reference_date)

    frappe.logger().info(
        "[B07] Analyse semaine %s → %s | seuil=%.1fh | dry_run=%s",
        week_start, week_end, threshold, dry_run,
    )
    if dry_run:
        print(
            "\n[B07] Semaine analysée : " + str(week_start) + " → " + str(week_end)
            + " | seuil=" + str(threshold) + "h"
        )

    # ------------------------------------------------------------------
    # Calcul des heures par employé depuis les Timesheets soumises
    # ------------------------------------------------------------------
    rows = frappe.db.sql(
        """
        SELECT
            ts.employee,
            ts.employee_name,
            SUM(tsd.hours)                                          AS total_hours,
            GROUP_CONCAT(
                DISTINCT NULLIF(tsd.project, '')
                ORDER BY tsd.project
                SEPARATOR '||'
            )                                                       AS projects_raw
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
        msg = "[B07] Aucun dépassement détecté pour la semaine " + str(week_start) + " → " + str(week_end) + "."
        frappe.logger().info(msg)
        if dry_run:
            print(msg)
        return

    rh_emails = _get_rh_emails()
    alerts_sent = 0

    for row in rows:
        employee_id   = row.employee
        employee_name = row.employee_name or employee_id or "(sans nom)"
        total_hours   = round(float(row.total_hours), 2)
        projects      = [p.strip() for p in (row.projects_raw or "").split("||") if p.strip()]

        # Destinataires : RH InovaYa + manager direct
        manager_email = _get_manager_email(employee_id)
        recipients = list(rh_emails)
        if manager_email and manager_email not in recipients:
            recipients.append(manager_email)

        if dry_run:
            print("\n  --- Alerte (dry_run) ---")
            print("  Collaborateur : " + employee_name + " (" + str(employee_id) + ")")
            print("  Heures        : " + str(total_hours) + "h  (seuil=" + str(threshold) + "h, +"
                  + str(round(total_hours - threshold, 2)) + "h)")
            print("  Projets       : " + (", ".join(projects) if projects else "(aucun)"))
            print("  Destinataires : " + str(recipients))
            continue

        if not recipients:
            frappe.logger().warning(
                "[B07] Aucun destinataire pour %s — alerte non envoyée.", employee_name
            )
            continue

        subject = (
            "[InovaYa] Dépassement heures hebdomadaires — "
            + employee_name
            + " (" + str(total_hours) + "h / seuil " + str(threshold) + "h)"
        )
        message = _build_email_body(
            employee_name, total_hours, threshold, week_start, week_end, projects
        )

        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=message,
            now=True,
        )
        frappe.logger().info(
            "[B07] Alerte envoyée — %s : %.2fh → %s", employee_name, total_hours, recipients
        )
        alerts_sent += 1

    if dry_run:
        print(
            "\n[B07] dry_run terminé — "
            + str(len(rows)) + " dépassement(s) détecté(s), aucun mail envoyé."
        )
    else:
        frappe.logger().info("[B07] %d alerte(s) envoyée(s).", alerts_sent)
