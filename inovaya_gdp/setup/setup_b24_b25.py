"""
Setup B24/B25 — Enregistrement des Pages Frappe en DB + liens Workspace.
bench --site inovaya.localhost execute inovaya_gdp.setup.setup_b24_b25.run

Crée dans tabPage :
  - "plan-charge-equipe-inovaya" (B25 — Manager)
  - "mon-planning-inovaya"       (B24 — Collaborateur)

Ajoute dans Workspace :
  - "plan-charge-equipe-inovaya" → InovaYa Pôle GdP (Manager)
  - "mon-planning-inovaya"       → InovaYa Projets (si existe) OU InovaYa Pôle GdP
"""
import frappe
from frappe.utils import now_datetime


PAGES = [
    {
        "name":    "plan-charge-equipe-inovaya",
        "title":   "Plan de Charge Équipe",
        "module":  "Inovaya",
        "roles":   ["Manager InovaYa", "Responsable GdP", "System Manager"],
        "workspace": "InovaYa Pôle GdP",
        "ws_label": "Plan de Charge (vue manager)",
        "ws_idx": 8,
    },
    {
        "name":    "mon-planning-inovaya",
        "title":   "Mon Planning",
        "module":  "Inovaya",
        "roles":   ["Collaborateur Projet", "Chef de Projet",
                    "Manager InovaYa", "Responsable GdP", "System Manager"],
        "workspace": "InovaYa Pôle GdP",
        "ws_label": "Mon Planning (collaborateur)",
        "ws_idx": 9,
    },
]


def _create_page(cfg):
    name = cfg["name"]
    if frappe.db.exists("Page", name):
        print(f"  ↻  Page '{name}' déjà existante")
        return

    now = str(now_datetime())
    frappe.db.sql("""
        INSERT INTO `tabPage`
            (name, creation, modified, modified_by, owner, docstatus,
             page_name, title, module, standard)
        VALUES
            (%s, %s, %s, 'Administrator', 'Administrator', 0,
             %s, %s, %s, 'Yes')
    """, (name, now, now, name, cfg["title"], cfg["module"]))

    # Rôles
    for role in cfg["roles"]:
        role_name = frappe.generate_hash(length=10)
        frappe.db.sql("""
            INSERT INTO `tabHas Role`
                (name, creation, modified, modified_by, owner, docstatus,
                 parent, parentfield, parenttype, role)
            VALUES
                (%s, %s, %s, 'Administrator', 'Administrator', 0,
                 %s, 'roles', 'Page', %s)
        """, (role_name, now, now, name, role))

    frappe.db.commit()
    print(f"  ✅ Page '{name}' ({cfg['title']}) créée")


def _add_page_to_workspace(ws_name, page_name, label, idx):
    """Ajoute un lien de type Page dans un Workspace."""
    exists = frappe.db.sql(
        "SELECT name FROM `tabWorkspace Link` WHERE parent=%s AND link_to=%s LIMIT 1",
        (ws_name, page_name),
    )
    if exists:
        print(f"  ↻  Lien Page '{page_name}' déjà dans workspace '{ws_name}'")
        return

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
             'Link', %s, 'Page', %s, 0, NULL, %s)
    """, (link_name, now, now, ws_name, label, page_name, idx))
    frappe.db.commit()
    print(f"  ✅ Lien '{label}' (Page:{page_name}) → Workspace '{ws_name}'")


def run():
    print("\n=== SETUP B24/B25 — Pages Frappe ===")

    for cfg in PAGES:
        print(f"\n[Page] {cfg['title']}")
        _create_page(cfg)

        ws = cfg["workspace"]
        if frappe.db.exists("Workspace", ws):
            _add_page_to_workspace(ws, cfg["name"], cfg["ws_label"], cfg["ws_idx"])
        else:
            print(f"  ⚠️  Workspace '{ws}' introuvable — lien non ajouté")

    # ── Vérification ─────────────────────────────────────────────────────────
    print("\n[VÉRIFICATION]")
    for cfg in PAGES:
        exists = frappe.db.exists("Page", cfg["name"])
        print(f"  {'✅' if exists else '❌'} Page : {cfg['name']}")

        roles = frappe.db.sql(
            "SELECT role FROM `tabHas Role` WHERE parent=%s AND parenttype='Page'",
            (cfg["name"],), as_dict=True,
        )
        for r in roles:
            print(f"     🔑 {r.role}")

    print("\n=== FIN SETUP B24/B25 ===\n")
