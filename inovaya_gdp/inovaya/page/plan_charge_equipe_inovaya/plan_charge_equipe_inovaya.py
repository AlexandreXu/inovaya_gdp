"""
B25 — Page Plan de Charge Équipe InovaYa.

Méthode whitelisted appelée depuis le JS de la page.
Réutilise la logique de plan_de_charge_inovaya.py (B01).

Accès : Manager InovaYa, Responsable GdP, System Manager.
"""
import json
import frappe
from frappe.utils import getdate
from datetime import date, timedelta


# ── Helpers ───────────────────────────────────────────────────────────────────

def _week_label(week_start):
    """Ex : S23—2026"""
    iso = week_start.isocalendar()
    return f"S{iso[1]:02d}—{iso[0]}"


def _working_days(start, end):
    """Nombre de jours ouvrés (lun-ven) dans [start, end]."""
    count = 0
    d = start
    while d <= end:
        if d.weekday() < 5:
            count += 1
        d += timedelta(days=1)
    return count


def _daily_threshold():
    val = frappe.db.get_single_value("System Settings", "inovaya_daily_hours_threshold")
    try:
        return float(val) if val else 8.0
    except (TypeError, ValueError):
        return 8.0


# ── API whitelisted ───────────────────────────────────────────────────────────

@frappe.whitelist()
def get_charge_data(from_monday=None):
    """
    Retourne 4 semaines (S-1, S, S+1, S+2) de charge planifiée par collaborateur.

    Paramètre :
        from_monday (str, optionnel) : lundi de la semaine de référence (YYYY-MM-DD).
                     Défaut = lundi de la semaine courante.

    Retourne :
        {
          "weeks"     : [{"start","end","label"}, ...],   # 4 semaines
          "employees" : [
              {
                "email" : "...",
                "name"  : "Prénom Nom",
                "weeks" : {
                    "S22—2026": {"hours": 28.0, "pct": 80, "tasks": [
                        {"name":"TASK-001","subject":"...","project":"..."}
                    ]},
                    ...
                }
              }, ...
          ],
          "capacity"  : 40.0   # heures hebdo (threshold × 5)
        }
    """
    frappe.only_for(["Manager InovaYa", "Responsable GdP", "System Manager"])

    # Calculer le lundi de référence
    today = date.today()
    if from_monday:
        base = getdate(from_monday)
    else:
        base = today - timedelta(days=today.weekday())

    # Construire les 4 semaines
    weeks = []
    for offset in (-1, 0, 1, 2):
        ws = base + timedelta(weeks=offset)
        we = ws + timedelta(days=6)          # dimanche
        weeks.append({
            "start": str(ws),
            "end":   str(we),
            "label": _week_label(ws),
        })

    from_date = getdate(weeks[0]["start"])
    to_date   = getdate(weeks[-1]["end"])
    capacity  = _daily_threshold() * 5       # ex: 40h

    # ── Tâches actives dans la fenêtre 4 semaines ─────────────────────────────
    tasks = frappe.db.sql("""
        SELECT name, subject, project,
               DATE(exp_start_date) AS start_date,
               DATE(exp_end_date)   AS end_date,
               COALESCE(NULLIF(inovaya_hours_per_day, 0), 8.0) AS hours_per_day,
               _assign
        FROM `tabTask`
        WHERE is_template = 0
          AND exp_start_date IS NOT NULL
          AND exp_end_date   IS NOT NULL
          AND DATE(exp_end_date)   >= %(from_date)s
          AND DATE(exp_start_date) <= %(to_date)s
          AND _assign IS NOT NULL
          AND _assign NOT IN ('', '[]')
          AND status NOT IN ('Completed', 'Cancelled')
    """, {"from_date": str(from_date), "to_date": str(to_date)}, as_dict=True)

    # ── Calculer la charge par collaborateur × semaine ────────────────────────
    emp_week: dict = {}   # {email: {wlabel: {hours, tasks}}}
    name_cache: dict = {}

    for task in tasks:
        try:
            assignees = json.loads(task._assign or "[]")
        except (ValueError, TypeError):
            continue

        t_start = getdate(task.start_date)
        t_end   = getdate(task.end_date)

        for email in assignees:
            if email not in name_cache:
                name_cache[email] = (
                    frappe.db.get_value("User", email, "full_name") or email
                )

            for week in weeks:
                ws = getdate(week["start"])
                we = getdate(week["end"])
                overlap_start = max(t_start, ws)
                overlap_end   = min(t_end,   we)
                if overlap_start > overlap_end:
                    continue
                days = _working_days(overlap_start, overlap_end)
                if days == 0:
                    continue

                hours  = float(task.hours_per_day) * days
                wlabel = week["label"]

                bucket = (
                    emp_week
                    .setdefault(email, {})
                    .setdefault(wlabel, {"hours": 0.0, "tasks": []})
                )
                bucket["hours"] += hours
                bucket["tasks"].append({
                    "name":    task.name,
                    "subject": task.subject,
                    "project": task.project or "",
                })

    # ── Construire la réponse ─────────────────────────────────────────────────
    employees = []
    for email in sorted(emp_week.keys(),
                        key=lambda e: name_cache.get(e, e).lower()):
        weeks_data = {}
        for week in weeks:
            wlabel = week["label"]
            wd     = emp_week[email].get(wlabel, {"hours": 0.0, "tasks": []})
            pct    = round(wd["hours"] / capacity * 100) if capacity > 0 else 0
            weeks_data[wlabel] = {
                "hours": round(wd["hours"], 1),
                "pct":   pct,
                "tasks": wd["tasks"],
            }
        employees.append({
            "email": email,
            "name":  name_cache.get(email, email),
            "weeks": weeks_data,
        })

    return {
        "weeks":     weeks,
        "employees": employees,
        "capacity":  capacity,
    }
