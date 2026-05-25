# InovaYa GdP — ERPNext v16 Native-First

Application Frappe de configuration ERP Gestion de Projets pour InovaYa SAS (Phase 1).

> **Périmètre de la Phase 1** : socle ERPNext natif uniquement — rôles, modèles de projet, champs de qualification, workspaces et rapports standards. Les modules différenciants (plan de charge, Eisenhower, jalons de facturation automatiques, etc.) sont en backlog Phase 2.

---

## Prérequis

| Composant | Version requise |
|---|---|
| ERPNext | v16.x |
| Frappe | v16.x |
| Python | 3.11+ |
| MariaDB | 10.6+ ou MySQL 8.0+ |
| Node.js | 18+ |

> ⚠️ L'environnement de développement local actuel (Frappe v15.107.2, sans ERPNext) **ne peut pas exécuter cette app directement**. Utiliser une instance ERPNext v16 dédiée (self-hosted ou Frappe Cloud).

---

## Installation

### 1. Obtenir l'application

```bash
# Depuis le répertoire de votre bench ERPNext v16
bench get-app /chemin/vers/inovaya_gdp
# ou depuis un dépôt Git une fois publié :
# bench get-app https://github.com/inovaya/inovaya_gdp
```

### 2. Installer sur le site

```bash
bench --site votre-site.local install-app inovaya_gdp
```

L'installation charge automatiquement via `after_install` :
- Les **9 rôles** InovaYa
- Les **Custom Fields** sur `Project` et `Task`
- Les **5 types de projet** (IND, CLIENT TEE, R&D, Digital, Interne)
- Les **5 modèles de projet** avec leurs phases et jalons
- Les **6 Workspaces** InovaYa

### 3. Vérification post-install

```bash
bench --site votre-site.local run-tests --app inovaya_gdp
```

Ou suivre la checklist manuelle dans `DEMO_SCENARIO_INOVAYA.md`.

### 4. Configuration post-install (manuelle, 30 min)

Voir `CONFIGURATION_NATIVE_FIRST.md` pour :
- Créer la société InovaYa SAS
- Configurer l'exercice fiscal
- Créer les employés et les lier aux utilisateurs
- Paramétrer les types de congés
- Attribuer les rôles aux utilisateurs

---

## Mise à jour

```bash
bench --site votre-site.local migrate
```

Les fixtures sont resynchronisées automatiquement via `after_migrate`.

---

## Désinstallation

```bash
bench --site votre-site.local uninstall-app inovaya_gdp
```

> Les Custom Fields et données métier créés après installation ne sont **pas supprimés** automatiquement. Supprimer manuellement si nécessaire.

---

## Structure du projet

```
inovaya_gdp/
├── inovaya_gdp/
│   ├── fixtures/
│   │   ├── role.json               # 9 rôles InovaYa
│   │   ├── custom_field.json       # Champs légers Project + Task
│   │   ├── project_type.json       # 5 types de projet
│   │   ├── project_template.json   # 5 modèles avec phases/jalons
│   │   └── workspace.json          # 6 espaces de travail
│   ├── setup/
│   │   └── install.py              # Hook after_install / after_migrate
│   ├── hooks.py                    # Déclaration fixtures et hooks
│   └── modules.txt
├── README.md
├── CONFIGURATION_NATIVE_FIRST.md
├── COUVERTURE_NATIVE_ERPNext_V16.md
├── BACKLOG_DEVELOPPEMENTS_SPECIFIQUES.md
└── DEMO_SCENARIO_INOVAYA.md
```

---

## Contacts

- Éditeur : InovaYa SAS — info@inovaya.com
- Intégrateur : à compléter
