"""
B08 — Heures par Verticale Métier InovaYa
Rapport Script Report "Heures par Verticale InovaYa"

Colonnes  : Collaborateur | Verticale Métier | Heures réalisées
Groupement: par collaborateur puis par verticale

Source :
  tabTimesheet Detail (td) — heures réelles (parent docstatus=1)
  JOIN tabTimesheet (ts)   — pour employee_name
  LEFT JOIN tabTask (t)    — pour inovaya_task_vertical
  Filtre période : td.from_time entre from_date et to_date (inclus)

Filtres optionnels : employee, verticale.
Lignes sans tâche ou sans verticale renseignée → verticale = "(non renseignée)".
"""
import frappe
from frappe import _
from frappe.utils import getdate, add_days


# ── Entrée principale ─────────────────────────────────────────────────────────

def execute(filters=None):
    _validate(filters)
    columns = get_columns()
    data = get_data(filters)
    return columns, data


# ── Validation ────────────────────────────────────────────────────────────────

def _validate(filters):
    if not filters or not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Les dates De et À sont obligatoires."))
    if getdate(filters["from_date"]) > getdate(filters["to_date"]):
        frappe.throw(_("La date de début doit être antérieure à la date de fin."))


# ── Colonnes ──────────────────────────────────────────────────────────────────

def get_columns():
    return [
        {
            "fieldname": "employee_name",
            "label": _("Collaborateur"),
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "fieldname": "verticale",
            "label": _("Verticale Métier"),
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "fieldname": "heures_realisees",
            "label": _("Heures réalisées"),
            "fieldtype": "Float",
            "width": 160,
        },
        {
            "fieldname": "nb_saisies",
            "label": _("Nb saisies"),
            "fieldtype": "Int",
            "width": 110,
        },
    ]


# ── Données ───────────────────────────────────────────────────────────────────

def get_data(filters):
    from_date = str(getdate(filters["from_date"]))
    # to_date inclus : on prend jusqu'à minuit du lendemain
    to_date_excl = str(add_days(getdate(filters["to_date"]), 1))

    params = {
        "from_date": from_date,
        "to_date_excl": to_date_excl,
    }

    # Clause optionnelle employee
    emp_clause = ""
    if filters.get("employee"):
        emp_clause = "AND ts.employee = %(employee)s"
        params["employee"] = filters["employee"]

    # Clause optionnelle verticale
    vert_clause = ""
    if filters.get("verticale"):
        # "Non renseignée" → filtre sur NULL/vide
        if filters["verticale"] in ("(non renseignée)", ""):
            vert_clause = "AND (t.inovaya_task_vertical IS NULL OR t.inovaya_task_vertical = '')"
        else:
            vert_clause = "AND t.inovaya_task_vertical = %(verticale)s"
            params["verticale"] = filters["verticale"]

    rows = frappe.db.sql(
        f"""
        SELECT
            ts.employee_name                                    AS employee_name,
            COALESCE(
                NULLIF(t.inovaya_task_vertical, ''),
                '(non renseignée)'
            )                                                   AS verticale,
            ROUND(SUM(td.hours), 2)                             AS heures_realisees,
            COUNT(td.name)                                      AS nb_saisies
        FROM `tabTimesheet Detail` td
        INNER JOIN `tabTimesheet` ts
            ON ts.name = td.parent
            AND ts.docstatus = 1
        LEFT JOIN `tabTask` t
            ON t.name = td.task
        WHERE td.from_time >= %(from_date)s
          AND td.from_time  < %(to_date_excl)s
          {emp_clause}
          {vert_clause}
        GROUP BY ts.employee, ts.employee_name,
                 COALESCE(NULLIF(t.inovaya_task_vertical, ''), '(non renseignée)')
        ORDER BY ts.employee_name,
                 COALESCE(NULLIF(t.inovaya_task_vertical, ''), '(non renseignée)')
        """,
        params,
        as_dict=True,
    )

    return rows
