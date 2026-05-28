# CHANGELOG — inovaya_gdp

## v1.0.0 — 2026-05-28

Application **InovaYa GdP** — ERPNext v16 native-first.  
Gestion de projets pour InovaYa : planification, suivi, facturation, RH, logistique.

---

### Sprint 1 — Socle métier (B11, B12, B07)

**B11 — Sélection automatique du Project Template par Project Type**  
Hook `before_save` sur Project : quand `project_type` est renseigné et qu'aucun
template n'est encore appliqué, Frappe sélectionne automatiquement le template
correspondant (InovaYa - IND, CLIENT TEE, R&D, Digital, Interne).

**B12 — Champs personnalisés Projet**  
Custom Fields `inovaya_*` sur Project : `inovaya_business_vertical`,
`inovaya_budget_section`, `inovaya_billing_section`, `inovaya_eac` (Estimated at
Completion), `inovaya_billing_notes`, `inovaya_project_impact_summary`.
Custom Fields sur Task : `inovaya_importance`, `inovaya_eisenhower_info`,
`inovaya_hours_per_day`, `inovaya_task_vertical`.
Custom Fields sur System Settings : `inovaya_daily_hours_threshold`,
`inovaya_weekly_hours_threshold`, `inovaya_default_hourly_rate`.
Custom Fields sur Purchase Order et Material Request : `inovaya_linked_task`.

**B07 — Alertes dépassement heures hebdomadaires**  
Scheduler event `weekly` (chaque dimanche) : calcule les heures enregistrées par
collaborateur sur la semaine écoulée, envoie un email d'alerte aux managers si le
seuil `inovaya_weekly_hours_threshold` est dépassé.

---

### Sprint 2 — Tâches & Absences (B02, B04, B22, B23)

**B02 — DocType "Annexe Task"**  
Tâche légère hors projet (autoname ANNX-.#####). Champs : subject, status, priority,
assigned_to (Link→User), initiateur, pole, dates, importance, Eisenhower, heures/jour.
Réutilise le hook `before_save` de Task pour le calcul Eisenhower.

**B04 — Priorisation Eisenhower automatique**  
Hook `before_save` sur Task et Annexe Task : croise `inovaya_importance`
(Critique/Haute/Normale/Faible) et `priority` (Urgent/Moyen/Faible) pour déduire
le quadrant Eisenhower et renseigner `inovaya_eisenhower_info`
(ex. "Q1 — Faire maintenant", "Q4 — Déléguer").

**B22 — Synchronisation absences ↔ planning**  
Hook `on_submit` / `on_cancel` sur Leave Application (hrms).
À la validation d'un congé : détecte les tâches projet dont les dates chevauchent
le congé et positionne `inovaya_conflit_absence = 1`.
À l'annulation : remet le flag à 0 sauf si un autre congé validé couvre encore la tâche.

**B23 — Alertes congé vs tâches projet**  
Même hook que B22 : en plus du flag, envoie un email au manager du collaborateur
et au chef de projet (Project.owner) listant les tâches impactées par le congé.

---

### Sprint 3 — Conflits de planning (B05)

**B05 — Conflits de planning (blocage dur)**  
Hook `before_save` sur Task : vérifie que les dates de la tâche ne chevauchent pas
une autre tâche assignée au même collaborateur dans le même projet. Lève une exception
Frappe si conflit détecté (bloquant). Utilise un fallback DB sur `_assign` quand
le payload du formulaire ne l'inclut pas (comportement Frappe v16 documenté).

---

### Sprint 4 — Facturation & Budget (B15, B16, B17, B18, B19)

**B15 — DocType "Budget Detaille InovaYa"**  
Child table de Project. Colonnes : category (Select), amount_planned (Currency),
amount_actual (Currency). Supporte plusieurs lignes par projet (ETPs, Frais, etc.).

**B16 — Rapport "Suivi Financier Projet InovaYa"**  
Script Report sur Project : budget prévu vs réalisé, EAC, écart en % et en valeur.
Filtres : from_date / to_date / project / project_type.

**B17 — Jauges budgétaires dynamiques sur la fiche Projet**  
`doctype_js` pour Project : calcul côté client via `frappe.call` pour afficher
budget prévu / réalisé / EAC sous forme de jauges HTML dans la fiche projet.

**B18 — Filtre tâche par projet dans Jalon Facturation**  
`doctype_js` pour Jalon Facturation InovaYa : le champ `task` est filtré dynamiquement
selon le projet sélectionné (uniquement les tâches du projet concerné).

**B19 — Génération Sales Invoice draft depuis Jalon Facturation**  
Hook `on_update` sur Jalon Facturation InovaYa : lorsque le statut passe à "Validé",
crée automatiquement une Sales Invoice en brouillon pré-remplie (client, montant,
référence projet).

---

### Sprint 5 — Rapports & Planification (B01, B03, B20, B21)

**B01 — Rapport "Plan de Charge InovaYa"**  
Script Report sur Task : charge hebdomadaire par collaborateur (heures planifiées
depuis les dates de tâche × `inovaya_hours_per_day` vs heures réalisées depuis
Timesheets soumises). Capacité = `inovaya_daily_hours_threshold` × 5 jours.
Coloration JS : vert < 80 %, orange 80-100 %, rouge > 100 %.

**B03 — Rapport "Tableau de Bord Collaborateur InovaYa"**  
Script Report sur Timesheet : vue individuelle des heures saisies et tâches actives
par collaborateur. Filtres : collaborateur, période.

**B20 — Mise à jour budget ETPs depuis Timesheets (scheduler daily)**  
Scheduler event `daily` : agrège les heures soumises (Timesheet docstatus=1) par
projet, calcule `amount_actual = total_hours × inovaya_default_hourly_rate` et met
à jour la ligne "ETPs" de Budget Detaille InovaYa pour chaque projet.

**B21 — Rapport "Marge Atterrissage InovaYa"**  
Script Report sur Project : calcule la marge d'atterrissage (EAC - budget prévu),
le pourcentage de consommation et signale les projets à risque (marge < 15 %).

---

### Sprint C — Modules métier (B06, B08, B09, B10, B13, B14)

**B06 — Timesheet draft automatique à l'assignation**  
Hook `after_save` sur Task : lorsqu'un nouveau collaborateur est ajouté dans `_assign`,
crée automatiquement un Timesheet brouillon pré-rempli (employee, projet, tâche,
dates, durée). Utilise INSERT SQL direct pour contourner le `OverlapError` ERPNext v16.
Idempotent : vérifie l'existence d'un draft avant création.

**B08 — Rapport "Heures par Verticale InovaYa"**  
Script Report sur Timesheet : heures saisies agrégées par verticale métier
(`inovaya_task_vertical`). Filtres : from_date / to_date / employee / verticale.

**B09 — Workspace "InovaYa Pôle GdP" + Dashboard Charts**  
Workspace accessible aux rôles Manager InovaYa et Responsable GdP.  
Dashboard Charts : "Projets par Type InovaYa" (Group By / Donut) et "Charge Équipe
InovaYa" (Sum heures soumises / Bar mensuel).  
Liens : Projets actifs, Plan de Charge, Heures par Verticale, Marge Atterrissage,
Timesheets, + pages B24/B25.

**B10 — DocType "Impact Projet InovaYa"**  
Autoname IMP-.YYYY.-.#####. Champs : project (reqd), indicateur, valeur (Float),
unite, date_mesure, commentaire. Permissions : Chef de Projet (CRUD),
Direction Générale (lecture seule).

**B13 — DocType "Demande Transport InovaYa"**  
Autoname TRP-.YYYY.-.#####. Champs : project (reqd), task, description_materiel
(reqd), date_souhaitee, statut (Select : Brouillon / Validé / Expédié),
responsable. Permissions : Logistique Achats (all), Chef de Projet (no delete).

**B14 — Alertes retard commande → impact planning**  
Hooks `before_save`, `on_update`, `on_submit` sur Purchase Order.
Condition : `inovaya_linked_task` renseigné ET `schedule_date > task.exp_end_date`.
Action : email au Project.owner et aux managers des collaborateurs assignés à la tâche.
Notification seulement — aucun blocage automatique.

---

### Sprint UI — Interfaces Frappe (B24, B25, B26)

**B24 — Page "Mon Planning" (`/app/mon-planning-inovaya`)**  
Tableau de bord individuel du collaborateur connecté.  
Tâches projet (assignées via `_assign`) + Annexes Tasks (via `assigned_to`).  
Colonnes : Projet · Tâche · Statut · Eisenhower · H.alloué · H.réalisé · Échéance.  
Filtres : Toutes / En retard / Conflit absence. Mise à jour statut inline sécurisée
(vérification assignee côté serveur). Bouton saisie de temps.  
Accessible : Collaborateur Projet, Chef de Projet, Manager InovaYa.

**B25 — Page "Plan de Charge Équipe" (`/app/plan-charge-equipe-inovaya`)**  
Vue manager : 4 semaines (S-1 / S / S+1 / S+2), une ligne par collaborateur.  
Charge colorée : 🟢 < 80 % · 🟡 80-100 % · 🔴 > 100 % de la capacité hebdo.  
Clic sur cellule → popup tâches. Navigation ← / →. Bouton "Ajouter tâche annexe".  
Réutilise la logique de calcul du rapport B01 (jours ouvrés, threshold).  
Accessible : Manager InovaYa, Responsable GdP.

**B26 — Workspace "InovaYa Direction"**  
Tableau de bord KPI pour la Direction Générale.  
4 Dashboard Charts : Projets par Type (donut B09) + Charge Équipe + Budget Réalisé
ETPs + Budget Prévu ETPs.  
5 liens rapports : Marge Atterrissage · Plan de Charge · Suivi Financier Projet ·
Heures par Verticale · Projets actifs.  
Accessible : Direction Générale, Manager InovaYa.  
Blocages documentés Phase 3 : "Charge semaine % en temps réel" et "Top 3 risque"
nécessitent Number Card ou Chart custom avec calcul dynamique.

---

### Fixes (B27, B28, B29)

**B27 — Flag `is_milestone` sur tâches jalon à la création de projet**  
Hook `after_insert` sur Project : parcourt les tâches créées depuis le template
et positionne `is_milestone = 1` sur les tâches dont le sujet contient "Jalon"
ou dont le type est "Milestone".

**B28 — Correctif fallback `_assign` payload Frappe v16**  
Le formulaire Frappe v16 n'inclut pas toujours `_assign` dans le payload `before_save`
lors d'une modification via l'UI web. Correctif : fallback DB avec
`frappe.db.get_value("Task", doc.name, "_assign")` dans les hooks B04, B05, B06.

**B29 — Correctif `frappe.db.affected_rows()` absent en v16**  
La méthode `MariaDBDatabase.affected_rows()` n'existe pas dans Frappe v16.
Correctif dans B20 (budget_update.py) : remplacement par une requête SELECT
d'existence avant le UPDATE pour vérifier la présence de la ligne "ETPs".

---

## Infrastructure technique

- **9 rôles** InovaYa (Collaborateur Projet → Direction Générale)
- **20 custom fields** `inovaya_*` sur Project, Task, Purchase Order, System Settings
- **5 DocTypes** custom (Annexe Task, Budget Detaille, Jalon Facturation, Impact Projet, Demande Transport)
- **5 rapports** Script Report (Plan de Charge, Suivi Financier, Marge Atterrissage, Tableau de Bord Collaborateur, Heures par Verticale)
- **2 pages** Frappe UI (Mon Planning, Plan de Charge Équipe)
- **8 workspaces** InovaYa (Pôle GdP, Direction, Projets, Temps, Finance, RH, Achats, Administration)
- **4 Dashboard Charts** (Projets par Type, Charge Équipe, Budget Réalisé, Budget Prévu)
- **8 overrides** Python (project, task, jalon_facturation, purchase_order, leave_application, weekly_hours_alert, budget_update + __init__)
- **9 hooks** doc_events + 2 scheduler events (weekly B07, daily B20)
- **89 fichiers** trackés en git — branche `POC_InovaYa_V16`

## Déploiement Frappe Cloud

```bash
# 1. Ajouter l'app depuis GitHub
bench get-app https://github.com/AlexandreXu/inovaya_gdp \
    --branch POC_InovaYa_V16

# 2. Installer sur le site
bench --site <site>.frappe.cloud install-app inovaya_gdp

# 3. Vérifier post-install (0 erreur attendu)
bench --site <site>.frappe.cloud execute inovaya_gdp.setup.verify_install.run
```

## Limitations documentées (Phase 3)

| Item | Limitation | Solution Phase 3 |
|------|-----------|-----------------|
| B09/B26 | Dashboard Charts exclus des fixtures (ORM validation `group_by_based_on`) | Correction schéma INSERT ou contribution upstream |
| B09/B26 | "Charge semaine en cours %" non calculable nativement | Number Card custom ou Chart type=Report |
| B26 | "Top 3 projets à risque" = lien vers rapport | Requête custom + Number Card |
| B25 | Pas de drag & drop pour rééquilibrer la charge | Composant Vue.js Phase 3 |
| B06 | Annexe Tasks non incluses dans Plan de Charge (pas de `_assign`) | Migration vers `_assign` ou calcul séparé |
