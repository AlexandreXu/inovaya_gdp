# Configuration Native-First — InovaYa GdP

Ce document décrit les fonctionnalités ERPNext v16 utilisées nativement dans la Phase 1, et explique comment les utiliser au quotidien.

---

## 1. Gestion des Projets

### 1.1 Créer un projet

**Module** : Projects → Project → Nouveau

Champs natifs à renseigner obligatoirement :

| Champ natif | Description |
|---|---|
| Nom du projet | Libellé du projet |
| Statut | Open / Completed / Cancelled / Hold |
| Type de projet | Sélectionner parmi IND, CLIENT TEE, R&D, Digital, Interne |
| Client | Lien vers le client (module Selling) |
| Société | InovaYa SAS |
| Date de début prévue | Date de démarrage |
| Date de fin prévue | Échéance cible |
| Coût estimatif | Budget issu du chiffrage commercial (en €) |
| Centre de coût | Pour le suivi budgétaire comptable |

Champs InovaYa ajoutés (section "InovaYa") :

| Champ custom | Description |
|---|---|
| Verticale Métier | TEE Collectivités / Traitement Eau Industriel / R&D / Digital / Transversal |
| Synthèse d'Impact | Description courte des impacts environnementaux attendus |
| Notes Facturation | Jalons et conditions de paiement (texte libre, sans automatisation en Phase 1) |

### 1.2 Utiliser un modèle de projet

Lors de la création d'un projet, cliquer sur **"Depuis un modèle"** et sélectionner le modèle correspondant à la typologie :

| Modèle | Phases générées |
|---|---|
| InovaYa - CLIENT TEE | Diagnostic → Cadrage → Conception → Achats → Réalisation → Mise en service → Clôture |
| InovaYa - IND | Cadrage industriel → Ingénierie → Approvisionnement → Installation → Tests → Clôture |
| InovaYa - R&D | Cadrage hypothèse → Expérimentation → Analyse → Itération → Documentation → Valorisation |
| InovaYa - Digital | Cadrage → Spécification → Développement → Recette → Déploiement → Maintenance |
| InovaYa - Interne | Cadrage → Plan d'action → Réalisation → Validation → Capitalisation |

> Les tâches générées sont modifiables librement par le chef de projet. Les dates relatives sont converties en dates absolues à partir de la date de début du projet.

### 1.3 Modifier un modèle

Les modèles sont accessibles via **Projects → Project Template**. InovaYa peut les modifier sans intervention technique (ajout/suppression de tâches, modification des durées).

### 1.4 Vues disponibles

| Vue | Accès |
|---|---|
| Liste des projets | Projects → Project → Vue Liste |
| Gantt du projet | Ouvrir le projet → Onglet "Tâches" → Vue Gantt |
| Kanban des tâches | Projects → Task → Vue Kanban |
| Tâches par collaborateur | Projects → Task → Filtrer par "Assigné à" |

---

## 2. Suivi des Temps

### 2.1 Saisir une feuille de temps

**Module** : Projects → Timesheet → Nouvelle Feuille de Temps

- Champ **Employé** : sélectionner l'employé
- Dans la table **Détail des activités** :
  - **Type d'activité** : choisir la nature du travail
  - **De** / **À** : heures de début et de fin (granularité 0,5h possible, ex : 09:00 → 09:30)
  - **Projet** : lier au projet
  - **Tâche** : lier à la tâche si applicable

> **Convention de granularité** : saisir au minimum des créneaux de 30 minutes. Aucun blocage technique, mais la règle est documentée ici par convention métier.

### 2.2 Rapports de temps disponibles nativement

| Rapport | Accès |
|---|---|
| Récapitulatif Timesheet journalier | Reports → Daily Timesheet Summary |
| Heures par employé | Reports → Employee Hours Utilization Based On Timesheet |
| Feuilles de temps par projet | Projects → Timesheet → Filtrer par Projet |

---

## 3. Achats liés aux projets

### Flux d'achat recommandé

1. **Demande de Matériel** (Material Request) : créer depuis Buying → Material Request, renseigner le champ **Projet**.
2. **Bon de Commande** (Purchase Order) : généré depuis la Demande de Matériel, avec le champ **Projet** hérité.
3. **Facture Fournisseur** (Purchase Invoice) : liée au Purchase Order.

> Le lien à une **tâche spécifique** (pas seulement au projet) n'est pas disponible nativement — prévu en Phase 2.

---

## 4. Finance et Budget

### 4.1 Budget projet

Deux approches natives disponibles :

**A — Champ "Coût estimatif" sur le projet** : simple, visible sur la fiche projet.

**B — Module Budget (recommandé pour le suivi comptable)** :
1. Créer un **Centre de Coût** par projet (ou par pôle).
2. Créer un **Budget** associé à ce Centre de Coût pour l'exercice fiscal en cours.
3. ERPNext alerte automatiquement en cas de dépassement budgétaire sur les écritures comptables.

### 4.2 Facturation client

1. Créer une **Commande Client** (Sales Order) liée au projet.
2. Configurer un **Calendrier de Paiement** (Payment Schedule) sur la commande pour les jalons de facturation.
3. Générer les **Factures Client** (Sales Invoice) manuellement au moment du jalon.

> La génération automatique de factures depuis un jalon de tâche validé est prévue en Phase 2.

---

## 5. RH et Absences

### 5.1 Gérer les congés

1. Configurer les **Types de Congé** (HR → Leave Type).
2. Attribuer un **Calendrier de Congés** (Holiday List) aux employés.
3. Les collaborateurs saisissent leurs **Demandes de Congé** (Leave Application).
4. Le manager approuve via le workflow natif ERPNext.

> La prise en compte automatique des congés dans le planning projet (blocage des tâches) est prévue en Phase 2.

---

## 6. Workspaces disponibles

| Workspace | Public | Accès |
|---|---|---|
| InovaYa — Projets | Oui | Tous les rôles |
| InovaYa — Temps | Oui | Tous les rôles |
| InovaYa — Achats Projet | Oui | Logistique Achats, Chef de Projet, Manager InovaYa |
| InovaYa — Finance Projet | Oui | Finance InovaYa, Direction Generale |
| InovaYa — RH / Absences | Oui | RH InovaYa, Manager InovaYa |
| InovaYa — Administration GdP | Non (restreint) | Responsable GdP, System Manager |

---

## 7. Rôles et attribution

Attribuer les rôles via **Settings → User → Rôles** :

| Rôle | Profil type |
|---|---|
| Collaborateur Projet | Tout collaborateur opérationnel |
| Chef de Projet | Responsable d'un ou plusieurs projets |
| Manager InovaYa | Manager d'équipe avec vision charge |
| Responsable GdP | Responsable du pôle Gestion de Projets |
| Responsable Operations | Responsable des opérations terrain |
| Direction Generale | Direction générale |
| Finance InovaYa | Équipe finance / contrôle de gestion |
| Logistique Achats | Équipe achats et logistique |
| RH InovaYa | Équipe RH |

> Combiner avec les rôles ERPNext natifs (ex : "Projects User" pour les collaborateurs, "Purchase User" pour la logistique).
