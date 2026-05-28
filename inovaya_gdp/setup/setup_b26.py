"""
Setup B26 — Workspace "InovaYa Direction" (tableau de bord Direction Générale).
bench --site inovaya.localhost execute inovaya_gdp.setup.setup_b26.run

Crée :
  1. Dashboard Chart "Budget Réalisé InovaYa"  — Sum, Budget Detaille InovaYa, amount_actual
  2. Dashboard Chart "Budget Prévu InovaYa"    — Sum, Budget Detaille InovaYa, amount_planned
  3. Workspace "InovaYa Direction" — rôle Direction Générale uniquement
       - Charts : Projets par Type (B09) + Budget Réalisé + Budget Prévu
       - Liens : Marge Atterrissage + Plan de Charge + Suivi Financier Projet
       + B24/B25 si créés

Blocages documentés (Phase 3) :
  - "Charge équipe semaine en cours %" → nécessite calcul dynamique, lien rapport B01
  - "Top 3 projets à risque" → filtre complexe, lien rapport Marge Atterrissage
  - Budget Detaille InovaYa = child table : group_by based_on=parent fonctionne
    comme Sum global (pas par projet) car Frappe agrège sur created — acceptable POC
"""
import frappe
from frappe.utils import now_datetime


def _insert_chart(name, chart_type, document_type, based_on=None,
                  group_by_type=None, value_based_on=None,
                  aggregate_function_based_on=None,
                  parent_document_type=None,
                  color=None, filters_json="[]",
                  time_interval=None, viz_type="Bar"):
    """Insère un Dashboard Chart avec schéma v16 validé."""
    if frappe.db.exists("Dashboard Chart", name):
        print(f"  ↻  Chart '{name}' déjà existant — conservé")
        return

    now = str(now_datetime())
    frappe.db.sql("""
        INSERT INTO `tabDashboard Chart`
            (name, creation, modified, modified_by, owner, docstatus,
             chart_name, chart_type, type, document_type, parent_document_type,
             based_on, group_by_type, value_based_on, aggregate_function_based_on,
             color, filters_json, time_interval, timeseries, is_public)
        VALUES
            (%s, %s, %s, 'Administrator', 'Administrator', 0,
             %s, %s, %s, %s, %s,
             %s, %s, %s, %s,
             %s, %s, %s, 0, 1)
    """, (name, now, now,
          name, chart_type, viz_type, document_type, parent_document_type,
          based_on, group_by_type, value_based_on, aggregate_function_based_on,
          color or "#5e64ff", filters_json, time_interval))
    frappe.db.commit()
    print(f"  ✅ Chart '{name}' créé ({chart_type}/{viz_type})")


def _insert_workspace_chart_link(workspace, chart_name, idx):
    if frappe.db.exists("Workspace Chart", {"parent": workspace, "chart_name": chart_name}):
        return
    now = str(now_datetime())
    link_name = frappe.generate_hash(length=10)
    frappe.db.sql("""
        INSERT INTO `tabWorkspace Chart`
            (name, creation, modified, modified_by, owner, docstatus,
             parent, parentfield, parenttype, chart_name, idx)
        VALUES
            (%s, %s, %s, 'Administrator', 'Administrator', 0,
             %s, 'charts', 'Workspace', %s, %s)
    """, (link_name, now, now, workspace, chart_name, idx))


def _add_workspace_link(workspace, link_type, label, link_to,
                        is_query_report=0, report_ref_doctype=None, idx=1):
    now = str(now_datetime())
    link_name = frappe.generate_hash(length=10)
    frappe.db.sql("""
        INSERT INTO `tabWorkspace Link`
            (name, creation, modified, modified_by, owner, docstatus,
             parent, parentfield, parenttype,
             type, label, link_type, link_to, is_query_report, report_ref_doctype, idx)
        VALUES
            (%s, %s, %s, 'Administrator', 'Administrator', 0,
             %s, 'links', 'Workspace',
             'Link', %s, %s, %s, %s, %s, %s)
    """, (link_name, now, now, workspace, label, link_type, link_to,
          is_query_report, report_ref_doctype, idx))


def run():
    print("\n=== SETUP B26 — Workspace InovaYa Direction ===")

    # ── 1. Dashboard Charts budget ────────────────────────────────────────
    print("\n[1] Dashboard Charts budget")
    _insert_chart(
        name="Budget Réalisé InovaYa",
        chart_type="Sum",
        document_type="Budget Detaille InovaYa",
        parent_document_type="Project",
        based_on="modified",               # axe temporel
        value_based_on="amount_actual",
        color="#FF6384",
        filters_json='[["Budget Detaille InovaYa","category","=","ETPs",false]]',
        time_interval="Monthly",
        viz_type="Bar",
    )
    _insert_chart(
        name="Budget Prévu InovaYa",
        chart_type="Sum",
        document_type="Budget Detaille InovaYa",
        parent_document_type="Project",
        based_on="modified",
        value_based_on="amount_planned",
        color="#36A2EB",
        filters_json='[["Budget Detaille InovaYa","category","=","ETPs",false]]',
        time_interval="Monthly",
        viz_type="Bar",
    )

    # ── 2. Workspace ──────────────────────────────────────────────────────
    print("\n[2] Workspace")
    ws_name = "InovaYa Direction"
    if frappe.db.exists("Workspace", ws_name):
        print(f"  ↻  Workspace '{ws_name}' déjà existant")
    else:
        ws = frappe.get_doc({
            "doctype": "Workspace",
            "name": ws_name,
            "title": ws_name,
            "label": ws_name,
            "module": "",
            "icon": "bar-chart",
            "color": "#9c27b0",
            "is_hidden": 0,
            "public": 1,
            "sequence_id": 100,
            "roles": [
                {"role": "Direction Generale"},
                {"role": "Manager InovaYa"},
                {"role": "System Manager"},
            ],
            "content": "[]",
            "charts": [],
            "links": [],
            "shortcuts": [],
        })
        ws.flags.ignore_permissions = True
        ws.flags.ignore_validate = True
        ws.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"  ✅ Workspace '{ws_name}' créé")

    # Vider pour éviter doublons
    frappe.db.sql("DELETE FROM `tabWorkspace Link`  WHERE parent=%s", (ws_name,))
    frappe.db.sql("DELETE FROM `tabWorkspace Chart` WHERE parent=%s", (ws_name,))

    # ── 3. Charts ─────────────────────────────────────────────────────────
    print("\n[3] Charts")
    charts = [
        ("Projets par Type InovaYa", 1),   # B09 — existe déjà
        ("Charge Équipe InovaYa",    2),   # B09 — proxy heures réelles
        ("Budget Réalisé InovaYa",   3),
        ("Budget Prévu InovaYa",     4),
    ]
    for chart_name, idx in charts:
        _insert_workspace_chart_link(ws_name, chart_name, idx)
        print(f"  ✅ [{idx}] {chart_name}")

    # ── 4. Liens / Rapports clés ──────────────────────────────────────────
    print("\n[4] Liens Rapports")
    links = [
        # (link_type, label, link_to, is_query_report, report_ref_doctype, idx)
        ("Report", "Marge Atterrissage InovaYa",    "Marge Atterrissage InovaYa",    1, "Project",   1),
        ("Report", "Plan de Charge InovaYa",         "Plan de Charge InovaYa",         1, "Task",      2),
        ("Report", "Suivi Financier Projet InovaYa", "Suivi Financier Projet InovaYa", 1, "Project",   3),
        ("Report", "Heures par Verticale InovaYa",   "Heures par Verticale InovaYa",   1, "Timesheet", 4),
        ("DocType","Projets actifs",                 "Project",                        0, None,        5),
    ]
    for lt, label, lo, iqr, rrd, idx in links:
        _add_workspace_link(ws_name, lt, label, lo, iqr, rrd, idx)
        print(f"  ✅ [{idx}] {label}")

    frappe.db.commit()

    # ── 5. Vérification ───────────────────────────────────────────────────
    print("\n[5] VÉRIFICATION")
    ws = frappe.db.get_value("Workspace", ws_name, ["name", "public"], as_dict=True)
    if ws:
        print(f"  ✅ Workspace : {ws.name} | public={ws.public}")

    charts_db = frappe.db.sql(
        "SELECT chart_name FROM `tabWorkspace Chart` WHERE parent=%s ORDER BY idx",
        (ws_name,), as_dict=True,
    )
    for c in charts_db:
        print(f"  ✅ Chart : {c.chart_name}")

    links_db = frappe.db.sql(
        "SELECT label, link_to FROM `tabWorkspace Link` WHERE parent=%s ORDER BY idx",
        (ws_name,), as_dict=True,
    )
    for lk in links_db:
        print(f"  ✅ Lien : {lk.label} → {lk.link_to}")

    print("""
BLOCAGES MÉTIER B26 DOCUMENTÉS :
  - "Charge semaine en cours (%)" → calcul dynamique non natif en Dashboard Chart v16
    → Lien vers rapport Plan de Charge InovaYa (exact même donnée, moins visuel)
  - "Top 3 projets à risque"      → filtre complexe (atterrissage<15% OU tâches en retard)
    → Lien vers Marge Atterrissage InovaYa (tri manuel par Direction)
  Phase 3 : Chart type=Custom ou Number Card avec script Python dédié.
""")
    print("=== FIN SETUP B26 ===\n")
