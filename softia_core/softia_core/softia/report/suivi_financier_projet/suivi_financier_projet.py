"""
B16 — Vue financière prévu / engagé / réalisé par projet.
Rapport Script Report Frappe — colonnes :
  Catégorie | Prévu | Engagé | Réalisé | Écart Prévu-Réalisé | % Consommé

Sources :
  Prévu    → SUM(amount_planned)  tabBudget Detaille Projet  (B15)
  Engagé   → SUM(grand_total)     tabPurchase Order   status != Cancelled
  Réalisé  → SUM(grand_total)     tabPurchase Invoice docstatus = 1

Note POC : engagé et réalisé sont des totaux projet (PO/PI sans
ventilation par catégorie). Affinable en Phase 3 via B18 (jalons).
Limitation POC : champ project au niveau header PO — un PO multi-projets
ne serait pas ventilé correctement (voir BACKLOG B16).
"""
import frappe
from frappe import _


def execute(filters=None):
    _validate(filters)
    return get_columns(), get_data(filters)


# ── Validation ────────────────────────────────────────────────────────────────

def _validate(filters):
    if not filters or not filters.get("project"):
        frappe.throw(_("Le filtre Projet est obligatoire."))
    if not frappe.db.exists("Project", filters["project"]):
        frappe.throw(_("Projet introuvable : {0}").format(filters["project"]))


# ── Colonnes ──────────────────────────────────────────────────────────────────

def get_columns():
    return [
        {"fieldname": "category",       "label": _("Catégorie"),               "fieldtype": "Data",     "width": 230},
        {"fieldname": "amount_planned",  "label": _("Prévu (€)"),               "fieldtype": "Currency", "width": 150},
        {"fieldname": "amount_engaged",  "label": _("Engagé (€)"),              "fieldtype": "Currency", "width": 150},
        {"fieldname": "amount_actual",   "label": _("Réalisé (€)"),             "fieldtype": "Currency", "width": 150},
        {"fieldname": "variance",        "label": _("Écart Prévu-Réalisé (€)"), "fieldtype": "Currency", "width": 200},
        {"fieldname": "pct_consumed",    "label": _("% Consommé"),              "fieldtype": "Percent",  "width": 120},
    ]


# ── Helpers date ──────────────────────────────────────────────────────────────

def _date_clauses(filters):
    """
    Retourne (po_clause, pi_clause, params) pour les filtres de date optionnels.
    PO  : transaction_date   PI : posting_date
    """
    f, t   = filters.get("from_date"), filters.get("to_date")
    params = {"project": filters["project"]}
    po = pi = ""

    if f and t:
        po = "AND po.transaction_date BETWEEN %(from_date)s AND %(to_date)s"
        pi = "AND pi.posting_date     BETWEEN %(from_date)s AND %(to_date)s"
        params.update({"from_date": f, "to_date": t})
    elif f:
        po = "AND po.transaction_date >= %(from_date)s"
        pi = "AND pi.posting_date     >= %(from_date)s"
        params["from_date"] = f
    elif t:
        po = "AND po.transaction_date <= %(to_date)s"
        pi = "AND pi.posting_date     <= %(to_date)s"
        params["to_date"] = t

    return po, pi, params


# ── Données ───────────────────────────────────────────────────────────────────

def get_data(filters):
    project              = filters["project"]
    po_clause, pi_clause, params = _date_clauses(filters)

    # 1. Budget ventilé par catégorie (B15) ───────────────────────────
    budget_rows = frappe.db.sql(
        """
        SELECT   category,
                 COALESCE(SUM(amount_planned), 0) AS amount_planned
        FROM     `tabBudget Detaille Projet`
        WHERE    parent     = %(project)s
          AND    parenttype = 'Project'
        GROUP BY category
        ORDER BY FIELD(category,
                     'Matériel','Prestations externes','ETPs','Frais divers'),
                 category
        """,
        {"project": project},
        as_dict=True,
    )

    # 2. Engagé — Purchase Orders non annulés ─────────────────────────
    po_row = frappe.db.sql(
        f"""
        SELECT COALESCE(SUM(po.grand_total), 0) AS total
        FROM   `tabPurchase Order` po
        WHERE  po.project = %(project)s
          AND  po.status  NOT IN ('Cancelled')
          {po_clause}
        """,
        params,
        as_dict=True,
    )
    engaged = (po_row[0]["total"] or 0) if po_row else 0

    # 3. Réalisé — Purchase Invoices soumises ─────────────────────────
    pi_row = frappe.db.sql(
        f"""
        SELECT COALESCE(SUM(pi.grand_total), 0) AS total
        FROM   `tabPurchase Invoice` pi
        WHERE  pi.project   = %(project)s
          AND  pi.docstatus = 1
          {pi_clause}
        """,
        params,
        as_dict=True,
    )
    actual = (pi_row[0]["total"] or 0) if pi_row else 0

    # 4. Construction des lignes ──────────────────────────────────────
    data          = []
    total_planned = 0

    for row in budget_rows:
        planned        = row["amount_planned"] or 0
        total_planned += planned
        data.append({
            "category":       row["category"],
            "amount_planned":  planned,
            "amount_engaged":  None,
            "amount_actual":   None,
            "variance":        None,
            "pct_consumed":    None,
            "is_total":        0,
        })

    if not budget_rows:
        data.append({
            "category":       _("(Aucune ligne de budget — renseigner l'onglet Budget Ventilé)"),
            "amount_planned":  0,
            "amount_engaged":  None,
            "amount_actual":   None,
            "variance":        None,
            "pct_consumed":    None,
            "is_total":        0,
        })

    # Ligne TOTAL ─────────────────────────────────────────────────────
    variance = total_planned - actual
    pct      = round(actual / total_planned * 100, 1) if total_planned else 0.0

    data.append({
        "category":       _("TOTAL"),
        "amount_planned":  total_planned,
        "amount_engaged":  engaged,
        "amount_actual":   actual,
        "variance":        variance,
        "pct_consumed":    pct,
        "is_total":        1,
    })

    return data
