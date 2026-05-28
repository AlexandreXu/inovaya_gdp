"""
B21 — Rapport "Marge Atterrissage InovaYa"
Calcul de marge prévisionnelle vs marge projetée (atterrissage).

Colonnes : Poste | Montant (€)

Lignes :
  CA projet           = SUM(Jalon Facturation InovaYa.amount)
  Budget initial      = SUM(Budget Detaille InovaYa.amount_planned)
  Dépenses réalisées  = SUM(Purchase Order.grand_total) docstatus=1
  Coût ETP réalisé    = SUM(Timesheet Detail.hours) × inovaya_default_hourly_rate
  Reste à faire (EAC) = Project.inovaya_eac
  ─────────────────────────────────────────────────────────────────
  Coût total projeté   = Dépenses + Coût ETP + EAC
  Marge prévisionnelle = CA − Budget initial
  Marge projetée       = CA − Coût total projeté
  Atterrissage %       = Marge projetée / CA × 100
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
        {
            "fieldname": "poste",
            "label": _("Poste"),
            "fieldtype": "Data",
            "width": 340,
        },
        {
            "fieldname": "montant",
            "label": _("Montant (€)"),
            "fieldtype": "Currency",
            "width": 220,
        },
    ]


# ── Données ───────────────────────────────────────────────────────────────────

def get_data(filters):
    project = filters["project"]

    # 1. CA projet — jalons de facturation ───────────────────────────────────
    ca_row = frappe.db.sql(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM   `tabJalon Facturation InovaYa`
        WHERE  project = %(project)s
        """,
        {"project": project},
        as_dict=True,
    )
    ca = float(ca_row[0].total or 0) if ca_row else 0.0

    # 2. Budget initial — Budget Détaillé ────────────────────────────────────
    budget_row = frappe.db.sql(
        """
        SELECT COALESCE(SUM(amount_planned), 0) AS total
        FROM   `tabBudget Detaille InovaYa`
        WHERE  parent     = %(project)s
          AND  parenttype = 'Project'
        """,
        {"project": project},
        as_dict=True,
    )
    budget = float(budget_row[0].total or 0) if budget_row else 0.0

    # 3. Dépenses réalisées — Purchase Orders soumis (coûts engagés) ─────────
    # Source : PO docstatus=1. Quand des PI seront soumises, elles seront
    # ajoutées ici en Phase 2 (UNION ALL PI) pour éviter le double-comptage.
    po_row = frappe.db.sql(
        """
        SELECT COALESCE(SUM(grand_total), 0) AS total
        FROM   `tabPurchase Order`
        WHERE  project   = %(project)s
          AND  docstatus = 1
        """,
        {"project": project},
        as_dict=True,
    )
    depenses = float(po_row[0].total or 0) if po_row else 0.0

    # 4. Coût ETP — heures Timesheet × taux horaire System Settings ──────────
    # tsd.project prioritaire, fallback sur ts.project (ERPNext v16)
    hourly_rate = float(
        frappe.db.get_single_value("System Settings", "inovaya_default_hourly_rate") or 50
    )
    ts_row = frappe.db.sql(
        """
        SELECT COALESCE(SUM(tsd.hours), 0) AS total_hours
        FROM   `tabTimesheet Detail` tsd
        JOIN   `tabTimesheet`        ts  ON ts.name = tsd.parent
        WHERE  tsd.project  = %(project)s
          AND  ts.docstatus = 1
        """,
        {"project": project},
        as_dict=True,
    )
    total_hours = float(ts_row[0].total_hours or 0) if ts_row else 0.0
    cout_etp = total_hours * hourly_rate

    # 5. EAC — champ personnalisé sur le Project (saisi par Resp. GdP) ───────
    eac = float(frappe.db.get_value("Project", project, "inovaya_eac") or 0)

    # 6. Calculs dérivés ──────────────────────────────────────────────────────
    marge_prev   = ca - budget
    cout_total   = depenses + cout_etp + eac
    marge_proj   = ca - cout_total
    atterrissage = round(marge_proj / ca * 100, 1) if ca else 0.0

    def _color(val, is_pct=False):
        """rouge si négatif · vert si > 15 % du CA (ou > 15 % si is_pct)."""
        if is_pct:
            if val < 0:   return "rouge"
            if val > 15:  return "vert"
            return ""
        if val < 0: return "rouge"
        if ca > 0 and val / ca > 0.15: return "vert"
        return ""

    etp_label = "Coût ETP réalisé ({0:.1f}h × {1:.0f}€/h)".format(total_hours, hourly_rate)

    return [
        # ── Données source ─────────────────────────────────────────────────
        _row("CA projet (jalons)",        ca,           "ca"),
        _row("Budget initial",            budget,       "budget"),
        _row("Dépenses réalisées (PO)",   depenses,     "depenses"),
        _row(etp_label,                   cout_etp,     "etp"),
        _row("Reste à faire — EAC",       eac,          "eac"),
        # ── Séparateur visuel ──────────────────────────────────────────────
        {"poste": "", "montant": None, "_key": "sep",
         "_bold": 0, "_color": "", "_is_pct": 0, "_is_sep": 1},
        # ── Résultats ─────────────────────────────────────────────────────
        _row("Coût total projeté",        cout_total,   "cout_total",  bold=1),
        _row("Marge prévisionnelle",      marge_prev,   "marge_prev",  bold=1, color=_color(marge_prev)),
        _row("Marge projetée",            marge_proj,   "marge_proj",  bold=1, color=_color(marge_proj)),
        _row("Atterrissage %",            atterrissage, "atterrissage",bold=1,
             color=_color(atterrissage, is_pct=True), is_pct=1),
    ]


def _row(poste, montant, key, bold=0, color="", is_pct=0):
    return {
        "poste":   poste,
        "montant": montant,
        "_key":    key,
        "_bold":   bold,
        "_color":  color,
        "_is_pct": is_pct,
        "_is_sep": 0,
    }
