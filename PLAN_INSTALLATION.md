# Plan d'installation — InovaYa GdP v1.0.0

**App** : `inovaya_gdp`  
**Cible** : ERPNext v16 (Frappe v16)  
**Dépôt** : `https://git.softia.fr/cloclo/poc/erpnext_ai.git` branche `POC_InovaYa_V16`  
**Date** : 2026-05-25

---

## Prérequis communs

- ERPNext v16 opérationnel avec au moins **un site** configuré
- Accès SSH ou terminal avec droits `bench`
- Le compte git doit avoir accès en lecture au dépôt Softia
- Python 3.11+ dans l'environnement virtualenv de bench

---

## Scénario 1 — Instance self-hosted (Linux / VM / WSL)

### 1.1 Prérequis

| Élément | Valeur attendue |
|---------|----------------|
| OS | Ubuntu 22.04 LTS ou Debian 12 |
| Frappe bench | v5.x installé, `~/frappe-bench/` |
| ERPNext | v16 installé sur le site cible |
| Site ERPNext | ex. `monsite.localhost` |
| Accès git | SSH key ou HTTPS avec token |

Vérification de l'environnement avant de commencer :
```bash
cd ~/frappe-bench
bench version                          # doit afficher frappe v16.x et erpnext v16.x
bench list-apps                        # erpnext doit être présent
bench --site monsite.localhost list-apps  # erpnext installé sur le site
```

### 1.2 Clonage de l'app

> **IMPORTANT** : Ne pas utiliser `bench get-app` — le dépôt s'appelle `erpnext_ai`
> mais le package Python est `inovaya_gdp`. Le clonage manuel est obligatoire.

```bash
cd ~/frappe-bench/apps

git clone \
  https://git.softia.fr/cloclo/poc/erpnext_ai.git \
  inovaya_gdp \
  --branch POC_InovaYa_V16 \
  --single-branch

# Vérification du clonage
ls inovaya_gdp/
# attendu : hooks.py  setup.py  inovaya_gdp/  fixtures/  README.md  ...
```

Si le dépôt demande une authentification :
```bash
# Avec token HTTPS
git clone \
  https://<TOKEN>@git.softia.fr/cloclo/poc/erpnext_ai.git \
  inovaya_gdp \
  --branch POC_InovaYa_V16
```

### 1.3 Installation dans le virtualenv bench

```bash
cd ~/frappe-bench

# Installe le package Python inovaya_gdp dans l'env bench
pip install -e apps/inovaya_gdp

# Point de contrôle : l'app doit être listée
bench list-apps | grep inovaya_gdp
```

### 1.4 Installation sur le site ERPNext

```bash
bench --site monsite.localhost install-app inovaya_gdp
```

Sortie attendue :
```
[inovaya_gdp] Installation de l'app InovaYa GdP terminée.
[inovaya_gdp] Les fixtures (rôles, champs, modèles, workspaces) ont été chargées.
```

### 1.5 Migration (charge les fixtures)

```bash
bench --site monsite.localhost migrate
```

### 1.6 Build des assets (si interface modifiée)

```bash
bench build --app inovaya_gdp
```

### 1.7 Points de contrôle après installation

**Depuis le terminal :**
```bash
# Vérifie que les fixtures sont chargées
bench --site monsite.localhost execute frappe.db.count --args '["Role"]' | grep -v "^0"

# Vérifie les Task template
bench --site monsite.localhost execute frappe.db.count \
  --args '["Task"]' \
  --kwargs '{"filters": {"is_template": 1, "name": ["like", "InovaYa-%"]}}'
# attendu : 41
```

**Depuis l'interface ERPNext :**

| Élément | Menu | Attendu |
|---------|------|---------|
| Rôles InovaYa | Paramètres > Rôles | 9 rôles `Collaborateur Projet`, `Chef de Projet`, etc. |
| Types de projet | Projets > Types de projet | IND, CLIENT TEE, R&D, Digital, Interne |
| Tâches template | Projets > Tâches (filtre is_template=1) | 41 tâches InovaYa-TEE-01…InovaYa-INT-06 |
| Modèles de projet | Projets > Modèles de projet | 5 modèles InovaYa |
| Workspaces | Accueil | 6 espaces InovaYa (Projets, Temps, Achats Projet, Finance Projet, RH Absences, Administration GdP) |
| Champs custom | Personnalisation > Champs personnalisés | 6 champs préfixe `inovaya_` |

### 1.8 Vérification fonctionnelle minimale

```
1. Créer un projet test avec Project Type = "CLIENT TEE"
2. Sélectionner le modèle "InovaYa - CLIENT TEE" → vérifier que 11 tâches sont générées
3. Ouvrir une tâche → vérifier les champs custom (inovaya_criticite, inovaya_categorie_tache…)
4. Ouvrir le workspace "InovaYa Projets" → vérifier que les shortcuts fonctionnent
5. Créer une feuille de temps liée au projet → workspace "InovaYa Temps"
```

### 1.9 Rollback si l'installation échoue

**Désinstaller l'app du site :**
```bash
bench --site monsite.localhost uninstall-app inovaya_gdp --yes
bench --site monsite.localhost migrate
```

**Supprimer l'app de bench :**
```bash
# Retirer du virtualenv
pip uninstall inovaya_gdp -y

# Supprimer le dossier
rm -rf ~/frappe-bench/apps/inovaya_gdp
```

**Si les fixtures ont laissé des données corrompues :**
```bash
# Supprimer manuellement via console Frappe
bench --site monsite.localhost console
```
```python
# Dans la console Frappe
frappe.db.delete("Task", {"name": ["like", "InovaYa-%"], "is_template": 1})
frappe.db.delete("Project Template", {"name": ["like", "InovaYa -%"]})
frappe.db.delete("Project Type", {"name": ["in", ["IND","CLIENT TEE","R&D","Digital","Interne"]]})
frappe.db.delete("Custom Field", {"fieldname": ["like", "inovaya_%"]})
frappe.db.delete("Role", {"name": ["like", "%InovaYa%"]})
frappe.db.commit()
```

---

## Scénario 2 — Frappe Cloud (instance distante managée)

### 2.1 Prérequis

| Élément | Valeur attendue |
|---------|----------------|
| Compte Frappe Cloud | Accès au dashboard `frappecloud.com` |
| Bench Frappe Cloud | Version ERPNext v16 |
| Dépôt git | Accessible publiquement **ou** token SSH configuré dans FC |
| Droits | Propriétaire ou Développeur sur le site FC |

> **Contrainte FC** : Frappe Cloud ne permet pas l'accès SSH direct à la VM.
> L'installation se fait uniquement via le dashboard ou l'API FC.

### 2.2 Rendre le dépôt accessible depuis Frappe Cloud

**Option A — Dépôt public** (plus simple) :
- Rendre le dépôt `https://git.softia.fr/cloclo/poc/erpnext_ai.git` public en lecture
- Aucune configuration supplémentaire requise

**Option B — Token d'accès privé** :
- Générer un token GitLab avec accès `read_repository`
- Utiliser l'URL : `https://<TOKEN>:@git.softia.fr/cloclo/poc/erpnext_ai.git`

**Option C — Miroir GitHub/GitLab public** (recommandé pour FC) :
- Créer un miroir du dépôt sur GitHub public
- FC gère nativement les dépôts GitHub

### 2.3 Ajout de l'app via le dashboard Frappe Cloud

1. Aller sur `https://frappecloud.com/dashboard` → votre site ERPNext v16
2. Cliquer sur **Apps** → **Add App**
3. Renseigner :
   - **Source** : `https://git.softia.fr/cloclo/poc/erpnext_ai.git`
   - **Branch** : `POC_InovaYa_V16`
   - **App name** : `inovaya_gdp` *(spécifier explicitement si FC demande)*
4. Cliquer **Install**

> **Attention nom de package** : Si FC détecte le nom `erpnext_ai` au lieu de `inovaya_gdp`,
> l'installation échouera. Vérifier que `setup.py` contient bien `name="inovaya_gdp"`.

### 2.4 Vérification du `setup.py`

S'assurer que `apps/inovaya_gdp/setup.py` contient :
```python
from setuptools import setup, find_packages

setup(
    name="inovaya_gdp",
    ...
)
```

Si le fichier dit `name="erpnext_ai"`, le corriger et pousser avant l'installation FC.

### 2.5 Points de contrôle après installation FC

Via le dashboard Frappe Cloud :
- **Apps** → `inovaya_gdp` doit apparaître avec statut **Installed**
- **Logs** → chercher `[inovaya_gdp] Installation de l'app InovaYa GdP terminée`

Via l'interface ERPNext du site FC :
- Mêmes vérifications que le Scénario 1, §1.7

### 2.6 Mise à jour de l'app sur Frappe Cloud

Après chaque push sur `POC_InovaYa_V16` :
1. Dashboard FC → Apps → `inovaya_gdp` → **Update**
2. FC exécute `git pull` + `bench migrate` automatiquement
3. Vérifier les logs de migration

### 2.7 Rollback sur Frappe Cloud

Via le dashboard FC :
1. Apps → `inovaya_gdp` → **Uninstall**
2. FC supprime l'app et exécute `bench migrate`

> FC ne permet pas l'exécution de console Python directement.
> Si des données corrompues persistent, ouvrir un ticket support FC ou utiliser
> le mode **SSH Tunnel** si disponible sur votre offre.

---

## Vérifications fonctionnelles communes (post-installation)

### Test 1 — Création de projet depuis un modèle

```
Menu : Projets > Projets > Nouveau
  → Nom : "PROJ-TEST-001"
  → Type de projet : "CLIENT TEE"
  → Modèle de projet : "InovaYa - CLIENT TEE"
  → Sauvegarder
  → Vérifier : 11 tâches créées automatiquement
  → Vérifier : tâche "InovaYa-TEE-03" est marquée jalon (is_milestone=1)
```

### Test 2 — Champs personnalisés

```
Ouvrir n'importe quelle tâche du projet test
  → Vérifier : présence de "Criticité" (inovaya_criticite), "Catégorie tâche" (inovaya_categorie_tache)
Ouvrir le projet
  → Vérifier : présence de "Type client" (inovaya_type_client), "Code affaire" (inovaya_code_affaire)
```

### Test 3 — Workspaces

```
Accueil → "InovaYa Projets" doit apparaître
  → Cliquer "Projets" → ouvre la liste des projets
  → Cliquer "Modèles de Projet" → ouvre la liste des templates
Accueil → "InovaYa Administration GdP"
  → Visible uniquement pour les rôles "Responsable GdP" et "System Manager"
```

### Test 4 — Feuille de temps

```
Menu : InovaYa Temps > Feuilles de Temps > Nouvelle
  → Lier au projet PROJ-TEST-001
  → Saisir des heures sur une activité
  → Sauvegarder et soumettre
```

---

## Tableau récapitulatif des commandes

| Étape | Self-hosted | Frappe Cloud |
|-------|-------------|--------------|
| Cloner l'app | `git clone ... apps/inovaya_gdp` | Dashboard FC → Add App |
| Installer | `bench ... install-app inovaya_gdp` | Automatique via FC |
| Migrer | `bench ... migrate` | Automatique via FC |
| Vérifier | `bench ... list-apps` | Dashboard FC → Apps |
| Désinstaller | `bench ... uninstall-app inovaya_gdp` | Dashboard FC → Uninstall |
| Mettre à jour | `git pull` + `bench migrate` | Dashboard FC → Update |

---

## Risques résiduels à surveiller

| Risque | Probabilité | Mitigation |
|--------|-------------|------------|
| Nom repo ≠ nom package (`erpnext_ai` vs `inovaya_gdp`) | Élevée | Clone manuel avec alias ; vérifier `setup.py` |
| `Project Template Task` child table différente en v16 | Mitigé | Fixtures réécrites v16 (template_task.json + project_template.json) |
| Icônes Workspace non reconnues | Faible | Noms Lucide vérifiés (folder, check-square, file-text…) |
| Conflits de rôles existants | Faible | Rôles préfixés InovaYa, pas de collision avec rôles ERPNext natifs |
| `start` / `duration` non reconnus sur Task v16 | Faible | Champs natifs confirmés dans le schéma ERPNext v16 |
