import frappe


def after_insert(doc, method=None):
    """
    B27 — Propager is_milestone depuis les Task templates vers les Tasks générées.

    ERPNext copy_from_template() ne propage pas is_milestone.
    Notre hook after_insert se déclenche APRÈS le natif ERPNext → Tasks déjà créées.
    """
    if not doc.project_template:
        return

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
            frappe.db.set_value("Task", task.name, "is_milestone", tmpl_val,
                                update_modified=False)
            updated += 1

    if updated:
        frappe.db.commit()
        frappe.logger().info(
            "[B27] Projet %s : %d tâche(s) mises à jour (is_milestone).",
            doc.name, updated,
        )


def before_save(doc, method=None):
    """
    B11 — Sélection automatique du Project Template par Project Type.

    - Si project_type vide → rien.
    - Si project_template déjà renseigné → ne pas écraser (idempotent).
    - Recherche LIKE sur le nom du template.
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
