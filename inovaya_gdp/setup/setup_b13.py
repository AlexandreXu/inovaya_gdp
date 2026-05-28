"""
Setup B13 — DocType "Demande Transport InovaYa".
bench --site inovaya.localhost execute inovaya_gdp.setup.setup_b13.run

DocType créé :
  - Autoname : TRP-.YYYY.-.#####
  - Champs : project (Link→Project, reqd), task (Link→Task),
             description_materiel (Data, reqd), date_souhaitee (Date),
             statut (Select: Brouillon/Validé/Expédié, reqd),
             responsable (Link→User)
  - Permissions :
      Logistique Achats  → all (read/write/create/delete)
      Chef de Projet     → read / write / create (pas delete)
      Manager InovaYa    → read / write / create / delete
  - Shortcut ajouté au Workspace "InovaYa Pôle GdP"
"""
import frappe
from frappe.utils import now_datetime


DT_NAME = "Demande Transport InovaYa"


def run():
    print("\n=== SETUP B13 — DocType Demande Transport InovaYa ===")

    # ── 1. Créer le DocType ───────────────────────────────────────────────
    if frappe.db.exists("DocType", DT_NAME):
        print(f"  ↻  DocType '{DT_NAME}' déjà existant — skip création")
    else:
        dt = frappe.get_doc({
            "doctype": "DocType",
            "name": DT_NAME,
            "module": "Inovaya",
            "autoname": "TRP-.YYYY.-.#####",
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
                    "fieldname": "task",
                    "fieldtype": "Link",
                    "label": "Tâche",
                    "options": "Task",
                    "in_list_view": 1,
                },
                {
                    "fieldname": "description_materiel",
                    "fieldtype": "Data",
                    "label": "Description matériel",
                    "reqd": 1,
                    "in_list_view": 1,
                },
                {
                    "fieldname": "date_souhaitee",
                    "fieldtype": "Date",
                    "label": "Date souhaitée",
                    "in_list_view": 1,
                },
                {
                    "fieldname": "statut",
                    "fieldtype": "Select",
                    "label": "Statut",
                    "options": "Brouillon\nValidé\nExpédié",
                    "reqd": 1,
                    "default": "Brouillon",
                    "in_list_view": 1,
                },
                {
                    "fieldname": "responsable",
                    "fieldtype": "Link",
                    "label": "Responsable",
                    "options": "User",
                    "in_list_view": 1,
                },
            ],
            "permissions": [
                {
                    "role": "Logistique Achats",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 1,
                    "permlevel": 0,
                },
                {
                    "role": "Chef de Projet",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 0,
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

    # ── 2. Corriger les permissions Frappe (defaults write/create=1 parfois) ──
    # Forcer Chef de Projet : delete=0
    frappe.db.sql("""
        UPDATE `tabDocPerm`
        SET `delete`=0
        WHERE parent=%s AND role='Chef de Projet'
    """, (DT_NAME,))
    frappe.db.commit()

    # ── 3. Shortcut dans Workspace ────────────────────────────────────────
    ws_name = "InovaYa Pôle GdP"
    if frappe.db.exists("Workspace", ws_name):
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
                     'Link', 'Transports', 'DocType', %s, 0, NULL, 7)
            """, (link_name, now, now, ws_name, DT_NAME))
            frappe.db.commit()
            print(f"  ✅ Shortcut 'Transports' ajouté au Workspace")

    # ── 4. Vérification ───────────────────────────────────────────────────
    print("\n[VÉRIFICATION]")
    dt_ok = frappe.db.exists("DocType", DT_NAME)
    print(f"  {'✅' if dt_ok else '❌'} DocType en DB : {dt_ok}")

    fields = frappe.db.sql(
        "SELECT fieldname, fieldtype, reqd FROM `tabDocField` WHERE parent=%s ORDER BY idx",
        (DT_NAME,), as_dict=True,
    )
    for f in fields:
        req = " (reqd)" if f.reqd else ""
        print(f"  • {f.fieldname} ({f.fieldtype}){req}")

    perms = frappe.db.sql(
        "SELECT role, `read`, `write`, `create`, `delete` FROM `tabDocPerm` WHERE parent=%s",
        (DT_NAME,), as_dict=True,
    )
    for p in perms:
        print(f"  🔑 {p.role} — r={p.read} w={p.write} c={p.create} d={p.delete}")

    print("\n=== FIN SETUP B13 ===\n")
