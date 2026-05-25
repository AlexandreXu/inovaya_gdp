# Prompt à transmettre à Claude Code — Création d’une application ERPNext v16 native-first pour InovaYa

Tu interviens comme **développeur senior Frappe / ERPNext v16, architecte fonctionnel ERP et intégrateur technique**. Tu dois créer une première base applicative pour le projet **InovaYa — ERP Gestion de Projets**, en partant d’une **version clean d’ERPNext v16**.

L’objectif de cette première itération est volontairement limité : **mettre en place tout ce qui peut être couvert par ERPNext v16 natif ou par du paramétrage ERPNext/Frappe standard**, sans développer les modules internes différenciants à ce stade. Les développements spécifiques seront ajoutés dans une seconde phase.

Tu dois donc construire une application Frappe d’intégration et de configuration, nommée par défaut `inovaya_gdp_native`, qui installe et organise la configuration native utile pour InovaYa : rôles, espaces de travail, champs de paramétrage lorsque nécessaire, workflows simples, modèles projet, vues, dashboards, rapports natifs référencés, permissions et documentation. Si le nom d’application doit être adapté à la convention du dépôt existant, propose le changement avant de l’appliquer.

## 1. Contexte métier à respecter

InovaYa souhaite remplacer ou réévaluer son outil actuel de gestion de projet afin de mieux piloter ses projets **IND**, **CLIENT / TEE**, **R&D**, **digitaux** et **internes**. Le futur système doit améliorer la centralisation des données projet, la planification, le suivi des charges, le suivi des temps, le lien avec les achats/logistique, le suivi budgétaire, les absences, les droits d’accès et le pilotage global.

L’analyse fonctionnelle préalable montre que certaines fonctionnalités sont natives ou partiellement natives dans ERPNext v16, tandis que d’autres nécessiteront du développement spécifique ultérieur. Pour cette première version, tu dois **maximiser l’usage natif** et **ne pas implémenter les développements spécifiques complexes** comme la détection automatique de conflits de charge, la priorisation Eisenhower automatique, les tâches annexes non liées projet, les jalons de facturation spécifiques ou les écrans Frappe UI avancés.

> Principe directeur : cette version doit être une **fondation ERPNext propre, maintenable et démontrable**, permettant à InovaYa de tester le plus tôt possible les processus couverts nativement.

## 2. Règles impératives de réalisation

Avant de coder, inspecte le projet local et vérifie la présence de Frappe, ERPNext et la version utilisée. Ne suppose pas que tous les DocTypes, champs et rapports existent exactement sous le même nom : vérifie dans le code ou via la console Frappe lorsque c’est possible.

Tu dois respecter les règles suivantes :

| Règle | Consigne à appliquer |
|---|---|
| Version cible | Travailler sur une base **ERPNext v16 clean**. Si la version locale n’est pas v16, l’indiquer clairement et ne pas masquer l’écart. |
| Approche | Faire une application Frappe de **configuration native-first**, pas une application métier spécifique complète. |
| Natif d’abord | Utiliser les modules ERPNext standards : Projects, Tasks, Timesheets, Buying, Selling, Accounts, HR/Leave, Budget, Roles, Permissions, Workspaces, Dashboards, Kanban, Gantt lorsque disponibles. |
| Développement spécifique | Ne pas créer de logique complexe custom dans cette phase. Tout besoin non natif doit être documenté dans un backlog séparé. |
| Custom Fields | Autorisés uniquement s’ils servent à configurer ou qualifier les DocTypes natifs sans créer de logique métier complexe. |
| Custom DocTypes | À éviter dans cette première phase. Si un DocType custom semble indispensable, le documenter comme besoin futur au lieu de le développer. |
| Scripts et hooks | Ne pas créer de hooks métier complexes. Les hooks d’installation/configuration sont acceptés uniquement pour charger les fixtures ou initialiser une configuration standard. |
| Maintenabilité | Toute configuration doit être versionnée autant que possible via fixtures, scripts de setup idempotents ou documentation reproductible. |
| Transparence | Pour chaque élément, préciser s’il est **natif ERPNext**, **paramétrage ERPNext**, **custom field léger**, ou **backlog développement futur**. |

## 3. Périmètre fonctionnel de la version native-first

Tu dois mettre en place une application ou un ensemble de configurations qui couvrent les domaines suivants dans la limite du natif ERPNext v16.

### 3.1 Gestion de projet native

Configurer le socle projet autour des DocTypes standards ERPNext/Frappe, notamment **Project**, **Task**, **Project Template**, **Timesheet**, vues Gantt et Kanban si disponibles.

Les typologies de projets InovaYa à prévoir sont :

| Type projet | Usage métier |
|---|---|
| IND | Projets industriels ou assimilés. |
| CLIENT / TEE | Projets client liés au traitement de l’eau et des effluents. |
| R&D | Projets de recherche et développement. |
| Digital | Projets digitaux nécessitant notamment une vue Kanban. |
| Interne | Groupes de travail, amélioration continue ou projets internes. |

Si ERPNext permet déjà un champ de typologie projet exploitable, utilise-le. Sinon, crée un **Custom Field léger** sur `Project`, par exemple `inovaya_project_type`, avec les valeurs ci-dessus. Ne crée pas encore de logique automatique de sélection du template : la sélection automatique devra rester dans le backlog de développement futur.

### 3.2 Modèles de projet natifs

Créer ou documenter la création de **Project Templates** pour les typologies ci-dessus. L’objectif est de permettre à InovaYa de démarrer rapidement des projets standards sans développement.

Pour chaque modèle, propose une structure minimale de phases et tâches. Les tâches doivent rester génériques et modifiables par InovaYa. Si le système local ne permet pas d’exporter proprement ces modèles en fixtures, fournis un script d’initialisation idempotent ou une procédure documentée.

| Modèle | Phases indicatives à créer ou proposer |
|---|---|
| CLIENT / TEE | Diagnostic, cadrage, conception, achats/logistique, réalisation, mise en service, clôture. |
| IND | Cadrage industriel, ingénierie, approvisionnement, installation, tests, clôture. |
| R&D | Cadrage hypothèse, expérimentation, analyse, itération, documentation, valorisation. |
| Digital | Cadrage besoin, spécification, développement, recette, déploiement, maintenance. |
| Interne | Cadrage, plan d’action, réalisation, validation, capitalisation. |

### 3.3 Fiche projet et champs de qualification

Configurer la fiche `Project` avec les champs natifs disponibles et, si nécessaire, quelques **Custom Fields légers** destinés à préparer le cadrage InovaYa sans implémenter les futurs modules spécifiques.

Les informations à couvrir sont : client, dates prévues, statut, équipe affectée via les mécanismes natifs, budget estimatif, coût estimatif, lien avec les ventes ou achats si ERPNext le permet nativement, et typologie projet.

Créer uniquement les champs additionnels strictement utiles pour qualifier les projets InovaYa, par exemple :

| Champ proposé | DocType | Type | Justification |
|---|---|---|---|
| `inovaya_project_type` | Project | Select | Typologie projet InovaYa. |
| `inovaya_business_vertical` | Project ou Task | Select / Data | Préparer l’analyse par verticale métier si aucune notion native équivalente n’existe. |
| `inovaya_project_impact_summary` | Project | Small Text | Champ temporaire de synthèse d’impact, sans créer encore de module d’impact. |
| `inovaya_billing_notes` | Project | Small Text | Notes sur les échéances de facturation, sans automatisation de jalon. |

Avant de créer un champ, vérifie qu’un champ natif équivalent n’existe pas. Si un équivalent natif existe, utilise le champ natif et documente le choix.

### 3.4 Suivi des temps natif

Configurer ou documenter l’utilisation du module **Timesheet** pour saisir le temps passé sur les tâches et projets. La granularité à la demi-heure doit être possible par convention d’usage et par documentation, sans développer d’automatisation.

Créer une documentation utilisateur courte expliquant comment :

| Action utilisateur | Couverture attendue |
|---|---|
| Saisir du temps sur un projet ou une tâche | Utilisation native de Timesheet si possible. |
| Relier une saisie de temps à un projet | Utilisation du lien natif vers Project/Task lorsque disponible. |
| Suivre le temps par collaborateur | Utilisation des rapports ou listes natives filtrées. |
| Suivre le temps par projet | Utilisation des rapports ou listes natives filtrées. |

Ne développe pas l’alimentation automatique des timesheets depuis les plannings collaborateurs. Ajoute ce besoin au backlog futur.

### 3.5 Achats et logistique natifs

Configurer l’usage natif des modules **Buying**, **Material Request**, **Supplier**, **Purchase Order** et **Purchase Invoice** avec rattachement au projet lorsque ERPNext le permet.

L’objectif est de permettre à InovaYa de suivre les demandes d’achat, commandes et factures fournisseurs liées à un projet. Si un lien natif vers `Project` existe sur les documents d’achat, l’utiliser. Si le lien à la tâche n’est pas natif, ne pas le développer dans cette phase ; le documenter dans le backlog futur.

Prévoir une documentation de démonstration du flux suivant :

| Étape | Document ERPNext attendu |
|---|---|
| Besoin d’achat projet | Material Request ou document natif équivalent. |
| Commande fournisseur | Purchase Order lié au projet si possible. |
| Réception ou suivi fournisseur | Flux natif ERPNext selon configuration disponible. |
| Facture fournisseur | Purchase Invoice liée au projet si possible. |
| Analyse des coûts | Rapports natifs ou filtres par Project. |

### 3.6 Finance, budget et facturation natifs

Configurer ou documenter l’usage natif des modules **Accounts**, **Budget**, **Cost Center**, **Sales Order**, **Sales Invoice**, **Payment Schedule** si disponibles et pertinents.

L’objectif est de couvrir une première vision standard du suivi financier projet, sans créer encore de jalons de facturation spécifiques liés aux tâches.

Tu dois proposer une structure de base pour :

| Besoin | Approche native-first attendue |
|---|---|
| Budget projet | Utiliser les champs et modules natifs disponibles, notamment Project, Estimated Costing, Budget ou Cost Center selon faisabilité. |
| Dépenses engagées et réalisées | Exploiter Purchase Order, Purchase Invoice et écritures comptables liées au projet si disponibles. |
| Facturation client | Utiliser Sales Order, Sales Invoice et Payment Schedule si pertinent. |
| Statut de paiement | Utiliser les statuts natifs des factures client. |
| Marge et atterrissage | Ne pas développer en phase 1 ; documenter comme backlog futur. |

Si ERPNext impose une structure comptable minimale pour installer ou utiliser ces modules, documente les prérequis sans inventer de données comptables définitives pour InovaYa.

### 3.7 RH et absences natives

Configurer ou documenter l’usage natif de **Employee**, **Leave Application**, **Leave Type** et des fonctions RH disponibles dans ERPNext v16 pour gérer les congés et absences.

Le blocage automatique des tâches projet en cas d’absence n’est pas à développer dans cette phase. Il doit être documenté dans le backlog futur.

### 3.8 Rôles, permissions et cloisonnement

Créer ou configurer les rôles fonctionnels nécessaires dans ERPNext/Frappe, en privilégiant le système natif de rôles et permissions.

Les rôles fonctionnels minimaux sont :

| Rôle InovaYa | Finalité |
|---|---|
| Collaborateur Projet | Consulter ses tâches, saisir ses temps, suivre ses projets affectés. |
| Chef de Projet | Piloter les projets, tâches, temps et éléments financiers associés. |
| Manager | Suivre l’activité de son équipe et les charges via les vues natives disponibles. |
| Responsable GdP | Superviser le portefeuille de projets et les modèles. |
| Responsable Opérations | Superviser les projets opérationnels. |
| Direction Générale | Vue globale et pilotage décisionnel. |
| Finance | Suivre budgets, facturation, paiements et dépenses. |
| Logistique Achats | Suivre demandes d’achat, commandes, fournisseurs et factures fournisseurs. |
| RH | Gérer collaborateurs, absences et alertes RH natives. |

Ne cherche pas à tout verrouiller parfaitement dans cette première itération si cela demande une logique spécifique. Mets en place une matrice de permissions initiale raisonnable et documente les arbitrages à valider avec InovaYa.

### 3.9 Workspaces, tableaux de bord et expérience utilisateur

Créer des **Workspaces** ou pages de navigation Frappe standards pour rendre la démonstration exploitable par InovaYa. Les espaces doivent s’appuyer sur les listes, rapports, vues et dashboards natifs.

Prévoir au minimum :

| Workspace | Contenu attendu |
|---|---|
| InovaYa — Projets | Projects, Tasks, Project Templates, vues Gantt/Kanban si disponibles. |
| InovaYa — Temps | Timesheets, rapports de temps natifs ou listes filtrées. |
| InovaYa — Achats Projet | Material Requests, Purchase Orders, Purchase Invoices filtrables par Project. |
| InovaYa — Finance Projet | Budgets, Sales Orders, Sales Invoices, rapports financiers natifs pertinents. |
| InovaYa — RH / Absences | Employees, Leave Applications, Leave Types. |
| InovaYa — Administration GdP | Paramètres, modèles projet, rôles, documentation de configuration. |

Si certains Workspaces natifs existent déjà, ne les duplique pas inutilement. Tu peux créer un Workspace InovaYa qui agrège des raccourcis vers les modules natifs.

## 4. Backlog obligatoire des développements futurs

Créer un fichier `BACKLOG_DEVELOPPEMENTS_SPECIFIQUES.md` qui liste clairement les besoins non couverts par le natif et qui devront être développés plus tard.

Ce backlog doit au minimum contenir :

| Besoin futur | Raison du report |
|---|---|
| Plan de charge manager hebdomadaire/mensuel consolidé | Vue spécifique non native. |
| Tâches annexes hors projet / espace pôle / “Mon travail” | Modèle métier spécifique à InovaYa. |
| Priorisation automatique Eisenhower | Règle de calcul spécifique. |
| Alimentation automatique des timesheets depuis le planning | Automatisation spécifique. |
| Détection automatique des conflits de charge et planning | Logique complexe de capacité, chevauchement et blocage. |
| Alertes dépassement heures hebdomadaires manager + RH | Calcul périodique et notifications spécifiques. |
| Suivi d’impact projet détaillé | Modèle métier spécifique. |
| Lien achat ou transport vers tâche projet | Lien plus fin que le rattachement projet natif. |
| Demande de transport matériel | Module logistique spécifique si non disponible nativement. |
| Jalons de facturation liés aux tâches | Workflow projet-finance spécifique. |
| Génération automatique de factures depuis jalon validé | Automatisation spécifique. |
| Objectif de marge et atterrissage projet | Calcul financier spécifique InovaYa. |
| Blocage des tâches en cas d’absence | Automatisation RH-projet spécifique. |
| Pages Frappe UI collaborateur, manager et direction | UX spécifique à développer ultérieurement. |

Pour chaque élément du backlog, ajoute une colonne `Priorité proposée`, `Complexité estimée`, `Dépendances ERPNext` et `Questions à valider`.

## 5. Livrables techniques attendus

À la fin de ton intervention, le dépôt doit contenir une base propre, installable et documentée. Tu dois produire les éléments suivants :

| Livrable | Description |
|---|---|
| Application Frappe | App `inovaya_gdp_native` ou nom validé, compatible ERPNext v16. |
| Fixtures ou setup scripts | Rôles, Custom Fields légers, Workspaces, dashboards, modèles ou données de démonstration si exportables proprement. |
| Documentation d’installation | Fichier `README.md` expliquant comment installer l’app sur une instance ERPNext v16 clean. |
| Documentation fonctionnelle | Fichier `CONFIGURATION_NATIVE_FIRST.md` décrivant ce qui est couvert nativement et comment l’utiliser. |
| Matrice de couverture | Fichier `COUVERTURE_NATIVE_ERPNext_V16.md` indiquant pour chaque besoin : natif, paramétrage, champ léger ou backlog. |
| Backlog spécifique | Fichier `BACKLOG_DEVELOPPEMENTS_SPECIFIQUES.md`. |
| Guide de démonstration | Fichier `DEMO_SCENARIO_INOVAYA.md` permettant de montrer un parcours de bout en bout. |
| Tests ou vérifications | Scripts ou checklist permettant de vérifier que l’app s’installe sans erreur et que les principaux objets sont créés. |

## 6. Scénario de démonstration attendu

Prépare un scénario de démonstration simple, basé uniquement sur le natif et le paramétrage léger, permettant de montrer à InovaYa une première chaîne opérationnelle.

Le scénario doit couvrir :

| Étape | Résultat attendu |
|---|---|
| Création d’un projet CLIENT / TEE | Projet qualifié avec typologie, client, dates et budget estimatif. |
| Utilisation d’un modèle projet | Tâches de base créées ou proposées selon les possibilités natives. |
| Affectation de tâches | Collaborateurs associés via les mécanismes standards. |
| Visualisation projet | Vue liste, Gantt ou Kanban si disponible. |
| Saisie des temps | Timesheet liée au projet ou à la tâche. |
| Demande d’achat | Material Request ou Purchase Order rattaché au projet si possible. |
| Facturation client | Sales Order ou Sales Invoice standard avec échéance de paiement si pertinent. |
| Absence collaborateur | Leave Application standard, sans blocage automatique des tâches. |
| Reporting | Consultation des rapports ou listes natives par projet, temps, achats et factures. |

## 7. Méthode de travail attendue

Commence par un audit rapide de l’environnement. Ensuite, propose un plan d’exécution court avant de modifier les fichiers. Si tu rencontres une incertitude bloquante, pose une question avant d’implémenter. Si l’incertitude n’est pas bloquante, fais une hypothèse raisonnable, documente-la et continue.

Applique la méthode suivante :

1. Inspecter la version de Frappe et ERPNext.
2. Vérifier les DocTypes et champs natifs disponibles.
3. Créer l’application Frappe si elle n’existe pas.
4. Ajouter les configurations natives-first et fixtures nécessaires.
5. Ajouter les Custom Fields légers uniquement après vérification d’absence de champ natif équivalent.
6. Créer les Workspaces ou raccourcis de navigation InovaYa.
7. Créer les rôles et une première matrice de permissions.
8. Préparer les modèles projet ou la procédure de création si l’export fixture est fragile.
9. Rédiger les documents de couverture, de démonstration et de backlog.
10. Tester l’installation ou fournir une checklist de test reproductible.

## 8. Critères d’acceptation

La livraison sera considérée comme satisfaisante si :

| Critère | Attendu |
|---|---|
| Installation | L’application s’installe sur une instance ERPNext v16 clean sans erreur documentée. |
| Natif-first | Les modules natifs ERPNext sont utilisés en priorité et les développements spécifiques sont explicitement exclus. |
| Clarté fonctionnelle | InovaYa peut comprendre ce qui est déjà utilisable nativement et ce qui reste à développer. |
| Démonstrabilité | Un scénario simple de démonstration peut être déroulé de bout en bout. |
| Maintenabilité | Les configurations sont versionnées, documentées et reproductibles. |
| Transparence | Les hypothèses, limites et besoins futurs sont clairement indiqués. |

## 9. Contraintes importantes

Ne crée pas une solution qui donne l’illusion que les besoins complexes sont déjà couverts. Par exemple, ne simule pas une détection de conflit de charge si elle n’est pas réellement implémentée. Ne crée pas de code métier partiel non testé pour les fonctions différenciantes. Le but de cette phase est de créer un **socle ERPNext v16 propre**, utile pour cadrer, démontrer et accélérer la suite.

Ne modifie pas le cœur ERPNext ni Frappe. Toute configuration doit passer par une application dédiée, des fixtures, des Custom Fields, des Property Setters documentés ou des scripts d’installation maîtrisés.

## 10. Sortie finale attendue de ta réponse

À la fin, fournis une réponse structurée contenant :

```markdown
# Livraison — InovaYa ERPNext v16 Native First

## 1. Résumé de ce qui a été créé

## 2. Fichiers ajoutés ou modifiés

## 3. Fonctionnalités couvertes par le natif

## 4. Paramétrages et champs légers ajoutés

## 5. Fonctionnalités explicitement reportées en développement spécifique

## 6. Instructions d’installation et de test

## 7. Scénario de démonstration

## 8. Points à valider avec InovaYa
```

Si tu dois poser des questions avant d’agir, limite-toi aux questions réellement bloquantes, par exemple le nom définitif de l’application, l’emplacement du dépôt ou la disponibilité d’une instance ERPNext v16 clean.
