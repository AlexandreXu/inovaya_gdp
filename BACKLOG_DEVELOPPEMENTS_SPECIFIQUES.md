# Backlog — Développements Spécifiques Phase 2+

Ce fichier liste les besoins fonctionnels identifiés dans le CDC InovaYa qui **ne sont pas couverts nativement par ERPNext v16** et nécessiteront un développement custom dans les phases suivantes.

> Référence CDC : `CAHIER DES CHARGES_ERP GdP signé.pdf` — InovaYa SAS, avril 2026, Révision A.

---

## Tableau du backlog

| # | Besoin fonctionnel | Priorité | Complexité | Dépendances ERPNext | Questions à valider avec InovaYa |
|---|---|---|---|---|---|
| B01 | **Plan de charge manager** — vue hebdomadaire et mensuelle consolidée de la charge de l'équipe | Haute | Haute | Task, Timesheet, Employee | Quelle est l'unité de charge : jours/homme ou heures ? Le manager peut-il modifier les affectations depuis cette vue ? |
| B02 | **Tâches annexes hors projet** — espace "Pôle" pour le manager + espace "Mon Travail" pour le collaborateur | Haute | Moyenne | Task (nouveau DocType ou extension) | Les tâches hors projet doivent-elles apparaître dans les timesheets ? Faut-il les versionner ? |
| B03 | **Tableau de bord collaborateur avancé** — vue individuelle (projet, temps alloué, échéance, priorité calculée, statut, temps réalisé) | Haute | Haute | Task, Timesheet, Employee, B01, B05 | Peut-on réutiliser une page Frappe UI existante comme base ? Faut-il une app mobile ? |
| B04 | **Priorisation automatique Eisenhower** — calcul urgence × importance → priorité affichée sur les tâches | Haute | Moyenne | Task, B02 | Quelle est la règle précise : seuils d'urgence en jours ? Qui peut modifier l'importance (uniquement Resp. GdP, Resp. Ops, DG) ? |
| B05 | **Détection automatique des conflits de planning et de charge** — intra-projet, inter-projets, tâches annexes | Haute | Très haute | Task, Timesheet, Employee, B01, B02 | Le blocage est-il dur (impossible de sauvegarder) ou doux (alerte + confirmation) ? Quel seuil : 100 % de charge ou configurable ? |
| B06 | **Alimentation automatique des timesheets depuis les plannings collaborateurs** — pré-remplissage des lignes de timesheet à partir des tâches affectées | Moyenne | Moyenne | Task, Timesheet | La saisie reste-t-elle toujours manuelle par le collaborateur, ou veut-on une saisie en un clic depuis le planning ? |
| B07 | **Alertes dépassement heures hebdomadaires** — notification manager + RH si un collaborateur dépasse le seuil hebdomadaire | Haute | Faible | Timesheet, Employee, Email Notification | Quel est le seuil réglementaire retenu ? 35h, 39h, ou configurable par employé ? |
| B08 | **Heures par verticale métier** — rapport consolidé heures par personne × verticale métier (champ `inovaya_task_vertical` existant) | Moyenne | Faible | Task (champ custom déjà créé), Timesheet | Le champ "Verticale" doit-il aussi être sur les timesheets ou uniquement sur les tâches ? |
| B09 | **Feuille de route du Pôle GdP** — vue portfolio avec indicateurs de suivi propres au pôle | Moyenne | Moyenne | Project, Dashboard, B03 | Quels indicateurs précisément : nb projets actifs, charge totale, budget consommé, alertes en cours ? |
| B10 | **Suivi d'impact des projets** — page dédiée par projet avec indicateurs d'impact environnemental et social | Basse | Moyenne | Project (champ temporaire `inovaya_project_impact_summary` existant) | Quels sont les indicateurs d'impact retenus par InovaYa ? Liés à un référentiel (Bilan Carbone, etc.) ? |
| B11 | **Sélection automatique du modèle de projet par typologie** — hook qui charge automatiquement le template correspondant au `project_type` sélectionné | Haute | Faible | Project, Project Template, Project Type | Valider que les 5 typologies correspondent bien aux 5 modèles existants. |
| B12 | **Lien Achat → Tâche projet** — champ `Task` sur Material Request et Purchase Order pour lier une commande à une tâche spécifique | Haute | Faible | Material Request, Purchase Order, Task | Un achat peut-il être lié à plusieurs tâches ? La tâche doit-elle être bloquée si la commande est en retard ? |
| B13 | **Module Transport** — demande de transport matériel liée à un projet et une tâche | Moyenne | Haute | Nouveau DocType `Demande de Transport` | Quel est le flux exact : qui crée, qui valide, quel lien avec l'expédition fournisseur ? |
| B14 | **Alertes retard commande → impact planning** — notification chef de projet en cas de changement de statut ou retard sur un Purchase Order | Haute | Moyenne | Purchase Order, Task, Email/Notification | L'alerte doit-elle proposer un re-planning automatique ou seulement informer ? |
| B15 | **Budget ventilé par type d'achat** — table détaillée sur la fiche projet (matériel, prestations, ETPs) | Haute | Faible | Project (Custom DocType child table) | Quelles sont les catégories definitives retenues par InovaYa ? Correspondent-elles aux comptes comptables ? |
| B16 | **Vue financière prévu/engagé/réalisé** — agrégation Purchase Request + Purchase Order + Purchase Invoice par projet | Haute | Moyenne | Purchase Order, Purchase Invoice, GL Entry | Le "prévu" est-il le budget initial ou le révisé ? Comment gérer les avoirs ? |
| B17 | **Jauges budgétaires dynamiques** — indicateur visuel % budget consommé sur la fiche projet | Moyenne | Faible | Project, B16 | Doit-on afficher une jauge globale ou une par catégorie d'achat ? |
| B18 | **Jalons de facturation liés aux tâches** — DocType `Jalon de Facturation` lié à Project + Task avec statut | Haute | Moyenne | Project, Task, Sales Invoice | Un jalon peut-il couvrir plusieurs tâches ? Qui valide la completion du jalon ? |
| B19 | **Génération automatique de demande de facturation** — workflow : validation jalon → création Sales Invoice draft | Haute | Moyenne | B18, Sales Invoice, Workflow | Faut-il une double validation (chef de projet + finance) avant création de la facture ? |
| B20 | **Alimentation budget par heures** — intégration du coût ETP (heures × taux horaire) dans le budget réalisé | Moyenne | Moyenne | Timesheet, Activity Cost, Project | Le taux horaire est-il fixe par rôle ou par employé ? Est-il confidentiel ? |
| B21 | **Calcul objectif de marge et atterrissage** — formule Marge = Budget − (Dépenses + Coût ETP) + EAC | Haute | Moyenne | B16, B20 | Quelle est la formule exacte retenue ? L'atterrissage doit-il tenir compte du reste à faire saisi manuellement ? |
| B22 | **Synchronisation absences ↔ planning** — blocage automatique des tâches projet lors de la validation d'un congé | Haute | Haute | Leave Application, Task, B05 | Le blocage est-il dur ou avec notification ? Qui doit réaffecter la tâche : le manager ou le chef de projet ? |
| B23 | **Alertes congé vs tâche existante** — notification au manager et chef de projet lors de la validation d'un congé en conflit | Haute | Faible | Leave Application, Task, Email Notification | La notification doit-elle proposer un workflow de re-planification ou seulement alerter ? |
| B24 | **Pages Frappe UI — Vue Collaborateur** — interface personnalisée Vue.js/Frappe UI pour le tableau de bord individuel | Haute | Haute | B02, B03, B04, B05 | Valider les maquettes avant développement. Faut-il une version mobile/PWA ? |
| B25 | **Pages Frappe UI — Vue Manager** — interface personnalisée pour le plan de charge manager | Haute | Haute | B01, B24 | La vue doit-elle permettre le drag & drop de tâches entre collaborateurs ? |
| B26 | **Pages Frappe UI — Vue Direction** — tableau de bord décisionnel pour la DG | Moyenne | Haute | B09, B16, B21 | Quels KPIs sont prioritaires pour la DG ? Fréquence de rafraîchissement ? |
| B27 | **Copie de `is_milestone` depuis les tâches-modèles** — `create_task_from_template` (ERPNext v16 upstream) ne copie pas le champ `is_milestone` lors de la génération des tâches depuis un Project Template ; les jalons sont créés sans le flag, ce qui empêche le filtre Gantt de les identifier | Haute | Faible | Task, Project Template | Limitation upstream confirmée (v16.19.1). Contournement Phase 1 : les jalons sont identifiables par leur sujet ("Jalon — …"). Correction Phase 2 : hook `after_insert` sur Task ou monkey-patch de `copy_from_template`. |

---

## Légende priorités et complexités

| Valeur | Priorité | Valeur | Complexité estimée |
|---|---|---|---|
| Haute | Bloquant pour la mise en production | Très haute | > 20 j/h dev |
| Moyenne | Nécessaire à 3 mois | Haute | 10–20 j/h dev |
| Basse | Utile à 6 mois+ | Moyenne | 3–10 j/h dev |
| — | — | Faible | < 3 j/h dev |

---

## Ordre de développement recommandé (Phase 2)

```
Sprint 1 : B11 (auto-template) + B12 (lien achat-tâche) + B07 (alertes heures)
Sprint 2 : B04 (Eisenhower) + B02 (tâches hors projet) + B23 (alertes congés)
Sprint 3 : B05 (conflits de charge) + B22 (sync absences-planning)
Sprint 4 : B15 (budget ventilé) + B16 (prévu/engagé/réalisé) + B18 (jalons)
Sprint 5 : B19 (génération facture) + B21 (marge/atterrissage)
Sprint 6 : B24 + B25 + B26 (pages Frappe UI)
```

> L'ordre est indicatif — à valider en atelier de priorisation avec InovaYa avant le lancement de la Phase 2.
