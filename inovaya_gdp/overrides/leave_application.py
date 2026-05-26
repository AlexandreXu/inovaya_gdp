import frappe
from frappe.utils import getdate


# ---------------------------------------------------------------------------
# B23 — Alertes congé vs tâches projet existantes
#
# Prérequis : app "hrms" installée (fournit le DocType "Leave Application").
# Le hook est enregistré dans hooks.py ; il est silencieux si hrms est absent.
# ---------------------------------------------------------------------------

def _get_user_email(employee_id):
    """Retourne l'email (user_id) d'un Employee, ou None."""
    if not employee_id:
        return None
    user_id = frappe.db.get_value("Employee", employee_id, "user_id")
    if not user_id:
        frappe.logger().warning(
            "[B23] Employé %s sans user_id — impossible de chercher ses tâches.", employee_id
        )
        return None
    email = frappe.db.get_value("User", user_id, "email")
    return email or user_id   # user_id est souvent l'email


def _get_manager_email(employee_id):
    """Résout email du manager via Employee.reports_to → user_id → email."""
    if not employee_id:
        return None
    reports_to = frappe.db.get_value("Employee", employee_id, "reports_to")
    if not reports_to:
        frappe.logger().warning("[B23] Employé %s sans reports_to.", employee_id)
        return None
    mgr_user = frappe.db.get_value("Employee", reports_to, "user_id")
    if not mgr_user:
        frappe.logger().warning("[B23] Manager %s sans user_id.", reports_to)
        return None
    return frappe.db.get_value("User", mgr_user, "email") or mgr_user


def _get_project_owner_email(project_name):
    """
    Retourne l'email du responsable projet.
    Project.project_manager n'existe pas en ERPNext v16 ;
    on utilise Project.owner (créateur du document = chef de projet par défaut).
    """
    if not project_name:
        return None
    owner = frappe.db.get_value("Project", project_name, "owner")
    if not owner:
        return None
    return frappe.db.get_value("User", owner, "email") or owner


def _find_conflicting_tasks(user_email, leave_start, leave_end):
    """
    Retourne la liste des tâches actives qui chevauchent la période de congé
    pour l'utilisateur donné.

    Deux vecteurs de recherche :
    1. Affectation directe : Task._assign contient l'email (JSON Frappe).
    2. Appartenance projet : l'utilisateur est dans Project User du projet
       lié à la tâche.

    Les tâches template, complétées ou annulées sont exclues.
    exp_start_date / exp_end_date sont des Datetime → DATE() pour comparaison.
    """
    if not user_email:
        return []

    like_pattern = '%"' + user_email + '"%'

    rows = frappe.db.sql(
        """
        SELECT DISTINCT
            t.name,
            t.subject,
            t.project,
            DATE(t.exp_start_date) AS start_date,
            DATE(t.exp_end_date)   AS end_date
        FROM `tabTask` t
        WHERE t.is_template = 0
          AND t.status NOT IN ('Completed', 'Cancelled')
          AND t.exp_start_date IS NOT NULL
          AND t.exp_end_date   IS NOT NULL
          AND DATE(t.exp_start_date) <= %(leave_end)s
          AND DATE(t.exp_end_date)   >= %(leave_start)s
          AND (
              t._assign LIKE %(like_pattern)s
              OR t.project IN (
                  SELECT pu.parent
                  FROM `tabProject User` pu
                  WHERE pu.user = %(user_email)s
              )
          )
        ORDER BY t.exp_start_date
        """,
        {
            "leave_start": leave_start,
            "leave_end":   leave_end,
            "user_email":  user_email,
            "like_pattern": like_pattern,
        },
        as_dict=True,
    )
    return rows


def _build_email_body(employee_name, leave_start, leave_end, leave_type, tasks):
    """Construit le corps HTML du mail d'alerte."""
    rows_html = ""
    for t in tasks:
        project_label = t.project or "(sans projet)"
        rows_html += (
            "<tr>"
            "<td style='padding:6px 12px;border-bottom:1px solid #eee;'>" + str(t.subject) + "</td>"
            "<td style='padding:6px 12px;border-bottom:1px solid #eee;'>" + project_label + "</td>"
            "<td style='padding:6px 12px;border-bottom:1px solid #eee;'>" + str(t.start_date or "—") + "</td>"
            "<td style='padding:6px 12px;border-bottom:1px solid #eee;'>" + str(t.end_date or "—") + "</td>"
            "</tr>"
        )

    return (
        "<p>Bonjour,</p>"
        "<p>Une demande de congé a été validée pour <strong>" + employee_name + "</strong> "
        "et chevauche des tâches projet planifiées.</p>"
        "<table style='border-collapse:collapse;font-size:14px;'>"
        "<tr style='background:#f5f5f5;'>"
        "<td style='padding:6px 12px;font-weight:bold;'>Type de congé</td>"
        "<td style='padding:6px 12px;'>" + str(leave_type or "—") + "</td></tr>"
        "<tr><td style='padding:6px 12px;font-weight:bold;'>Début</td>"
        "<td style='padding:6px 12px;'>" + str(leave_start) + "</td></tr>"
        "<tr><td style='padding:6px 12px;font-weight:bold;'>Fin</td>"
        "<td style='padding:6px 12px;'>" + str(leave_end) + "</td></tr>"
        "</table>"
        "<br>"
        "<p><strong>Tâches en conflit (" + str(len(tasks)) + ") :</strong></p>"
        "<table style='border-collapse:collapse;font-size:14px;width:100%;'>"
        "<tr style='background:#f5f5f5;'>"
        "<th style='padding:6px 12px;text-align:left;'>Tâche</th>"
        "<th style='padding:6px 12px;text-align:left;'>Projet</th>"
        "<th style='padding:6px 12px;text-align:left;'>Début prévu</th>"
        "<th style='padding:6px 12px;text-align:left;'>Fin prévue</th>"
        "</tr>"
        + rows_html +
        "</table>"
        "<br>"
        "<p style='color:#888;font-size:12px;'>"
        "Ce message est généré automatiquement par InovaYa GdP (B23). "
        "Il est informatif — aucune action automatique n'a été déclenchée."
        "</p>"
    )


def on_submit(doc, method=None):
    """
    B23 — Détection de conflits congé ↔ tâches projet à la soumission
    d'une Leave Application.

    Comportement :
    - Aucun blocage : la Leave Application est soumise normalement.
    - Si aucun conflit : silent exit.
    - Si conflit : email au manager direct + email du responsable de chaque
      projet impacté (Project.owner, faute de project_manager en v16).
    """
    employee_id   = doc.employee
    employee_name = doc.employee_name or employee_id or "(sans nom)"
    leave_start   = getdate(doc.from_date)
    leave_end     = getdate(doc.to_date)
    leave_type    = getattr(doc, "leave_type", None)

    user_email = _get_user_email(employee_id)
    if not user_email:
        frappe.logger().warning(
            "[B23] Leave Application %s : employee sans user_id, analyse impossible.", doc.name
        )
        return

    tasks = _find_conflicting_tasks(user_email, leave_start, leave_end)

    if not tasks:
        frappe.logger().info(
            "[B23] Leave Application %s (%s) : aucun conflit détecté.", doc.name, employee_name
        )
        return

    frappe.logger().info(
        "[B23] %d conflit(s) détecté(s) pour %s (%s → %s).",
        len(tasks), employee_name, leave_start, leave_end,
    )

    # --- Construire la liste des destinataires ---
    recipients = set()

    manager_email = _get_manager_email(employee_id)
    if manager_email:
        recipients.add(manager_email)
    else:
        frappe.logger().warning("[B23] Manager introuvable pour %s.", employee_name)

    # Un email par projet impacté (owner du projet)
    projects_seen = set()
    for t in tasks:
        if t.project and t.project not in projects_seen:
            projects_seen.add(t.project)
            owner_email = _get_project_owner_email(t.project)
            if owner_email:
                recipients.add(owner_email)

    if not recipients:
        frappe.logger().warning(
            "[B23] Aucun destinataire résolu pour %s — alerte non envoyée.", employee_name
        )
        return

    subject = (
        "[InovaYa] Conflit congé / tâches — "
        + employee_name
        + " (" + str(leave_start) + " → " + str(leave_end) + ")"
    )
    message = _build_email_body(employee_name, leave_start, leave_end, leave_type, tasks)

    frappe.sendmail(
        recipients=list(recipients),
        subject=subject,
        message=message,
        now=True,
    )
    frappe.logger().info(
        "[B23] Alerte envoyée → %s", list(recipients)
    )


# ---------------------------------------------------------------------------
# Utilitaire : test dry_run en console sans Leave Application réelle
# ---------------------------------------------------------------------------

def dry_run(employee_id, from_date, to_date, leave_type="Congés payés"):
    """
    Simule on_submit sans envoyer de mail.
    Usage depuis bench console :
        from inovaya_gdp.overrides.leave_application import dry_run
        dry_run('EMP-0001', '2026-06-01', '2026-06-07')
    """
    from frappe.utils import getdate as _getdate

    leave_start = _getdate(from_date)
    leave_end   = _getdate(to_date)

    employee_name = frappe.db.get_value("Employee", employee_id, "employee_name") or employee_id
    user_email    = _get_user_email(employee_id)
    manager_email = _get_manager_email(employee_id)

    print("[B23 dry_run]")
    print("  Employé      : " + employee_name + " (" + str(employee_id) + ")")
    print("  User email   : " + str(user_email))
    print("  Manager email: " + str(manager_email))
    print("  Congé        : " + str(leave_start) + " → " + str(leave_end))
    print("  Type congé   : " + str(leave_type))
    print("")

    if not user_email:
        print("  [WARN] Aucun user_email — analyse impossible.")
        return

    tasks = _find_conflicting_tasks(user_email, leave_start, leave_end)

    if not tasks:
        print("  Résultat : AUCUN CONFLIT détecté pour cette période.")
        return

    print("  Résultat : " + str(len(tasks)) + " conflit(s) détecté(s) :")
    for t in tasks:
        print(
            "    - [" + str(t.project or "sans projet") + "] "
            + str(t.subject)
            + "  (" + str(t.start_date) + " → " + str(t.end_date) + ")"
        )

    # Résoudre les destinataires
    recipients = set()
    if manager_email:
        recipients.add(manager_email)
    projects_seen = set()
    for t in tasks:
        if t.project and t.project not in projects_seen:
            projects_seen.add(t.project)
            owner_email = _get_project_owner_email(t.project)
            if owner_email:
                recipients.add(owner_email)

    print("")
    print("  Destinataires résolus : " + str(sorted(recipients)))
    print("  (dry_run — aucun mail envoyé)")
