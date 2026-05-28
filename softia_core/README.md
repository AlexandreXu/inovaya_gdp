# softia_core — Socle technique Frappe/ERPNext

App Frappe réutilisable développée par **Softia** comme base pour les applications ERPNext prospects.

## Ce que fait softia_core

Fournit les fonctionnalités de gestion de projets suivantes, configurables sans développement :

| Code | Fonctionnalité |
|------|----------------|
| B04 | Priorisation Eisenhower (urgence × importance → priority) |
| B05 | Détection conflits de charge journalière (blocage dur) |
| B06 | Timesheets draft auto à l'assignation d'une tâche |
| B07 | Alertes dépassement heures hebdomadaires (email) |
| B11 | Sélection automatique Project Template par Project Type |
| B14 | Alertes retard commande fournisseur vs échéance tâche |
| B19 | Génération Sales Invoice draft depuis Jalon Facturation |
| B20 | Mise à jour budget ETPs depuis Timesheets soumises |
| B22 | Flag absence validée en conflit sur Task |
| B23 | Alerte email manager + chef projet lors soumission congé |
| B27 | Propagation is_milestone depuis templates (correctif ERPNext v16) |

**DocTypes inclus** : Annexe Task, Budget Detaille Projet, Jalon Facturation, Impact Projet

**Rapports inclus** : Plan de Charge, Tableau de Bord Collaborateur, Suivi Financier Projet, Marge Atterrissage

## Usage pour un nouveau prospect

### 1. Créer l'app prospect

```bash
cd ~/frappe-bench/apps
bench new-app prospect_app
```

### 2. Installer softia_core

```bash
bench get-app softia_core https://github.com/AlexandreXu/inovaya_gdp --branch softia_core
bench --site mon-site.localhost install-app softia_core
```

### 3. Installer l'app prospect

```bash
bench --site mon-site.localhost install-app prospect_app
bench --site mon-site.localhost migrate
```

### 4. `hooks.py` de prospect_app

L'app prospect ne déclare **PAS** de `doc_events` — ils sont dans softia_core.
Elle déclare uniquement ses fixtures métier :

```python
app_name = "prospect_app"
required_apps = ["softia_core"]

fixtures = [
    # Rôles métier du prospect
    {"dt": "Role", "filters": [["name", "in", ["Chef de Projet Prospect", "RH Prospect"]]]},
    # Types de projets prospect
    {"dt": "Project Type", "filters": [["name", "in", ["Interne", "Client", "R&D"]]]},
    # Task templates prospect (is_template=1)
    {"dt": "Task", "filters": [["name", "like", "Prospect-%"], ["is_template", "=", 1]]},
    # Project templates prospect
    {"dt": "Project Template", "filters": [["name", "like", "Prospect -%"]]},
    # Workspaces prospect
    {"dt": "Workspace", "filters": [["name", "like", "Prospect%"]]},
]
```

### 5. Configurer System Settings

Après `bench migrate`, ouvrir System Settings et renseigner la section **Softia Core** :

| Paramètre | Description | Défaut |
|-----------|-------------|--------|
| `softia_app_name` | Nom affiché dans les sujets email | `"Softia ERP"` |
| `softia_importance_roles` | JSON list des rôles autorisés à modifier l'Importance | `[]` (pas de restriction) |
| `softia_urgency_days` | Jours avant échéance = urgence (B04) | `7` |
| `softia_daily_hours_threshold` | Seuil heures/jour avant blocage planning (B05) | `8` |
| `softia_weekly_hours_threshold` | Seuil heures/semaine avant alerte (B07) | `39` |
| `softia_default_hourly_rate` | Taux horaire ETP en €/h (B20/B21) | `50` |
| `softia_hr_role` | Rôle Frappe des RH destinataires des alertes B07 | `"HR Manager"` |

**Exemple pour un prospect nommé "AcmeCorp" :**

```python
# En console Frappe (bench --site site.local console)
import frappe
frappe.db.set_single_value("System Settings", "softia_app_name", "AcmeCorp ERP")
frappe.db.set_single_value("System Settings", "softia_importance_roles",
    '["Chef de Projet", "Directeur"]')
frappe.db.set_single_value("System Settings", "softia_hr_role", "RH AcmeCorp")
frappe.db.commit()
```

## Architecture multi-prospects

```
Frappe Cloud — site prospect_X.frappe.cloud
├── frappe (framework)
├── erpnext (modules métier)
├── softia_core (ce dépôt, branche softia_core) ← socle commun
└── prospect_x_app (dépôt dédié prospect) ← fixtures + personnalisations
```

## Référence

- `CLAUDE.md` — Règles de développement Softia × ERPNext v16
- `ERPNEXT_V16_REALITY.md` — Écarts documentation vs réalité ERPNext v16
- `PROSPECT_TEMPLATE.md` — Template d'analyse CDC pour nouveau prospect

## Développé par

**Softia** — [dev@softia.fr](mailto:dev@softia.fr)
Basé sur le projet InovaYa GdP (Phase 1, mai 2026).
