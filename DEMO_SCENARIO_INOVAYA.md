# Scénario de démonstration — InovaYa GdP Phase 1

Ce document guide un parcours de démonstration complet, du projet à la facturation, en utilisant uniquement les fonctionnalités natives ERPNext v16 configurées par l'app `inovaya_gdp`.

> **Durée estimée** : 45 minutes. Prérequis : instance ERPNext v16 avec l'app installée et les données de base configurées (société, exercice fiscal, un client, deux employés-utilisateurs avec rôles).

---

## Données de démonstration à créer avant la démo

| Objet | Valeur suggérée |
|---|---|
| Société | InovaYa SAS |
| Client | Agglo Grand Lyon |
| Employé 1 | Marie Dupont — Ingénieure projet (rôle : Chef de Projet) |
| Employé 2 | Thomas Bernard — Technicien (rôle : Collaborateur Projet) |
| Manager | Sophie Martin (rôle : Manager InovaYa) |
| Centre de coût | InovaYa SAS - Pôle GdP |
| Type de congé | Congé payé |

---

## Étape 1 — Créer un projet CLIENT TEE depuis le modèle

**Qui** : Chef de Projet (Marie Dupont)
**Workspace** : InovaYa — Projets

1. Ouvrir **Projects → Project → Nouveau**
2. Renseigner :
   - **Nom** : `TEE-2026-001 — Station d'épuration Grand Lyon`
   - **Type de projet** : `CLIENT TEE`
   - **Client** : `Agglo Grand Lyon`
   - **Date de début prévue** : `01/06/2026`
   - **Date de fin prévue** : `30/09/2026`
   - **Coût estimatif** : `185 000`
   - **Centre de coût** : `InovaYa SAS - Pôle GdP`
   - **Verticale Métier** (InovaYa) : `TEE Collectivités`
   - **Notes Facturation** (InovaYa) : `Jalon 1 : 30 % à la signature. Jalon 2 : 40 % à la réception provisoire. Jalon 3 : 30 % à la réception définitive.`
3. Cliquer sur **"Depuis un modèle"** → sélectionner `InovaYa - CLIENT TEE`
4. Sauvegarder → les tâches (Diagnostic, Cadrage, Conception, etc.) sont créées avec les durées relatives converties en dates absolues.

**Résultat visible** : fiche projet qualifiée, tâches structurées, jalons repérés en bleu.

---

## Étape 2 — Affecter les tâches aux collaborateurs

**Qui** : Chef de Projet

1. Dans le projet, onglet **Tâches**
2. Ouvrir la tâche `Diagnostic` :
   - **Assigné à** : `Thomas Bernard`
   - **Priorité** : `High`
   - **Verticale Métier** (InovaYa) : `TEE Collectivités`
3. Ouvrir la tâche `Conception technique` :
   - **Assigné à** : `Marie Dupont`
   - **Priorité** : `Medium`
4. Répéter pour les autres tâches

**Résultat visible** : chaque collaborateur voit ses tâches dans la liste Tasks filtrée par "Assigné à moi".

---

## Étape 3 — Visualiser le Gantt et le Kanban

**Qui** : Chef de Projet / Manager

- **Vue Gantt** : Projects → Task → Vue Gantt (affichage par date)
- **Vue Kanban** : Projects → Task → Vue Kanban (colonnes par statut : Open / Working / Pending Review / Completed)
  - _Particulièrement utile pour les projets de type Digital._

---

## Étape 4 — Saisir une feuille de temps

**Qui** : Thomas Bernard (Collaborateur Projet)
**Workspace** : InovaYa — Temps

1. **Projects → Timesheet → Nouveau**
2. Renseigner :
   - **Employé** : `Thomas Bernard`
3. Dans la table **Détail des activités** :
   - **Type d'activité** : `Consulting` (ou créer "Diagnostic terrain")
   - **De** : `09:00` | **À** : `11:30` (= 2,5 h)
   - **Projet** : `TEE-2026-001 — Station d'épuration Grand Lyon`
   - **Tâche** : `Diagnostic`
4. Soumettre la feuille de temps

**Résultat visible** : le projet affiche `Total heures consommées = 2,5 h` sur la fiche projet.

---

## Étape 5 — Créer une demande d'achat liée au projet

**Qui** : Chef de Projet / Logistique Achats
**Workspace** : InovaYa — Achats Projet

1. **Buying → Material Request → Nouveau**
2. Renseigner :
   - **Objectif** : `Purchase`
   - **Projet** : `TEE-2026-001 — Station d'épuration Grand Lyon`
3. Ajouter un article (ex : `Capteur pH — réf. SENSOR-pH-01`, quantité 2)
4. Soumettre

> Note : le lien à une tâche spécifique n'est pas disponible en Phase 1. Indiquer la tâche en commentaire si nécessaire. Prévu Phase 2 (B12).

5. Depuis la Material Request, générer un **Purchase Order** → champ Projet hérité automatiquement.

---

## Étape 6 — Facturation client (Sales Invoice standard)

**Qui** : Finance InovaYa
**Workspace** : InovaYa — Finance Projet

1. **Selling → Sales Order → Nouveau**
   - **Client** : `Agglo Grand Lyon`
   - Ajouter les articles/prestations de la commande
   - Dans l'onglet **Paiements** : ajouter le calendrier de paiement :
     - Ligne 1 : 30 % — due le 01/06/2026 (signature)
     - Ligne 2 : 40 % — due le 15/09/2026 (réception provisoire)
     - Ligne 3 : 30 % — due le 30/10/2026 (réception définitive)
2. Soumettre la Sales Order
3. Lors de l'atteinte du Jalon 1 : **Créer une Sales Invoice** depuis la Sales Order (30 %)

> La génération automatique depuis un jalon de tâche validé est prévue Phase 2 (B18, B19).

---

## Étape 7 — Gestion d'une absence collaborateur

**Qui** : Thomas Bernard + Manager Sophie Martin
**Workspace** : InovaYa — RH / Absences

1. Thomas Bernard crée une **Leave Application** :
   - **Type de congé** : `Congé payé`
   - **Du** : `15/07/2026` | **Au** : `25/07/2026`
2. Sophie Martin approuve la demande

> Note : aucun blocage automatique des tâches projet n'est généré en Phase 1. Le manager doit manuellement vérifier si une tâche projet existe sur ces dates et ré-affecter si nécessaire. Automatisation prévue Phase 2 (B22, B23).

---

## Étape 8 — Consulter les rapports natifs

**Workspace** : InovaYa — Temps / InovaYa — Finance Projet

| Rapport | Chemin |
|---|---|
| Heures par projet | Reports → Daily Timesheet Summary (filtrer par Projet) |
| Heures par employé | Reports → Employee Hours Utilization Based On Timesheet |
| Achats par projet | Buying → Purchase Order → Filtrer par Projet |
| Factures client | Selling → Sales Invoice → Filtrer par Client |
| Suivi budgétaire | Accounts → Budget → Voir le Cost Center du projet |

---

## Récapitulatif du parcours démontré

| Étape | Couvert ? | Commentaire |
|---|---|---|
| Création projet CLIENT TEE avec modèle | ✅ Natif | |
| Qualification du projet (type, verticale, notes facturation) | ✅ Natif + Custom Fields | |
| Affectation des tâches aux collaborateurs | ✅ Natif | |
| Visualisation Gantt et Kanban | ✅ Natif | |
| Saisie de temps à la demi-heure | ✅ Natif | |
| Demande d'achat liée au projet | ✅ Natif (lien projet) | Lien tâche : Phase 2 |
| Facturation client avec jalons | ⚠️ Natif partiel | Automatisation jalon : Phase 2 |
| Absence collaborateur | ⚠️ Natif partiel | Blocage tâche auto : Phase 2 |
| Rapports natifs | ✅ Natif | |
| Plan de charge manager | ❌ Non montré | Phase 2 |
| Priorisation Eisenhower | ❌ Non montré | Phase 2 |
| Détection conflits de charge | ❌ Non montré | Phase 2 |

---

## Points à soulever avec InovaYa après la démo

1. Les modèles de projet correspondent-ils aux phases réelles utilisées sur le terrain ?
2. Les 5 verticales métier proposées sont-elles les bonnes ?
3. Quel est l'outil RH externe actuel (Lucca, Payfit, autre) ? Impact sur l'interconnexion absences.
4. L'ERP Finance et l'ERP Achats sont-ils des modules de la même instance ERPNext ou des outils tiers ?
5. Valider la liste des besoins Phase 2 et leur priorisation (voir `BACKLOG_DEVELOPPEMENTS_SPECIFIQUES.md`).
