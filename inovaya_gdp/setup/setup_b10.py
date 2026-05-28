"""
Setup B10 — DocType "Impact Projet InovaYa".
bench --site inovaya.localhost execute inovaya_gdp.setup.setup_b10.run

DocType créé :
  - Autoname : IMP-.YYYY.-.#####
  - Champs : project (Link→Project, reqd), indicateur (Data),
             valeur (Float), unite (Data), date_mesure (Date),
             commentaire (Small Text)
  - Permissions :
      Chef de Projet     → create / write / read / delete (level 0)
      Direction Generale → read only
  - Shortcut ajouté au Workspace "InovaYa Pôle GdP"
"""
import frappe
from frappe.utils import now_datetime


DT_NAME = "Impact Projet InovaYa"


def _dt_exists():
    return frappe.db.exists("DocType", DT_NAME)


def run():
    print("\n=== SETUP B10 — DocType Impact Projet InovaYa ===")

    # ── 1. Créer le DocType ───────────────────────────────────────────────
    if _dt_exists():
        print(f"  ↻  DocType '{DT_NAME}' déjà existant — skip création")
    else:
        dt = frappe.get_doc({
            "doctype": "DocType",
            "name": DT_NAME,
            "module": "Inovaya",
            "autoname": "IMP-.YYYY.-.#####",
            "is_submittable": 0,
            "custom": 1,
            "track_changes": 1,
            "fields": [
                {
                    "fieldname": "project",
                    "fieldtype": "Link",
                    "label": "Projet",
                    "options": "Project",
                    "reqd": 1,
                    "in_list_view": 1,
                    "search_index": 1,
                },
                {
                    "fieldname": "indicateur",
                    "fieldtype": "Data",
                    "label": "Indicateur",
                    "reqd": 1,
                    "in_list_view": 1,
                },
                {
                    "fieldname": "valeur",
                    "fieldtype": "Float",
                    "label": "Valeur",
                    "in_list_view": 1,
                },
                {
                    "fieldname": "unite",
                    "fieldtype": "Data",
                    "label": "Unité",
                    "in_list_view": 1,
                },
                {
                    "fieldname": "date_mesure",
                    "fieldtype": "Date",
                    "label": "Date de mesure",
                    "in_list_view": 1,
                },
                {
                    "fieldname": "commentaire",
                    "fieldtype": "Small Text",
                    "label": "Commentaire",
                },
            ],
            "permissions": [
                {
                    "role": "Chef de Projet",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 1,
                    "permlevel": 0,
                },
                {
                    "role": "Manager InovaYa",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 1,
                    "permlevel": 0,
                },
                {
                    "role": "Direction Generale",
                    "read": 1,
                    "permlevel": 0,
                },
                {
                    "role": "System Manager",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 1,
                    "permlevel": 0,
                },
            ],
        })
        dt.flags.ignore_permissions = True
        dt.flags.ignore_validate = True
        dt.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"  ✅ DocType '{DT_NAME}' créé")

    # ── 2. Shortcut dans Workspace ────────────────────────────────────────
    ws_name = "InovaYa Pôle GdP"
    if not frappe.db.exists("Workspace", ws_name):
        print(f"  ⚠️  Workspace '{ws_name}' introuvable — shortcut non ajouté")
    else:
        # Vérifier si shortcut existe déjà
        exists = frappe.db.sql(
            "SELECT name FROM `tabWorkspace Link` WHERE parent=%s AND link_to=%s LIMIT 1",
            (ws_name, DT_NAME),
        )
        if exists:
            print(f"  ↻  Shortcut '{DT_NAME}' déjà dans workspace")
        else:
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
                     'Link', 'Impacts Projet', 'DocType', %s, 0, NULL, 6)
            """, (link_name, now, now, ws_name, DT_NAME))
            frappe.db.commit()
            print(f"  ✅ Shortcut 'Impacts Projet' ajouté au Workspace")

    # ── 3. Vérification ───────────────────────────────────────────────────
    print("\n[VÉRIFICATION]")
    dt_ok = frappe.db.exists("DocType", DT_NAME)
    print(f"  {'✅' if dt_ok else '❌'} DocType en DB : {dt_ok}")

    fields = frappe.db.sql(
        "SELECT fieldname, fieldtype FROM `tabDocField` WHERE parent=%s ORDER BY idx",
        (DT_NAME,), as_dict=True,
    )
    for f in fields:
        print(f"  • {f.fieldname} ({f.fieldtype})")

    perms = frappe.db.sql(
        "SELECT role, `read`, `write`, `create` FROM `tabDocPerm` WHERE parent=%s",
        (DT_NAME,), as_dict=True,
    )
    for p in perms:
        print(f"  🔑 {p.role} — r={p.read} w={p.write} c={p.create}")

    print("\n=== FIN SETUP B10 ===\n")
