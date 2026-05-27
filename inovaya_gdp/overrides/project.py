import frappe


def after_insert(doc, method=None):
    """
    B27 — Propager is_milestone depuis les Task templates vers les Tasks générées.

    ERPNext copy_from_template() (appelée dans Project.after_insert()) crée les
    Tasks depuis le Project Template et renseigne le champ ``template_task`` sur
    chaque Task créée, mais NE propage PAS is_milestone.

    Notre hook doc_events ``after_insert`` se déclenche APRÈS le after_insert
    natif d'ERPNext, donc les Tasks sont déjà créées avec template_task renseigné.

    Algorithme :
      Pour chaque Task du projet avec template_task != null,
        lire is_milestone sur la Task template,
        si différent de la Task créée → corriger via set_value (sans update_modified).
    """
    if not doc.project_template:
        return   # Projet sans template → rien à faire

    tasks = frappe.db.get_all(
        "Task",
        filters={"project": doc.name, "template_task": ["is", "set"]},
        fields=["name", "template_task", "is_milestone"],
    )
    if not tasks:
        return

    updated = 0
    for task in tasks:
        tmpl_milestone = frappe.db.get_value("Task", task.template_task, "is_milestone")
        if tmpl_milestone is None:
            continue
        tmpl_val = int(tmpl_milestone or 0)
        task_val = int(task.is_milestone or 0)
        if tmpl_val != task_val:
            frappe.db.set_value(
                "Task", task.name, "is_milestone", tmpl_val,
                update_modified=False,
            )
            updated += 1

    if updated:
        frappe.db.commit()
        frappe.logger().info(
            f"[B27] Projet {doc.name} : {updated} tâche(s) mises à jour (is_milestone)."
        )


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
