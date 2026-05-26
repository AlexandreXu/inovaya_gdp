app_name = "inovaya_gdp"
app_title = "InovaYa GdP"
app_publisher = "InovaYa"
app_description = "Configuration native-first ERP Gestion de Projets pour InovaYa — Phase 1"
app_email = "info@inovaya.com"
app_license = "MIT"
app_version = "1.0.0"

# Chargement des fixtures à l'installation et lors de bench migrate
fixtures = [
    # --- Rôles InovaYa ---
    {
        "dt": "Role",
        "filters": [
            ["name", "in", [
                "Collaborateur Projet",
                "Chef de Projet",
                "Manager InovaYa",
                "Responsable GdP",
                "Responsable Operations",
                "Direction Generale",
                "Finance InovaYa",
                "Logistique Achats",
                "RH InovaYa",
            ]]
        ],
    },
    # --- Champs personnalisés légers (préfixe inovaya_) ---
    {
        "dt": "Custom Field",
        "filters": [
            ["fieldname", "like", "inovaya_%"],
        ],
    },
    # --- Types de projet InovaYa ---
    {
        "dt": "Project Type",
        "filters": [
            ["name", "in", ["IND", "CLIENT TEE", "R&D", "Digital", "Interne"]],
        ],
    },
    # --- Tâches-modèles (v16 : les données de planification vivent sur Task, is_template=1) ---
    {
        "dt": "Task",
        "filters": [
            ["name", "like", "InovaYa-%"],
            ["is_template", "=", 1],
        ],
    },
    # --- Modèles de projet InovaYa ---
    {
        "dt": "Project Template",
        "filters": [
            ["name", "like", "InovaYa -%"],
        ],
    },
    # --- DocTypes custom InovaYa (B02+) ---
    {
        "dt": "DocType",
        "filters": [
            ["name", "in", ["Annexe Task"]],
        ],
    },
    # --- Espaces de travail InovaYa ---
    {
        "dt": "Workspace",
        "filters": [
            ["name", "like", "InovaYa%"],
        ],
    },
]

after_install = "inovaya_gdp.setup.install.after_install"
after_migrate = "inovaya_gdp.setup.install.after_migrate"

# ---------------------------------------------------------------------------
# B11 — Sélection automatique du Project Template par Project Type
# ---------------------------------------------------------------------------
doc_events = {
    "Project": {
        "before_save": "inovaya_gdp.overrides.project.before_save",
    },
    # B04 — Priorisation automatique Eisenhower (urgence × importance → priority)
    "Task": {
        "before_save": "inovaya_gdp.overrides.task.before_save",
    },
    "Annexe Task": {
        "before_save": "inovaya_gdp.overrides.task.before_save",
    },
    # B23 — Alertes congé vs tâches projet
    # Requiert l'app "hrms" (Leave Application). Silencieux si hrms absent.
    "Leave Application": {
        "on_submit": "inovaya_gdp.overrides.leave_application.on_submit",
    },
}

# ---------------------------------------------------------------------------
# B07 — Alertes dépassement heures hebdomadaires
# Frappe exécute l'événement "weekly" chaque dimanche à minuit (cron: 0 0 * * 0).
# Queue "default" (< 30 s) — utiliser "weekly_long" uniquement pour des jobs > plusieurs minutes.
# ---------------------------------------------------------------------------
scheduler_events = {
    "weekly": [
        "inovaya_gdp.overrides.weekly_hours_alert.run",
    ],
}
