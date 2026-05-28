"""
B03 — Tableau de bord collaborateur avancé
Rapport Script Report "Tableau de Bord Collaborateur"

Colonnes (ordre CDC page 4) :
  Projet | Tâche | Statut | Priorité Eisenhower | Temps alloué
  | Temps réalisé | Échéance | Retard

Sources :
  [1] tabTask WHERE _assign LIKE '%"email"%' AND is_template=0
      JOIN tabProject pour afficher project_name (pas PROJ-xxxx)
  [2] tabAnnexe Task WHERE assigned_to = email (B02 — hors projet)
  [3] tabTimesheet Detail (docstatus=1) agrégé par task — uniquement pour [1]

Tri : retard d'abord (is_late DESC), puis exp_end_date ASC.
Formatage JS : ligne rouge si retard, gras si Q1, orange si réalisé > alloué.

Note POC B03 :
  - Heures réalisées = 0 pour les Annexe Tasks (pas de lien Timesheet natif).
  - _assign est un JSON Frappe (ex: '["alice@x.com"]') — LIKE '%" email"%' est
    identique à l'approche B05 ; limitation : email partiel pourrait matcher
    (peu probable sur des emails réels). À passer en JSON_CONTAINS en Phase 3
    si MariaDB >= 10.2 (JSON_CONTAINS disponible).
"""
import frappe
from frappe import _
from frappe.utils import getdate, today
from datetime import timedelta


# ── Entrée principale ─────────────────────────────────────────────────────────

def execute(filters=None):
    _validate(filters)
    return get_columns(), get_data(filters)


# ── Validation ────────────────────────────────────────────────────────────────

def _validate(filters):
    if not filters or not filters.get("employee"):
        frappe.throw(_("Le collaborateur est obligatoire."))
    if (filters.get("from_date") and filters.get("to_date")
            and getdate(filters["from_date"]) > getdate(filters["to_date"])):
        frappe.throw(_("La date de début doit être antérieure à la date de fin."))


# ── Colonnes ──────────────────────────────────────────────────────────────────

def get_columns():
    return [
        {
            "fieldname": "project",
            "label":     _("Projet"),
            "fieldtype": "Data",
            "width":     160,
        },
        {
            "fieldname": "task_subject",
            "label":     _("Tâche"),
            "fieldtype": "Data",
            "width":     270,
        },
        {
            "fieldname": "status",
            "label":     _("Statut"),
            "fieldtype": "Data",
            "width":     120,
        },
        {
            "fieldname": "eisenhower",
            "label":     _("Priorité Eisenhower"),
            "fieldtype": "Data",
            "width":     230,
        },
        {
            "fieldname": "allocated_hours",
            "label":     _("Temps alloué (h)"),
            "fieldtype": "Float",
            "width":     130,
            "precision": 1,
        },
        {
            "fieldname": "actual_hours",
            "label":     _("Temps réalisé (h)"),
            "fieldtype": "Float",
            "width":     140,
            "precision": 1,
        },
        {
            "fieldname": "exp_end_date",
            "label":     _("Échéance"),
            "fieldtype": "Date",
            "width":     110,
        },
        {
            "fieldname": "is_late",
            "label":     _("Retard"),
            "fieldtype": "Data",        # rendu personnalisé dans le JS
            "width":     100,
        },
    ]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _working_days(start, end):
    """Nombre de jours ouvrés lun-ven entre start et end (inclus)."""
    if not start or not end or start > end:
        return 0
    count = 0
    d = start
    while d <= end:
        if d.weekday() < 5:    # lun=0 … ven=4
            count += 1
        d += timedelta(days=1)
    return count


def _build_date_conditions(from_date, to_date, date_prefix=""):
    """
    Retourne (clauses, params) pour filtrer par période.
    Une tâche est incluse si son échéance >= from_date
    ET son début <= to_date (si les dates sont renseignées).
    """
    clauses = []
    params  = {}
    if from_date:
        clauses.append(
            f"({date_prefix}exp_end_date IS NULL "
            f"OR {date_prefix}exp_end_date >= %(from_date)s)"
        )
        params["from_date"] = str(from_date)
    if to_date:
        clauses.append(
            f"({date_prefix}exp_start_date IS NULL "
            f"OR {date_prefix}exp_start_date <= %(to_date)s)"
        )
        params["to_date"] = str(to_date)
    return clauses, params


# ── Données ───────────────────────────────────────────────────────────────────

def get_data(filters):
    user_email    = filters["employee"]
    from_date     = getdate(filters["from_date"]) if filters.get("from_date") else None
    to_date       = getdate(filters["to_date"])   if filters.get("to_date")   else None
    status_filter = filters.get("status")
    today_d       = getdate(today())

    # ── [1] Tasks assignées au collaborateur ──────────────────────────────────
    task_conds  = [
        "t.is_template = 0",
        "t._assign LIKE %(pattern)s",
    ]
    task_params = {"pattern": f'%"{user_email}"%'}

    task_date_conds = []
    if from_date:
        task_date_conds.append(
            "(t.exp_end_date IS NULL OR DATE(t.exp_end_date) >= %(from_date)s)"
        )
        task_params["from_date"] = str(from_date)
    if to_date:
        task_date_conds.append(
            "(t.exp_start_date IS NULL OR DATE(t.exp_start_date) <= %(to_date)s)"
        )
        task_params["to_date"] = str(to_date)
    task_conds.extend(task_date_conds)

    if status_filter and status_filter != "All":
        task_conds.append("t.status = %(status)s")
        task_params["status"] = status_filter

    task_where = " AND ".join(task_conds)

    task_rows = frappe.db.sql(f"""
        SELECT
            t.name                                              AS task_name,
            t.subject,
            COALESCE(p.project_name, t.project, '')             AS project,
            t.status,
            COALESCE(t.softia_eisenhower_info, '')              AS eisenhower,
            COALESCE(NULLIF(t.softia_hours_per_day, 0), 8.0)   AS hours_per_day,
            DATE(t.exp_start_date)                              AS exp_start_date,
            DATE(t.exp_end_date)                                AS exp_end_date,
            'Task'                                              AS source
        FROM `tabTask` t
        LEFT JOIN `tabProject` p ON p.name = t.project
        WHERE {task_where}
    """, task_params, as_dict=True)

    # ── [2] Annexe Tasks assignées au collaborateur ───────────────────────────
    annexe_conds  = ["assigned_to = %(user)s"]
    annexe_params = {"user": user_email}

    if from_date:
        annexe_conds.append(
            "(exp_end_date IS NULL OR exp_end_date >= %(from_date)s)"
        )
        annexe_params["from_date"] = str(from_date)
    if to_date:
        annexe_conds.append(
            "(exp_start_date IS NULL OR exp_start_date <= %(to_date)s)"
        )
        annexe_params["to_date"] = str(to_date)
    if status_filter and status_filter != "All":
        annexe_conds.append("status = %(status)s")
        annexe_params["status"] = status_filter

    annexe_where = " AND ".join(annexe_conds)

    annexe_rows = frappe.db.sql(f"""
        SELECT
            name                                             AS task_name,
            subject,
            ''                                               AS project,
            status,
            COALESCE(softia_eisenhower_info, '')             AS eisenhower,
            COALESCE(NULLIF(softia_hours_per_day, 0), 8.0)  AS hours_per_day,
            exp_start_date,
            exp_end_date,
            'Annexe Task'                                    AS source
        FROM `tabAnnexe Task`
        WHERE {annexe_where}
    """, annexe_params, as_dict=True)

    # ── [3] Heures réalisées depuis Timesheets soumises (Tasks uniquement) ────
    task_names = [r.task_name for r in task_rows if r.task_name]
    ts_by_task = {}
    if task_names:
        placeholders = ", ".join(["%s"] * len(task_names))
        ts_data = frappe.db.sql(
            f"""
            SELECT tsd.task, SUM(tsd.hours) AS hours
            FROM `tabTimesheet Detail` tsd
            JOIN `tabTimesheet` ts ON ts.name = tsd.parent
            WHERE ts.docstatus = 1
              AND tsd.task IN ({placeholders})
            GROUP BY tsd.task
            """,
            tuple(task_names),
            as_dict=True,
        )
        ts_by_task = {r.task: float(r.hours or 0) for r in ts_data}

    # ── [4] Construire les lignes ─────────────────────────────────────────────
    rows = []
    for r in list(task_rows) + list(annexe_rows):
        start = getdate(r.exp_start_date) if r.exp_start_date else None
        end   = getdate(r.exp_end_date)   if r.exp_end_date   else None

        allocated = round(
            float(r.hours_per_day) * _working_days(start, end), 1
        ) if start and end else 0.0

        actual = ts_by_task.get(r.task_name, 0.0) if r.source == "Task" else 0.0

        is_late = bool(
            end
            and end < today_d
            and r.status not in ("Completed", "Done")
        )

        rows.append({
            "project":         r.project or "",
            "task_subject":    r.subject or "",
            "status":          r.status  or "",
            "eisenhower":      r.eisenhower or "",
            "allocated_hours": allocated,
            "actual_hours":    round(actual, 1),
            "exp_end_date":    r.exp_end_date,
            "is_late":         1 if is_late else 0,
            "is_annexe":       1 if r.source == "Annexe Task" else 0,
        })

    # ── [5] Tri : retard d'abord, puis échéance ASC ───────────────────────────
    rows.sort(key=lambda r: (
        0 if r["is_late"] else 1,
        str(r["exp_end_date"] or "9999-12-31"),
    ))

    return rows
