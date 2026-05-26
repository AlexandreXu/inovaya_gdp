import frappe


def before_save(doc, method=None):
    """
    B11 — Sélection automatique du Project Template par Project Type.

    Hypothèse technique : le hook ``before_save`` est enregistré via ``doc_events``
    dans hooks.py.  Il se déclenche à chaque sauvegarde (insert + update) AVANT
    que ERPNext n'appelle ``copy_from_template`` (qui se trouve dans ``after_insert``).
    Le template est donc positionné sur ``doc`` à temps pour être lu lors de la
    génération des tâches.

    Règles de gestion :
    - Si ``project_type`` est vide  → rien à faire.
    - Si ``project_template`` est déjà renseigné → ne pas écraser (idempotent).
    - Recherche le premier Project Template dont le **nom contient** ``project_type``
      (correspondance souple, casse non significative grâce à LIKE SQL).
    - Si aucun template ne correspond → continuer sans bloquer.
    """
    if not doc.project_type or doc.project_template:
        return

    templates = frappe.get_all(
        "Project Template",
        filters=[["name", "like", f"%{doc.project_type}%"]],
        pluck="name",
        limit=1,
    )

    if templates:
        doc.project_template = templates[0]
        frappe.msgprint(
            f"Template « {templates[0]} » sélectionné automatiquement "
            f"pour le type « {doc.project_type} ».",
            alert=True,
            indicator="green",
        )
