app_name = "softia_core"
app_title = "Softia Core"
app_publisher = "Softia"
app_description = "Socle technique Frappe/ERPNext réutilisable — base pour les apps prospects Softia"
app_email = "dev@softia.fr"
app_license = "MIT"
app_version = "1.0.0"

# ── Fixtures ──────────────────────────────────────────────────────────────────
# Intentionnellement minimaliste : PAS de rôles, PAS de Project Types,
# PAS de Task/Project templates, PAS de Workspaces, PAS de Custom DocPerms.
# Ces données sont propres à chaque prospect → dans l'app prospect.
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [["fieldname", "like", "softia_%"]],
    },
    {
        "dt": "DocType",
        "filters": [
            ["name", "in", [
                "Annexe Task",
                "Budget Detaille Projet",
                "Jalon Facturation",
                "Impact Projet",
            ]],
        ],
    },
]

after_install = "softia_core.setup.install.after_install"
after_migrate = "softia_core.setup.install.after_migrate"

doc_events = {
    # B11 — Auto-sélection Project Template par Project Type
    # B27 — Propagation is_milestone (correctif bug ERPNext v16)
    "Project": {
        "before_save":  "softia_core.overrides.project.before_save",
        "after_insert": "softia_core.overrides.project.after_insert",
    },
    # B04 — Eisenhower  B05 — Conflits charge  B06 — Timesheet draft auto
    "Task": {
        "before_save": "softia_core.overrides.task.before_save",
        "after_save":  "softia_core.overrides.task.after_save",
    },
    "Annexe Task": {
        "before_save": "softia_core.overrides.task.before_save",
    },
    # B19 — Sales Invoice draft quand statut → "Validé"
    "Jalon Facturation": {
        "on_update": "softia_core.overrides.jalon_facturation.on_update",
    },
    # B14 — Alerte retard PO vs échéance tâche
    "Purchase Order": {
        "before_save": "softia_core.overrides.purchase_order.before_save",
        "on_update":   "softia_core.overrides.purchase_order.on_update",
        "on_submit":   "softia_core.overrides.purchase_order.on_submit",
    },
    # B22 — Flag softia_conflit_absence  B23 — Alerte email absence↔tâches
    "Leave Application": {
        "on_submit": "softia_core.overrides.leave_application.on_submit",
        "on_cancel": "softia_core.overrides.leave_application.on_cancel",
    },
}

doctype_js = {
    "Jalon Facturation": "public/js/jalon_facturation.js",
    "Project":           "public/js/project_softia.js",
}

scheduler_events = {
    "weekly": ["softia_core.overrides.weekly_hours_alert.run"],
    "daily":  ["softia_core.overrides.budget_update.run"],
}
