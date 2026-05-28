"""
B04 — Priorisation automatique Eisenhower (Task + Annexe Task).
B05 — Détection automatique des conflits de planning (blocage dur).
B06 — Alimentation automatique de Timesheet draft lors d'une assignation Task.

Différences vs inovaya_gdp/overrides/task.py :
  - Champs : inovaya_* → softia_* (softia_importance, softia_eisenhower_info,
             softia_hours_per_day)
  - URGENCY_DAYS = 7 (constante) → _get_urgency_days() lit System Settings softia_urgency_days
  - ALLOWED_ROLES_IMPORTANCE (frozenset hardcodé) → _get_importance_roles()
    lit System Settings softia_importance_roles (JSON list, vide = pas de restriction)
"""
import json
import frappe
from frappe import _


def _get_urgency_days():
    """Lit softia_urgency_days depuis System Settings (défaut 7)."""
    val = frappe.db.get_single_value("System Settings", "softia_urgency_days")
    try:
        return int(val) if val else 7
    except (TypeError, ValueError):
        return 7


def _get_importance_roles():
    """
    Retourne un frozenset des rôles autorisés à modifier softia_importance.
    Vide → pas de restriction (tout le monde peut modifier).
    """
    raw = frappe.db.get_single_value("System Settings", "softia_importance_roles")
    if not raw:
        return frozenset()
    try:
        return frozenset(json.loads(raw))
    except (ValueError, TypeError):
        return frozenset()


_MATRIX = {
    (True,  True):  ("Q1 — Critique (Faire en priorité)",      "Urgent"),
    (True,  False): ("Q2 — Important (Planifier)",              "High"),
    (False, True):  ("Q3 — Déléguer (Urgent, non important)",  "Medium"),
    (False, False): ("Q4 — Reporter / Éliminer",                "Low"),
}


def _get_end_date(doc):
    val = doc.get("exp_end_date")
    return frappe.utils.getdate(val) if val else None


def _is_urgent(end_date):
    if not end_date:
        return False
    urgency_days = _get_urgency_days()
    today = frappe.utils.getdate(frappe.utils.today())
    return (end_date - today).days <= urgency_days


def _guard_importance_change(doc):
    new_val = doc.get("softia_importance") or ""
    if not new_val or new_val == "Basse":
        return
    doc_before = doc.get_doc_before_save()
    old_val = (doc_before.get("softia_importance") if doc_before else None) or ""
    if old_val == new_val:
        return
    allowed_roles = _get_importance_roles()
    if not allowed_roles:
        return
    user_roles = frozenset(frappe.get_roles(frappe.session.user))
    if allowed_roles & user_roles:
        return
    if doc_before:
        frappe.throw(
            _(
                "La modification de l'Importance (matrice Eisenhower) est réservée "
                "aux rôles configurés dans System Settings (softia_importance_roles)."
            ),
            title=_("Permission insuffisante — B04"),
        )
    else:
        doc.softia_importance = "Basse"


def _run_eisenhower(doc):
    if doc.get("is_template"):
        return
    if doc.doctype == "Task":
        _guard_importance_change(doc)
    importance_haute = doc.get("softia_importance") == "Haute"
    end_date = _get_end_date(doc)
    urgent   = _is_urgent(end_date)
    quadrant_label, priority = _MATRIX[(importance_haute, urgent)]
    doc.softia_eisenhower_info = f"{'Urgente' if urgent else 'Non urgente'} · {quadrant_label}"
    if doc.get("softia_importance"):
        doc.priority = priority


def _get_daily_hours(doc):
    val = doc.get("softia_hours_per_day")
    try:
        v = float(val)
        return v if v > 0 else 8.0
    except (TypeError, ValueError):
        return 8.0


def _get_daily_threshold():
    val = frappe.db.get_single_value("System Settings", "softia_daily_hours_threshold")
    try:
        return float(val) if val else 8.0
    except (TypeError, ValueError):
        return 8.0


def _get_assigned_users(doc):
    if doc.doctype == "Annexe Task":
        return [doc.assigned_to] if doc.assigned_to else []
    assign_val = doc.get("_assign")
    if not assign_val and doc.name:
        try:
            assign_val = frappe.db.get_value("Task", doc.name, "_assign")
        except Exception:
            pass
    try:
        return json.loads(assign_val or "[]")
    except (ValueError, TypeError):
        return []


def _get_doc_date_range(doc):
    start = doc.get("exp_start_date")
    end   = doc.get("exp_end_date")
    if not start or not end:
        return None, None
    return str(frappe.utils.getdate(start)), str(frappe.utils.getdate(end))


def _find_conflicts_for_user(doc, user_name, start_str, end_str, doc_hours, threshold):
    exclude = doc.name or ""
    results = []
    for row in frappe.db.sql(
        """
        SELECT subject, project,
               DATE(exp_start_date) AS start_date,
               DATE(exp_end_date)   AS end_date,
               COALESCE(NULLIF(softia_hours_per_day, 0), 8.0) AS hours_per_day
        FROM `tabTask`
        WHERE name != %(exclude)s AND is_template = 0
          AND _assign LIKE %(pattern)s
          AND DATE(exp_end_date) >= %(start)s AND DATE(exp_start_date) <= %(end)s
        LIMIT 10
        """,
        {"exclude": exclude, "pattern": f'%"{user_name}"%', "start": start_str, "end": end_str},
        as_dict=True,
    ):
        if doc_hours + row["hours_per_day"] > threshold:
            row["source_doctype"] = "Task"
            row["total_hours"] = doc_hours + row["hours_per_day"]
            results.append(row)
    for row in frappe.db.sql(
        """
        SELECT subject, '' AS project,
               exp_start_date AS start_date, exp_end_date AS end_date,
               COALESCE(NULLIF(softia_hours_per_day, 0), 8.0) AS hours_per_day
        FROM `tabAnnexe Task`
        WHERE name != %(exclude)s AND assigned_to = %(user)s
          AND exp_start_date IS NOT NULL
          AND exp_end_date >= %(start)s AND exp_start_date <= %(end)s
        LIMIT 10
        """,
        {"exclude": exclude, "user": user_name, "start": start_str, "end": end_str},
        as_dict=True,
    ):
        if doc_hours + row["hours_per_day"] > threshold:
            row["source_doctype"] = "Annexe Task"
            row["total_hours"] = doc_hours + row["hours_per_day"]
            results.append(row)
    return results


def _fmt_date(val):
    try:
        d = frappe.utils.getdate(val)
        return f"{d.day:02d}/{d.month:02d}"
    except Exception:
        return str(val)


def _check_planning_conflicts(doc):
    if frappe.flags.in_import or frappe.flags.in_migrate or frappe.flags.in_test:
        return
    if doc.get("is_template"):
        return
    users = _get_assigned_users(doc)
    if not users:
        return
    start_str, end_str = _get_doc_date_range(doc)
    if not start_str or not end_str:
        return
    doc_hours = _get_daily_hours(doc)
    threshold = _get_daily_threshold()
    conflict_lines = []
    for user_name in users:
        full_name = frappe.db.get_value("User", user_name, "full_name") or user_name
        for c in _find_conflicts_for_user(doc, user_name, start_str, end_str, doc_hours, threshold):
            d_from = _fmt_date(c["start_date"])
            d_to   = _fmt_date(c["end_date"])
            ref = (
                f"« {c['subject']} » (Tâche Annexe)" if c["source_doctype"] == "Annexe Task"
                else f"« {c['subject']} » ({c['project']})" if c["project"]
                else f"« {c['subject']} » (tâche sans projet)"
            )
            conflict_lines.append(
                f"• {full_name} : {doc_hours}h (cette tâche)"
                f" + {c['hours_per_day']}h {ref}"
                f" = {c['total_hours']}h/j > {threshold}h"
                f" — du {d_from} au {d_to}."
            )
    if conflict_lines:
        frappe.throw(
            _("Dépassement de charge journalière détecté :") + "<br>" + "<br>".join(conflict_lines),
            title=_("Conflit de planning — B05"),
        )


def _compute_new_assignees(doc):
    doc._b06_new_users = []
    if frappe.flags.in_import or frappe.flags.in_migrate or frappe.flags.in_test:
        return
    if doc.get("is_template"):
        return
    if not doc.get("exp_start_date") or not doc.get("exp_end_date"):
        return
    new_assign_raw = doc.get("_assign")
    if not new_assign_raw:
        return
    try:
        new_users = set(json.loads(new_assign_raw))
    except (ValueError, TypeError):
        return
    if not new_users:
        return
    old_raw = (frappe.db.get_value("Task", doc.name, "_assign") or "[]") \
              if (doc.name and not doc.is_new()) else "[]"
    try:
        old_users = set(json.loads(old_raw))
    except (ValueError, TypeError):
        old_users = set()
    doc._b06_new_users = list(new_users - old_users)


def _create_draft_timesheets_b06(doc, new_users):
    company = frappe.db.get_default("Company") or frappe.db.get_value("Company", {}, "name")
    hours = float(doc.get("expected_time") or 0) or _get_daily_hours(doc)
    from datetime import timedelta as _td
    start_date = frappe.utils.getdate(doc.exp_start_date)
    start_dt   = f"{start_date} 09:00:00"
    end_dt     = str(frappe.utils.get_datetime(start_dt) + _td(hours=hours))
    for user_email in new_users:
        emp_id = frappe.db.get_value("Employee", {"user_id": user_email}, "name")
        if not emp_id:
            frappe.logger().warning("[B06] Aucun Employee pour '%s'.", user_email)
            continue
        already = frappe.db.sql(
            "SELECT td.parent FROM `tabTimesheet Detail` td "
            "INNER JOIN `tabTimesheet` ts ON ts.name=td.parent "
            "WHERE td.task=%s AND ts.employee=%s AND ts.docstatus=0 LIMIT 1",
            (doc.name, emp_id),
        )
        if already:
            continue
        emp_name = frappe.db.get_value("Employee", emp_id, "employee_name") or user_email
        try:
            ts_name = frappe.generate_hash(length=10)
            now_str = str(frappe.utils.now_datetime())
            user    = frappe.session.user or "Administrator"
            frappe.db.sql(
                "INSERT INTO `tabTimesheet` "
                "(name,creation,modified,modified_by,owner,docstatus,"
                " employee,employee_name,company,parent_project,total_hours) "
                "VALUES (%s,%s,%s,%s,%s,0,%s,%s,%s,%s,%s)",
                (ts_name, now_str, now_str, user, user,
                 emp_id, emp_name, company, doc.project or None, hours),
            )
            td_name = frappe.generate_hash(length=10)
            frappe.db.sql(
                "INSERT INTO `tabTimesheet Detail` "
                "(name,creation,modified,modified_by,owner,docstatus,"
                " parent,parentfield,parenttype,"
                " task,project,from_time,to_time,"
                " hours,expected_hours,is_billable,completed,description,idx) "
                "VALUES (%s,%s,%s,%s,%s,0,"
                "        %s,'time_logs','Timesheet',"
                "        %s,%s,%s,%s,"
                "        %s,%s,0,0,%s,1)",
                (td_name, now_str, now_str, user, user,
                 ts_name, doc.name, doc.project or None, start_dt, end_dt,
                 hours, hours, f"[B06] Planification auto — {doc.subject}"),
            )
            frappe.db.commit()
            frappe.logger().info("[B06] Timesheet %s créée : employee=%s task=%s.",
                                 ts_name, emp_name, doc.name)
            frappe.msgprint(
                f"[B06] Timesheet draft créée pour {emp_name} — « {doc.subject} ».",
                indicator="green", alert=True,
            )
        except Exception as exc:
            frappe.logger().error("[B06] Erreur Timesheet employee=%s task=%s : %s",
                                  emp_id, doc.name, str(exc))


def after_save(doc, method=None):
    if doc.doctype != "Task":
        return
    new_users = getattr(doc, "_b06_new_users", [])
    if not new_users:
        return
    _create_draft_timesheets_b06(doc, new_users)


def before_save(doc, method=None):
    _run_eisenhower(doc)
    _check_planning_conflicts(doc)
    if doc.doctype == "Task":
        _compute_new_assignees(doc)
