"""
B01 — Plan de charge manager.
Rapport Script Report "Plan de Charge"

Colonnes  : Collaborateur | Semaine | H. planifiées | H. réalisées | Charge % | Projets concernés
Source planifiées : tabTask._assign + softia_hours_per_day × jours ouvrés ∩ semaine
Source réalisées  : tabTimesheet (docstatus=1) + tabTimesheet Detail
Capacité hebdo    : softia_daily_hours_threshold × 5 jours ouvrés
"""
import json
import frappe
from frappe import _
from frappe.utils import getdate
from datetime import timedelta


def execute(filters=None):
    _validate(filters)
    return get_columns(), get_data(filters)


def _validate(filters):
    if not filters or not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Les dates De et À sont obligatoires."))
    if getdate(filters["from_date"]) > getdate(filters["to_date"]):
        frappe.throw(_("La date de début doit être antérieure à la date de fin."))


def get_columns():
    return [
        {"fieldname": "user_full_name", "label": _("Collaborateur"), "fieldtype": "Data",    "width": 200},
        {"fieldname": "week_label",     "label": _("Semaine"),        "fieldtype": "Data",    "width": 110},
        {"fieldname": "planned_hours",  "label": _("H. planifiées"),  "fieldtype": "Float",   "width": 130, "precision": 1},
        {"fieldname": "actual_hours",   "label": _("H. réalisées"),   "fieldtype": "Float",   "width": 130, "precision": 1},
        {"fieldname": "charge_pct",     "label": _("Charge %"),       "fieldtype": "Percent", "width": 100},
        {"fieldname": "projects",       "label": _("Projets concernés"), "fieldtype": "Data", "width": 350},
    ]


def _get_weeks(from_date, to_date):
    start = getdate(from_date)
    start -= timedelta(days=start.weekday())
    end = getdate(to_date)
    weeks = []
    while start <= end:
        week_end = start + timedelta(days=6)
        weeks.append((start, min(week_end, end)))
        start += timedelta(days=7)
    return weeks


def _week_label(week_start):
    iso = week_start.isocalendar()
    return f"S{iso[1]:02d} — {iso[0]}"


def _working_days_in_overlap(task_start, task_end, week_start, week_end):
    overlap_start = max(task_start, week_start)
    overlap_end   = min(task_end,   week_end)
    if overlap_start > overlap_end:
        return 0
    count = 0
    d = overlap_start
    while d <= overlap_end:
        if d.weekday() < 5:
            count += 1
        d += timedelta(days=1)
    return count


def _daily_threshold():
    val = frappe.db.get_single_value("System Settings", "softia_daily_hours_threshold")
    try:
        return float(val) if val else 8.0
    except (TypeError, ValueError):
        return 8.0


def _sort_key_week(week_label):
    try:
        parts = week_label.replace("S", "").split("—")
        return (int(parts[1].strip()), int(parts[0].strip()))
    except (IndexError, ValueError):
        return (0, 0)


def get_data(filters):
    from_date   = getdate(filters["from_date"])
    to_date     = getdate(filters["to_date"])
    user_filter = filters.get("employee")

    threshold_daily = _daily_threshold()
    weekly_capacity = threshold_daily * 5
    weeks = _get_weeks(from_date, to_date)

    tasks = frappe.db.sql("""
        SELECT name, subject, project,
               DATE(exp_start_date) AS start_date,
               DATE(exp_end_date)   AS end_date,
               COALESCE(NULLIF(softia_hours_per_day, 0), 8.0) AS hours_per_day,
               _assign
        FROM `tabTask`
        WHERE is_template = 0
          AND exp_start_date IS NOT NULL AND exp_end_date IS NOT NULL
          AND DATE(exp_end_date)   >= %(from_date)s
          AND DATE(exp_start_date) <= %(to_date)s
          AND _assign IS NOT NULL AND _assign NOT IN ('', '[]')
    """, {"from_date": str(from_date), "to_date": str(to_date)}, as_dict=True)

    user_clause = "AND e.user_id = %(user)s" if user_filter else ""
    ts_rows = frappe.db.sql(f"""
        SELECT e.user_id AS user_email, DATE(tsd.from_time) AS work_date, SUM(tsd.hours) AS hours
        FROM `tabTimesheet Detail` tsd
        JOIN `tabTimesheet` ts ON ts.name = tsd.parent
        JOIN `tabEmployee`  e  ON e.name  = ts.employee
        WHERE ts.docstatus = 1 AND e.user_id IS NOT NULL
          AND DATE(tsd.from_time) BETWEEN %(from_date)s AND %(to_date)s
          {user_clause}
        GROUP BY e.user_id, DATE(tsd.from_time)
    """, {
        "from_date": str(from_date), "to_date": str(to_date),
        **({"user": user_filter} if user_filter else {}),
    }, as_dict=True)

    actual_by_user_week = {}
    for row in ts_rows:
        d = getdate(row.work_date)
        wstart = d - timedelta(days=d.weekday())
        wlabel = _week_label(wstart)
        actual_by_user_week.setdefault(row.user_email, {}).setdefault(wlabel, 0.0)
        actual_by_user_week[row.user_email][wlabel] += float(row.hours or 0)

    planned_by_user_week = {}
    full_name_cache = {}

    for task in tasks:
        try:
            assignees = json.loads(task._assign or "[]")
        except (ValueError, TypeError):
            continue
        t_start = getdate(task.start_date)
        t_end   = getdate(task.end_date)
        for user_email in assignees:
            if user_filter and user_email != user_filter:
                continue
            if user_email not in full_name_cache:
                full_name_cache[user_email] = (
                    frappe.db.get_value("User", user_email, "full_name") or user_email
                )
            for (ws, we) in weeks:
                wd = _working_days_in_overlap(t_start, t_end, ws, we)
                if wd == 0:
                    continue
                planned_h = float(task.hours_per_day) * wd
                wlabel    = _week_label(ws)
                bucket = planned_by_user_week.setdefault(user_email, {}).setdefault(
                    wlabel, {"hours": 0.0, "projects": set()})
                bucket["hours"] += planned_h
                if task.project:
                    bucket["projects"].add(task.project)

    all_users = set(planned_by_user_week.keys()) | set(actual_by_user_week.keys())
    for u in all_users:
        if u not in full_name_cache:
            full_name_cache[u] = frappe.db.get_value("User", u, "full_name") or u

    rows = []
    for user_email in sorted(all_users, key=lambda u: full_name_cache.get(u, u).lower()):
        user_planned = planned_by_user_week.get(user_email, {})
        user_actual  = actual_by_user_week.get(user_email, {})
        for wlabel in sorted(set(user_planned.keys()) | set(user_actual.keys()),
                             key=_sort_key_week):
            planned_data = user_planned.get(wlabel, {"hours": 0.0, "projects": set()})
            planned_h    = planned_data["hours"]
            actual_h     = user_actual.get(wlabel, 0.0)
            charge_pct   = round(planned_h / weekly_capacity * 100, 1) if weekly_capacity > 0 else 0.0
            rows.append({
                "user_full_name": full_name_cache.get(user_email, user_email),
                "week_label":     wlabel,
                "planned_hours":  round(planned_h, 1),
                "actual_hours":   round(actual_h, 1),
                "charge_pct":     charge_pct,
                "projects":       ", ".join(sorted(planned_data["projects"])) if planned_data["projects"] else "—",
            })
    return rows
