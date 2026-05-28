"""
Setup B09 — Workspace "InovaYa Pôle GdP" + Dashboard Charts.
bench --site inovaya.localhost execute inovaya_gdp.setup.setup_b09.run

Dashboard Charts créés :
  1. "Projets par Type InovaYa"  — Group By sur Project, group_by_type Count,
     based_on project_type. Natif v16.
  2. "Charge Équipe InovaYa"     — Sum sur Timesheet, value_based_on total_hours.
     (proxy charge : heures réelles soumises. Les heures planifiées futures
     nécessitent un calcul custom non disponible en natif v16 — documenté.)

Workspace "InovaYa Pôle GdP" :
  - Liste projets (status=Open)
  - Shortcut rapport Plan de Charge InovaYa
  - Les 2 charts ci-dessus
  - Rôles : Manager InovaYa + Responsable GdP
"""
import frappe
from frappe.utils import now_datetime


def _insert_chart(name, chart_type, document_type, based_on=None,
                  group_by_type=None, value_based_on=None, color=None,
                  filters_json="[]", time_interval=None, viz_type="Bar"):
    """Insère un Dashboard Chart en SQL direct (schéma v16 vérifié : is_public, type).
    Colonnes absentes en v16 : disabled, time_series_based_on → exclues.
    """
    if frappe.db.exists("Dashboard Chart", name):
        print(f"  ↻  Chart '{name}' déjà existant — conservé")
        return

    now = str(now_datetime())
    frappe.db.sql("""
        INSERT INTO `tabDashboard Chart`
            (name, creation, modified, modified_by, owner, docstatus,
             chart_name, chart_type, type, document_type, based_on,
             group_by_type, value_based_on, color, filters_json,
             time_interval, timeseries, is_public)
        VALUES
            (%s, %s, %s, 'Administrator', 'Administrator', 0,
             %s, %s, %s, %s, %s,
             %s, %s, %s, %s,
             %s, 0, 1)
    """, (name, now, now,
          name, chart_type, viz_type, document_type, based_on,
          group_by_type, value_based_on, color or "#5e64ff", filters_json,
          time_interval))
    frappe.db.commit()
    print(f"  ✅ Chart '{name}' créé ({chart_type} / {viz_type})")


def _insert_workspace_chart_link(workspace, chart_name, idx):
    """Ajoute un chart link dans Workspace Chart."""
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


def _create_workspace(ws_name):
    """Crée le Workspace InovaYa Pôle GdP via ORM (module vide = custom)."""
    if frappe.db.exists("Workspace", ws_name):
        print(f"  ↻  Workspace '{ws_name}' existe déjà — mise à jour partielle")
        return ws_name

    ws = frappe.get_doc({
        "doctype": "Workspace",
        "name": ws_name,
        "title": ws_name,
        "label": ws_name,
        "module": "",
        "icon": "project",
        "color": "#2196f3",
        "is_hidden": 0,
        "public": 1,
        "sequence_id": 99,
        "restrict_to_domain": "",
        "roles": [
            {"role": "Manager InovaYa"},
            {"role": "Responsable GdP"},
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
    return ws_name


def _add_workspace_link(workspace, link_type, label, link_to,
                        is_query_report=0, report_ref_doctype=None, idx=1):
    """Ajoute un lien/raccourci dans Workspace Links."""
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
             %s, %s, %s, %s, %s, %s, %s)
    """, (link_name, now, now,
          workspace,
          "Link", label, link_type, link_to, is_query_report, report_ref_doctype, idx))


def run():
    print("\n=== SETUP B09 — Workspace InovaYa Pôle GdP ===")

    # ── 1. Dashboard Chart 1 : Projets par Type ───────────────────────────
    print("\n[1] Dashboard Charts")
    _insert_chart(
        name="Projets par Type InovaYa",
        chart_type="Group By",
        document_type="Project",
        based_on="project_type",
        group_by_type="Count",
        value_based_on=None,
        color="#4BC0C0",
        filters_json='[["Project","status","=","Open",false]]',
        viz_type="Donut",
    )

    # ── 2. Dashboard Chart 2 : Charge Équipe (heures soumises proxy) ──────
    _insert_chart(
        name="Charge Équipe InovaYa",
        chart_type="Sum",
        document_type="Timesheet",
        based_on="creation",
        group_by_type=None,
        value_based_on="total_hours",
        color="#FF6384",
        filters_json='[["Timesheet","docstatus","=",1,false]]',
        time_interval="Monthly",
        viz_type="Bar",
    )

    # ── 3. Workspace ──────────────────────────────────────────────────────
    print("\n[2] Workspace")
    ws_name = "InovaYa Pôle GdP"
    _create_workspace(ws_name)

    # Vider les links existants pour éviter les doublons
    frappe.db.sql(
        "DELETE FROM `tabWorkspace Link` WHERE parent=%s", (ws_name,)
    )
    frappe.db.sql(
        "DELETE FROM `tabWorkspace Chart` WHERE parent=%s", (ws_name,)
    )

    # ── 4. Liens / Raccourcis dans le Workspace ───────────────────────────
    print("\n[3] Liens Workspace")
    links = [
        # (link_type, label, link_to, is_query_report, report_ref_doctype, idx)
        ("DocType",  "Projets actifs",              "Project",                       0, None,      1),
        ("Report",   "Plan de Charge InovaYa",      "Plan de Charge InovaYa",        1, "Task",    2),
        ("Report",   "Heures par Verticale InovaYa","Heures par Verticale InovaYa",  1, "Timesheet",3),
        ("Report",   "Marge Atterrissage InovaYa",  "Marge Atterrissage InovaYa",    1, "Project", 4),
        ("DocType",  "Timesheets",                  "Timesheet",                     0, None,      5),
    ]
    for lt, label, lo, iqr, rrd, idx in links:
        _add_workspace_link(ws_name, lt, label, lo, iqr, rrd, idx)
        print(f"  ✅ [{idx}] {label} ({lt}:{lo})")

    # ── 5. Charts dans le Workspace ───────────────────────────────────────
    print("\n[4] Charts dans Workspace")
    _insert_workspace_chart_link(ws_name, "Projets par Type InovaYa", 1)
    _insert_workspace_chart_link(ws_name, "Charge Équipe InovaYa", 2)
    frappe.db.commit()
    print("  ✅ Projets par Type InovaYa")
    print("  ✅ Charge Équipe InovaYa")

    # ── 6. Vérification finale ────────────────────────────────────────────
    print("\n[5] VÉRIFICATION")
    ws = frappe.db.get_value("Workspace", ws_name,
                              ["name", "public"], as_dict=True)
    if ws:
        print(f"  ✅ Workspace en DB : {ws.name} | public={ws.public}")

    charts_in_ws = frappe.db.sql(
        "SELECT chart_name FROM `tabWorkspace Chart` WHERE parent=%s ORDER BY idx",
        (ws_name,), as_dict=True,
    )
    for c in charts_in_ws:
        print(f"  ✅ Chart : {c.chart_name}")

    links_in_ws = frappe.db.sql(
        "SELECT label, link_to FROM `tabWorkspace Link` WHERE parent=%s ORDER BY idx",
        (ws_name,), as_dict=True,
    )
    for lk in links_in_ws:
        print(f"  ✅ Lien : {lk.label} → {lk.link_to}")

    print("\n=== FIN SETUP B09 ===\n")

    # ── NOTE MÉTIER ───────────────────────────────────────────────────────
    print("BLOCAGE MÉTIER B09 DOCUMENTÉ :")
    print("  'Charge Équipe InovaYa' = heures réelles soumises (proxy).")
    print("  Heures planifiées semaine en cours = calcul dynamique non natif")
    print("  en Dashboard Chart v16 → Phase 3 avec un Chart type=Report")
    print("  pointant vers Plan de Charge InovaYa (qui calcule planifié).")
    print()
