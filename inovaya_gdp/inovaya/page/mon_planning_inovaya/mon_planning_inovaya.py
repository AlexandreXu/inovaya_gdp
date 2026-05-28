"""
B24 — Vue Collaborateur InovaYa : Mon Planning.

Méthode whitelisted get_my_tasks() :
  - Tâches projet assignées au user connecté (_assign JSON contains email)
  - Annexes Tasks (assigned_to = user email)
  - Pour chaque tâche : heures allouées + réalisées + flags retard / conflit absence
  - Méthode update_task_status() : mise à jour inline du statut

Accès : tout utilisateur connecté (voit uniquement ses propres tâches).
"""
import frappe
from frappe.utils import getdate, today
from datetime import timedelta


# ── Helpers ───────────────────────────────────────────────────────────────────

def _working_days(start_date, end_date):
    """Nombre de jours ouvrés entre deux dates (inclusif)."""
    count = 0
    d = start_date
    while d <= end_date:
        if d.weekday() < 5:
            count += 1
        d += timedelta(days=1)
    return count


def _actual_hours(task_name, user_email):
    """Heures soumises (Timesheets docstatus=1) pour cette tâche et cet utilisateur."""
    rows = frappe.db.sql("""
        SELECT COALESCE(SUM(tsd.hours), 0) AS h
        FROM `tabTimesheet Detail` tsd
        JOIN `tabTimesheet` ts ON ts.name = tsd.parent
        JOIN `tabEmployee` e   ON e.name  = ts.employee
        WHERE tsd.task    = %s
          AND ts.docstatus = 1
          AND e.user_id    = %s
    """, (task_name, user_email), as_dict=True)
    return round(float(rows[0].h) if rows else 0.0, 1)


def _allocated_hours(task):
    """Heures allouées = hours_per_day × jours ouvrés de la tâche."""
    if not task.get("exp_start_date") or not task.get("exp_end_date"):
        return 0.0
    s = getdate(task["exp_start_date"])
    e = getdate(task["exp_end_date"])
    if s > e:
        return 0.0
    days = _working_days(s, e)
    return round(float(task.get("inovaya_hours_per_day") or 8.0) * days, 1)


# ── API whitelisted ───────────────────────────────────────────────────────────

@frappe.whitelist()
def get_my_tasks():
    """
    Retourne les tâches du collaborateur connecté.

    Retourne :
        {
          "tasks": [
              {
                "name", "subject", "project", "status",
                "eisenhower": str,
                "allocated_hours": float,
                "actual_hours": float,
                "exp_end_date": str,
                "is_late": bool,
                "conflit_absence": bool,
              }, ...
          ],
          "annexe_tasks": [
              {"name","subject","status","exp_end_date","is_late"}, ...
          ],
          "statuses": [...]   // liste des statuts Task disponibles
        }
    """
    user_email = frappe.session.user
    today_date = getdate(today())

    # ── Tâches projet ─────────────────────────────────────────────────────────
    # _assign est un JSON array stocké en TEXT — on filtre avec LIKE
    # (même technique que le rapport plan_de_charge)
    tasks_raw = frappe.db.sql("""
        SELECT name, subject, project, status,
               inovaya_eisenhower_info,
               inovaya_hours_per_day,
               inovaya_conflit_absence,
               DATE(exp_start_date) AS exp_start_date,
               DATE(exp_end_date)   AS exp_end_date
        FROM `tabTask`
        WHERE is_template = 0
          AND status NOT IN ('Completed', 'Cancelled')
          AND _assign LIKE %(pattern)s
        ORDER BY exp_end_date ASC, name ASC
    """, {"pattern": f"%{user_email}%"}, as_dict=True)

    tasks = []
    for t in tasks_raw:
        t.exp_start_date = str(t.exp_start_date) if t.exp_start_date else None
        t.exp_end_date   = str(t.exp_end_date)   if t.exp_end_date   else None
        t.allocated_hours = _allocated_hours(t)
        t.actual_hours    = _actual_hours(t.name, user_email)
        t.is_late         = bool(
            t.exp_end_date and getdate(t.exp_end_date) < today_date
        )
        t.conflit_absence = bool(t.inovaya_conflit_absence)
        t.eisenhower      = t.inovaya_eisenhower_info or ""
        tasks.append({
            "name":            t.name,
            "subject":         t.subject or "",
            "project":         t.project or "",
            "status":          t.status or "",
            "eisenhower":      t.eisenhower,
            "allocated_hours": t.allocated_hours,
            "actual_hours":    t.actual_hours,
            "exp_end_date":    t.exp_end_date,
            "is_late":         t.is_late,
            "conflit_absence": t.conflit_absence,
        })

    # ── Annexes Tasks ─────────────────────────────────────────────────────────
    annexe_raw = frappe.db.sql("""
        SELECT name, subject, status,
               DATE(exp_end_date) AS exp_end_date
        FROM `tabAnnexe Task`
        WHERE assigned_to = %(user)s
          AND status NOT IN ('Completed', 'Cancelled')
        ORDER BY exp_end_date ASC, name ASC
    """, {"user": user_email}, as_dict=True)

    annexe_tasks = []
    for at in annexe_raw:
        at.exp_end_date = str(at.exp_end_date) if at.exp_end_date else None
        annexe_tasks.append({
            "name":        at.name,
            "subject":     at.subject or "",
            "status":      at.status or "",
            "exp_end_date": at.exp_end_date,
            "is_late":     bool(
                at.exp_end_date and getdate(at.exp_end_date) < today_date
            ),
        })

    # Statuts disponibles pour Task (Select field)
    statuses = ["Open", "Working", "Pending Review", "Overdue", "Template",
                "Completed", "Cancelled"]

    return {
        "tasks":        tasks,
        "annexe_tasks": annexe_tasks,
        "statuses":     statuses,
    }


@frappe.whitelist()
def update_task_status(task_name, new_status):
    """
    Met à jour le statut d'une tâche.
    Vérifie que l'utilisateur connecté est bien assigné à la tâche.
    """
    user_email = frappe.session.user

    # Vérification sécurité : la tâche doit appartenir au user
    assign_raw = frappe.db.get_value("Task", task_name, "_assign") or "[]"
    import json
    try:
        assignees = json.loads(assign_raw)
    except (ValueError, TypeError):
        assignees = []

    if user_email not in assignees and not frappe.has_role("System Manager"):
        frappe.throw("Vous n'êtes pas assigné à cette tâche.", frappe.PermissionError)

    allowed = ["Open", "Working", "Pending Review", "Overdue", "Completed", "Cancelled"]
    if new_status not in allowed:
        frappe.throw(f"Statut invalide : {new_status}")

    frappe.db.set_value("Task", task_name, "status", new_status)
    frappe.db.commit()
    return {"ok": True, "status": new_status}
