import frappe
from frappe.utils import getdate


def _get_app_name():
    """Lit softia_app_name depuis System Settings (défaut 'Softia ERP')."""
    return frappe.db.get_single_value("System Settings", "softia_app_name") or "Softia ERP"


def _get_user_email(employee_id):
    if not employee_id:
        return None
    user_id = frappe.db.get_value("Employee", employee_id, "user_id")
    if not user_id:
        frappe.logger().warning("[B23] Employé %s sans user_id.", employee_id)
        return None
    return frappe.db.get_value("User", user_id, "email") or user_id


def _get_manager_email(employee_id):
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
    if not project_name:
        return None
    owner = frappe.db.get_value("Project", project_name, "owner")
    if not owner:
        return None
    return frappe.db.get_value("User", owner, "email") or owner


def _find_conflicting_tasks(user_email, leave_start, leave_end):
    if not user_email:
        return []
    like_pattern = '%"' + user_email + '"%'
    rows = frappe.db.sql(
        """
        SELECT DISTINCT t.name, t.subject, t.project,
               DATE(t.exp_start_date) AS start_date,
               DATE(t.exp_end_date)   AS end_date
        FROM `tabTask` t
        WHERE t.is_template = 0
          AND t.status NOT IN ('Completed', 'Cancelled')
          AND t.exp_start_date IS NOT NULL AND t.exp_end_date IS NOT NULL
          AND DATE(t.exp_start_date) <= %(leave_end)s
          AND DATE(t.exp_end_date)   >= %(leave_start)s
          AND (
              t._assign LIKE %(like_pattern)s
              OR t.project IN (
                  SELECT pu.parent FROM `tabProject User` pu WHERE pu.user = %(user_email)s
              )
          )
        ORDER BY t.exp_start_date
        """,
        {"leave_start": leave_start, "leave_end": leave_end,
         "user_email": user_email, "like_pattern": like_pattern},
        as_dict=True,
    )
    return rows


def _build_email_body(employee_name, leave_start, leave_end, leave_type, tasks):
    app_name = _get_app_name()
    rows_html = "".join(
        "<tr>"
        "<td style='padding:6px 12px;border-bottom:1px solid #eee;'>" + str(t.subject) + "</td>"
        "<td style='padding:6px 12px;border-bottom:1px solid #eee;'>" + (t.project or "(sans projet)") + "</td>"
        "<td style='padding:6px 12px;border-bottom:1px solid #eee;'>" + str(t.start_date or "—") + "</td>"
        "<td style='padding:6px 12px;border-bottom:1px solid #eee;'>" + str(t.end_date or "—") + "</td>"
        "</tr>"
        for t in tasks
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
        "</table><br>"
        "<p><strong>Tâches en conflit (" + str(len(tasks)) + ") :</strong></p>"
        "<table style='border-collapse:collapse;font-size:14px;width:100%;'>"
        "<tr style='background:#f5f5f5;'>"
        "<th style='padding:6px 12px;text-align:left;'>Tâche</th>"
        "<th style='padding:6px 12px;text-align:left;'>Projet</th>"
        "<th style='padding:6px 12px;text-align:left;'>Début prévu</th>"
        "<th style='padding:6px 12px;text-align:left;'>Fin prévue</th>"
        "</tr>" + rows_html + "</table><br>"
        "<p style='color:#888;font-size:12px;'>Ce message est généré automatiquement par "
        + app_name + " (B23). Il est informatif — aucune action automatique n'a été déclenchée.</p>"
    )


def _set_conflict_flag(task_name, value):
    """Positionne softia_conflit_absence sans mettre à jour modified."""
    frappe.db.set_value("Task", task_name, "softia_conflit_absence", value,
                        update_modified=False)


def _has_other_active_leave(user_email, task_start, task_end, exclude_la=None):
    sql = """
        SELECT la.name FROM `tabLeave Application` la
        INNER JOIN `tabEmployee` e ON e.name = la.employee
        WHERE e.user_id = %(user_email)s
          AND la.docstatus = 1
          AND la.from_date <= %(task_end)s
          AND la.to_date   >= %(task_start)s
    """
    p = {"user_email": user_email, "task_start": str(task_start), "task_end": str(task_end)}
    if exclude_la:
        sql += " AND la.name != %(exclude_la)s"
        p["exclude_la"] = exclude_la
    return bool(frappe.db.sql(sql, p))


def on_submit(doc, method=None):
    """B23 — Alerte email + B22 — Flag softia_conflit_absence=1 à la soumission."""
    if frappe.flags.in_import or frappe.flags.in_migrate or frappe.flags.in_test:
        return

    employee_id   = doc.employee
    employee_name = doc.employee_name or employee_id or "(sans nom)"
    leave_start   = getdate(doc.from_date)
    leave_end     = getdate(doc.to_date)
    leave_type    = getattr(doc, "leave_type", None)

    user_email = _get_user_email(employee_id)
    if not user_email:
        frappe.logger().warning("[B23/B22] Leave Application %s : employee sans user_id.", doc.name)
        return

    tasks = _find_conflicting_tasks(user_email, leave_start, leave_end)
    if not tasks:
        return

    for t in tasks:
        _set_conflict_flag(t.name, 1)

    recipients = set()
    manager_email = _get_manager_email(employee_id)
    if manager_email:
        recipients.add(manager_email)

    projects_seen = set()
    for t in tasks:
        if t.project and t.project not in projects_seen:
            projects_seen.add(t.project)
            owner_email = _get_project_owner_email(t.project)
            if owner_email:
                recipients.add(owner_email)

    if not recipients:
        return

    app_name = _get_app_name()
    subject = (
        f"[{app_name}] Conflit congé / tâches — "
        + employee_name
        + " (" + str(leave_start) + " → " + str(leave_end) + ")"
    )
    frappe.sendmail(
        recipients=list(recipients),
        subject=subject,
        message=_build_email_body(employee_name, leave_start, leave_end, leave_type, tasks),
        now=True,
    )


def on_cancel(doc, method=None):
    """B22 — Remet softia_conflit_absence=0 à l'annulation (si pas d'autre absence active)."""
    if frappe.flags.in_import or frappe.flags.in_migrate or frappe.flags.in_test:
        return

    employee_id = doc.employee
    leave_start = getdate(doc.from_date)
    leave_end   = getdate(doc.to_date)

    user_email = _get_user_email(employee_id)
    if not user_email:
        return

    tasks = _find_conflicting_tasks(user_email, leave_start, leave_end)
    if not tasks:
        return

    for t in tasks:
        if not _has_other_active_leave(user_email, t.start_date, t.end_date, exclude_la=doc.name):
            _set_conflict_flag(t.name, 0)
            frappe.logger().info("[B22] Task %s : softia_conflit_absence réinitialisé à 0.", t.name)
