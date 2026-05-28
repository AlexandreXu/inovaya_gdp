"""
Correction des permissions manquantes et du in_list_view.

1. Ajoute les permissions DocType pour "Responsable GdP" et "Collaborateur Projet"
   sur Project, Task, Timesheet
2. Passe in_list_view=1 sur Task-inovaya_eisenhower_info

bench --site inovaya.localhost execute inovaya_gdp.setup.fix_permissions.run
"""
import frappe


def _sep(t):
    print(f"\n{'='*65}\n{t}\n{'='*65}")


# ── Configuration des permissions ──────────────────────────────────────────
# Format : (doctype, role, read, write, create, delete)
PERMS = [
    # Responsable GdP — accès complet lecture + écriture, pas de suppression
    ("Project",    "Responsable GdP",        1, 1, 1, 0),
    ("Task",       "Responsable GdP",        1, 1, 1, 0),
    ("Timesheet",  "Responsable GdP",        1, 1, 1, 0),
    # Collaborateur Projet — lecture + saisie timesheets, pas de création projet
    ("Project",    "Collaborateur Projet",   1, 0, 0, 0),
    ("Task",       "Collaborateur Projet",   1, 1, 0, 0),
    ("Timesheet",  "Collaborateur Projet",   1, 1, 1, 0),
]


def _upsert_perm(doctype, role, read, write, create, delete):
    """
    Insère ou met à jour une ligne dans tabDocPerm pour le DocType donné.
    Utilise l'API frappe.permissions (Role Permission Manager).
    """
    from frappe.permissions import add_permission, update_permission_property

    permlevel = 0
    # Vérifie si la permission existe déjà dans tabDocPerm
    existing = frappe.db.get_value(
        "DocPerm",
        {"parent": doctype, "role": role, "permlevel": permlevel},
        "name",
    )

    if existing:
        # Met à jour les flags uniquement
        for prop, val in [("read", read), ("write", write),
                          ("create", create), ("delete", delete)]:
            frappe.db.set_value("DocPerm", existing, prop, val)
        frappe.db.commit()
        print(f"  ✅ MIS À JOUR : {doctype:<12} / {role}")
    else:
        # Crée via l'API officielle (écrit dans tabDocPerm)
        add_permission(doctype, role, permlevel)
        for prop, val in [("read", read), ("write", write),
                          ("create", create), ("delete", delete)]:
            update_permission_property(doctype, role, permlevel, prop, val)
        frappe.db.commit()
        print(f"  ✅ CRÉÉ      : {doctype:<12} / {role}")


def run():
    # ── 1. Permissions DocType ─────────────────────────────────────────
    _sep("1 — AJOUT PERMISSIONS DocType")
    for doctype, role, r, w, c, d in PERMS:
        try:
            _upsert_perm(doctype, role, r, w, c, d)
        except Exception as e:
            print(f"  ❌ ERREUR {doctype}/{role} : {e}")

    # ── 2. in_list_view sur inovaya_eisenhower_info ────────────────────
    _sep("2 — CUSTOM FIELD in_list_view")
    cf_name = "Task-inovaya_eisenhower_info"
    if frappe.db.exists("Custom Field", cf_name):
        frappe.db.set_value("Custom Field", cf_name, "in_list_view", 1)
        frappe.db.commit()
        print(f"  ✅ in_list_view=1 appliqué sur {cf_name}")
    else:
        print(f"  ❌ {cf_name} introuvable — relancer bench migrate")

    # ── 3. Clear cache ─────────────────────────────────────────────────
    _sep("3 — CLEAR CACHE")
    frappe.clear_cache()
    print("  ✅ Cache Frappe vidé")

    # ── 4. Vérification finale ─────────────────────────────────────────
    _sep("4 — VÉRIFICATION FINALE")
    for role in ["Responsable GdP", "Collaborateur Projet"]:
        perms = frappe.db.get_all(
            "DocPerm",
            filters={"parent": ["in", ["Project", "Task", "Timesheet"]], "role": role},
            fields=["parent", "read", "write", "create"],
            order_by="parent",
        )
        print(f"\n  {role} :")
        if not perms:
            print("    ❌ Toujours aucune permission")
        for p in perms:
            print(f"    {p.parent:<12}  read={p.read} write={p.write} create={p.create}")

    cf = frappe.db.get_value("Custom Field", cf_name,
                              ["in_list_view", "hidden"], as_dict=True)
    print(f"\n  {cf_name} : in_list_view={cf.in_list_view}  hidden={cf.hidden}")

    print("\n\n  ✅ Terminé. Accès projet et colonne liste corrigés.")
    print("  → Demander aux utilisateurs de vider leur cache navigateur (Ctrl+Shift+R)")
