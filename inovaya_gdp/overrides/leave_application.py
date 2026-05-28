import frappe
from frappe.utils import getdate


# ---------------------------------------------------------------------------
# B23 — Alertes congé vs tâches projet existantes
# B22 — Synchronisation absences ↔ planning (flag inovaya_conflit_absence)
#
# Prérequis : app "hrms" installée (fournit le DocType "Leave Application").
# Le hook est enregistré dans hooks.py ; il est silencieux si hrms est absent.
#
# B22 on_submit : détecte les Task chevauchant le congé → marque
#   inovaya_conflit_absence=1 (check, read_only).
# B22 on_cancel : réinitialise inovaya_conflit_absence=0 sur les mêmes tâches,
#   sauf si une autre Leave Application active couvre encore la tâche.
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


# ---------------------------------------------------------------------------
# B22 — Gestion du flag inovaya_conflit_absence sur Task
# ---------------------------------------------------------------------------

def _set_conflict_flag(task_name, value):
    """Positionne inovaya_conflit_absence sans mettre à jour modified."""
    frappe.db.set_value("Task", task_name, "inovaya_conflit_absence", value, update_modified=False)


def _has_other_active_leave(user_email, task_start, task_end, exclude_la=None):
    """
    Retourne True si une autre Leave Application soumise (docstatus=1)
    couvre encore la période de la tâche pour cet employé.
    Utilisé au on_cancel pour décider si on réinitialise le flag.
    """
    params = {
        "user_email": str(task_start),   # réutilisation de la variable ci-dessous
    }
    # Requête : LA active, même employé (via user_id), qui chevauche [task_start, task_end]
    sql = """
        SELECT la.name
        FROM `tabLeave Application` la
        INNER JOIN `tabEmployee` e ON e.name = la.employee
        WHERE e.user_id = %(user_email)s
          AND la.docstatus = 1
          AND la.from_date <= %(task_end)s
          AND la.to_date   >= %(task_start)s
    """
    p = {
        "user_email": user_email,
        "task_start": str(task_start),
        "task_end":   str(task_end),
    }
    if exclude_la:
        sql += " AND la.name != %(exclude_la)s"
        p["exclude_la"] = exclude_la

    rows = frappe.db.sql(sql, p)
    return bool(rows)


# ---------------------------------------------------------------------------
# B23 — Alerte + B22 flag à la soumission
# ---------------------------------------------------------------------------

def on_submit(doc, method=None):
    """
    B23 — Alerte congé ↔ tâches projet (email manager + chef projet).
    B22 — Marquage inovaya_conflit_absence=1 sur les tâches en conflit.

    Comportement :
    - Aucun blocage : la Leave Application est soumise normalement.
    - Si aucun conflit : silent exit.
    - Si conflit : flag tâches (B22) + email (B23).
    """
    if frappe.flags.in_import or frappe.flags.in_migrate or frappe.flags.in_test:
        return

    employee_id   = doc.employee
    employee_name = doc.employee_name or employee_id or "(sans nom)"
    leave_start   = getdate(doc.from_date)
    leave_end     = getdate(doc.to_date)
    leave_type    = getattr(doc, "leave_type", None)

    user_email = _get_user_email(employee_id)
    if not user_email:
        frappe.logger().warning(
            "[B23/B22] Leave Application %s : employee sans user_id, analyse impossible.", doc.name
        )
        return

    tasks = _find_conflicting_tasks(user_email, leave_start, leave_end)

    if not tasks:
        frappe.logger().info(
            "[B23/B22] Leave Application %s (%s) : aucun conflit détecté.", doc.name, employee_name
        )
        return

    frappe.logger().info(
        "[B23/B22] %d conflit(s) détecté(s) pour %s (%s → %s).",
        len(tasks), employee_name, leave_start, leave_end,
    )

    # ── B22 : marquer les tâches en conflit ─────────────────────────────
    for t in tasks:
        _set_conflict_flag(t.name, 1)
        frappe.logger().info("[B22] Task %s marquée inovaya_conflit_absence=1.", t.name)

    # ── B23 : notification email ─────────────────────────────────────────
    recipients = set()

    manager_email = _get_manager_email(employee_id)
    if manager_email:
        recipients.add(manager_email)
    else:
        frappe.logger().warning("[B23] Manager introuvable pour %s.", employee_name)

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
# B22 — Réinitialisation du flag à l'annulation
# ---------------------------------------------------------------------------

def on_cancel(doc, method=None):
    """
    B22 — Réinitialise inovaya_conflit_absence=0 sur les tâches qui chevauchaient
    le congé annulé, SAUF si une autre Leave Application active couvre encore la tâche.
    """
    if frappe.flags.in_import or frappe.flags.in_migrate or frappe.flags.in_test:
        return

    employee_id   = doc.employee
    employee_name = doc.employee_name or employee_id or "(sans nom)"
    leave_start   = getdate(doc.from_date)
    leave_end     = getdate(doc.to_date)

    user_email = _get_user_email(employee_id)
    if not user_email:
        frappe.logger().warning(
            "[B22] on_cancel : employee %s sans user_id, réinitialisation impossible.", employee_id
        )
        return

    tasks = _find_conflicting_tasks(user_email, leave_start, leave_end)
    if not tasks:
        return

    reset_count = 0
    for t in tasks:
        # Ne réinitialiser que si aucune autre LA active couvre encore cette tâche
        if not _has_other_active_leave(
            user_email,
            task_start=t.start_date,
            task_end=t.end_date,
            exclude_la=doc.name,
        ):
            _set_conflict_flag(t.name, 0)
            reset_count += 1
            frappe.logger().info(
                "[B22] Task %s : inovaya_conflit_absence réinitialisé à 0.", t.name
            )
        else:
            frappe.logger().info(
                "[B22] Task %s : autre absence active → flag maintenu à 1.", t.name
            )

    frappe.logger().info(
        "[B22] on_cancel %s (%s) : %d tâche(s) réinitialisée(s) sur %d.",
        doc.name, employee_name, reset_count, len(tasks),
    )


# ---------------------------------------------------------------------------
# Utilitaire : test dry_run en console sans Leave Application réelle
# ---------------------------------------------------------------------------

def dry_run(employee_id, from_date, to_date, leave_type="Congés payés"):  # noqa: E501
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
