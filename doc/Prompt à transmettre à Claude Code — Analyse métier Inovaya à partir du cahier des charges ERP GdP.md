# Prompt à transmettre à Claude Code — Analyse métier Inovaya à partir du cahier des charges ERP GdP

Tu interviens comme **analyste métier, architecte fonctionnel et assistant de cadrage produit** pour un nouveau projet logiciel relatif à l’entreprise **InovaYa**, spécialisée dans le traitement des eaux et effluents. Tu dois analyser le fichier joint `CAHIERDESCHARGES_ERPGdPsigné.pdf`, qui décrit les besoins d’un **ERP de gestion de projets** destiné à remplacer ou réévaluer l’outil actuel de gestion de projet.

L’objectif de ta mission est de **retrouver, structurer et expliciter tous les aspects métiers nécessaires au fonctionnement de l’entreprise InovaYa**, tels qu’ils apparaissent dans le cahier des charges. Il ne s’agit pas seulement de lister des fonctionnalités techniques, mais de reconstruire la logique métier sous-jacente : les pôles concernés, les rôles, les processus, les objets métiers, les règles de gestion, les interdépendances et les besoins de pilotage.

## 1. Contexte métier à prendre en compte

InovaYa accompagne des acteurs industriels et des collectivités locales sur des projets liés à la préservation de la ressource en eau, depuis le diagnostic jusqu’à la conception et la mise en service d’unités de traitement. L’entreprise mène plusieurs typologies de projets, notamment des projets **IND**, **CLIENT / TEE**, **R&D**, **digitaux** et des projets internes liés à des groupes de travail. L’organisation cherche à standardiser ses pratiques afin d’améliorer la réplicabilité de son activité.

Le futur ERP de gestion de projets doit permettre de centraliser les données projets, d’améliorer la planification, de sécuriser les délais et les budgets, de faciliter la coordination entre les équipes opérationnelles, les managers et les fonctions support, et de fournir un outil fiable de pilotage opérationnel et décisionnel. Il doit également répondre à un besoin de souveraineté.

## 2. Mission principale

À partir du cahier des charges, produis une **analyse métier complète** permettant de comprendre comment InovaYa fonctionne et quelles capacités métier doivent être prises en charge par le futur système. Ton analyse devra distinguer clairement :

| Axe d’analyse | Ce qui est attendu |
|---|---|
| Domaines métier | Identifier les grands domaines concernés, par exemple gestion de projet, planification, suivi des temps, achats/logistique, finance, RH, pilotage et reporting. |
| Acteurs et rôles | Identifier les utilisateurs et parties prenantes : collaborateur, chef de projet, manager, responsable GdP, responsable des opérations, direction générale, RH, finance, logistique/achats. |
| Processus métier | Décrire les processus de bout en bout, par exemple création d’un projet, planification des tâches, affectation des ressources, suivi du réalisé, détection des conflits, pilotage budgétaire, génération de demandes de facturation. |
| Objets métier | Identifier les entités principales : projet, modèle de projet, tâche, ressource, collaborateur, pôle, charge, planning, budget, achat, transport, facture, jalon, absence, alerte, indicateur, impact projet. |
| Règles métier | Extraire les règles de calcul, d’autorisation, d’alerte, de priorité, de disponibilité, de conflit de charge, de suivi budgétaire et de facturation. |
| Interconnexions | Décrire les flux entre ERP GdP, outil de planification individuelle, plan de charge manager, ERP finance, ERP logistique/achats, outil de gestion des absences et futurs outils comme le suivi du parc machines. |
| Besoins de pilotage | Identifier les tableaux de bord, indicateurs, vues consolidées, alertes et besoins décisionnels. |
| Questions ouvertes | Repérer les ambiguïtés, hypothèses à confirmer et points nécessitant un atelier métier. |

## 3. Points métier à extraire impérativement

Ton analyse doit impérativement couvrir les éléments suivants.

### 3.1 Gestion de projet et typologies de projets

Analyse les types de projets mentionnés dans le document, leurs différences potentielles et les implications métier pour le futur ERP. Décris comment les projets doivent être créés à partir de modèles standards générés automatiquement selon la typologie sélectionnée, puis personnalisés par le chef de projet.

Précise les informations nécessaires à la fiche projet, notamment les informations client, contacts clés, équipe projet, budget issu du chiffrage commercial, échéances de facturation, ressources humaines, dates de début et de fin, niveau d’importance des tâches et jalons.

### 3.2 Planification et coordination à trois niveaux

Reconstitue la logique de planification interconnectée entre :

| Niveau | Besoin métier à expliciter |
|---|---|
| Manager | Plan de charge global de l’équipe, visualisations hebdomadaire et mensuelle, ajout de tâches hors projet via un espace pôle, mise à jour dynamique depuis les projets. |
| Projet | Planning détaillé du projet avec tâches, temps alloué, ressources affectées et échéances. |
| Collaborateur | Tableau de bord individuel avec projet associé, temps alloué, échéance, priorité, statut, temps réalisé et possibilité d’ajouter des tâches hors projet. |

Décris les flux de synchronisation entre ces trois niveaux, les impacts d’une modification, et les alertes attendues en cas de modification impactante.

### 3.3 Priorisation des tâches

Formalise la règle métier de priorisation automatique inspirée de la matrice d’Eisenhower. Le niveau de priorité doit être calculé à partir du niveau d’urgence et du niveau d’importance. L’urgence dépend du temps restant avant l’échéance et de la durée de la tâche. L’importance est pilotée manuellement par le chef de projet pour les tâches projet, ou par le collaborateur et/ou son manager pour les tâches hors projet. Précise les rôles habilités à modifier l’importance : responsable GdP, responsable des opérations et direction générale, avec restriction pour les autres responsables de département lorsque la vision globale du projet est requise.

### 3.4 Suivi des temps et charge de travail

Décris les besoins liés au suivi des temps à la demi-heure, à l’alimentation automatique depuis les plannings collaborateurs et aux vues consolidées attendues. Le chef de projet doit pouvoir visualiser les heures dépensées par son équipe projet sur une période donnée. Les managers doivent pouvoir suivre les heures par personne, recevoir des alertes en cas de dépassement du nombre d’heures hebdomadaires, et analyser les heures par typologie de tâche et par verticale métier.

### 3.5 Détection des conflits de planning et de charge

Formalise le mécanisme métier attendu pour détecter automatiquement les conflits de planning et de charge d’un collaborateur, au sein d’un même projet, entre plusieurs projets et avec les tâches annexes. L’outil doit générer une alerte précisant la raison du blocage et suspendre la planification de la tâche jusqu’à résolution du conflit.

### 3.6 Achats, logistique et transport

Analyse le besoin d’interconnexion entre l’ERP de gestion de projets et l’ERP logistique/achats. Décris les objets et flux métier permettant de lier une demande d’achat ou de transport à une tâche projet et à une échéance. Précise les alertes attendues en cas de retard de livraison, changement de statut de commande ou impact sur le planning projet.

### 3.7 Finance, budget et facturation

Décris le suivi budgétaire projet attendu : saisie du budget initial issu du chiffrage commercial, ventilation par typologie d’achat, suivi des dépenses via l’ERP logistique/achats, alertes en cas de dépassement budgétaire et jauges dynamiques de consommation budgétaire.

Décris également le pilotage financier macro : visualisation des dépenses prévisionnelles, engagées et réalisées, saisie de jalons de facturation, lien entre jalons et étapes clés du projet, génération automatique de demandes de facturation après validation d’un jalon, retour de statut des factures, alimentation du suivi budgétaire par les heures, calcul de l’objectif de marge et de l’atterrissage.

### 3.8 RH, absences et disponibilité des ressources

Analyse le besoin de connexion avec l’outil de gestion des absences. Décris la prise en compte automatique des congés dans les plannings, le blocage des périodes indisponibles et les alertes envoyées aux managers et chefs de projet lorsqu’une absence entre en conflit avec une tâche projet existante.

### 3.9 Pilotage, reporting et indicateurs

Identifie les besoins de pilotage pour la responsable de pôle, la direction et les managers. L’outil doit permettre le pilotage de la feuille de route du pôle GdP, l’intégration d’indicateurs de suivi, le suivi d’impact des projets via une page dédiée, ainsi que des vues consolidées sur les ressources, budgets, délais, charges, heures, dépenses et marges.

### 3.10 Sécurité, droits et cloisonnement des accès

Déduis les besoins de droits d’accès et de cloisonnement mentionnés dans le cahier des charges. Propose une première matrice des droits par rôle, en distinguant au minimum les rôles collaborateur, chef de projet, manager, responsable GdP, responsable des opérations, direction générale, RH, finance et logistique/achats.

## 4. Livrables attendus

Produis une réponse structurée en français, en Markdown, avec des tableaux lorsque cela facilite la compréhension. Les livrables attendus sont les suivants :

1. **Synthèse exécutive** des enjeux métiers d’InovaYa.
2. **Cartographie des domaines métier** et de leurs responsabilités.
3. **Cartographie des acteurs et rôles** avec leurs besoins principaux.
4. **Modèle métier conceptuel** listant les objets métier, leurs attributs clés et leurs relations.
5. **Processus métier principaux** sous forme de descriptions séquentielles.
6. **Règles métier détaillées**, notamment priorité, conflit de charge, suivi des temps, budget, facturation et absences.
7. **Flux d’interconnexion** entre les différents outils et ERP.
8. **Tableau des fonctionnalités attendues**, classées par domaine métier et priorité métier.
9. **Matrice indicative des droits d’accès**.
10. **Liste des questions ouvertes** à poser à InovaYa lors d’un atelier de cadrage.
11. **Recommandations pour la suite du projet**, notamment les éléments à transformer en user stories, en modèle de données ou en architecture fonctionnelle.

## 5. Format de sortie souhaité

La réponse doit être rédigée comme un document exploitable par une équipe produit, fonctionnelle et technique. Évite de proposer directement une solution technique avant d’avoir terminé l’analyse métier. Lorsque tu fais une hypothèse, indique clairement qu’il s’agit d’une hypothèse à valider. Ne complète pas les informations manquantes par invention : signale les zones d’incertitude.

Utilise cette structure de sortie :

```markdown
# Analyse métier — InovaYa ERP Gestion de Projets

## 1. Synthèse exécutive

## 2. Domaines métier identifiés

## 3. Acteurs, rôles et responsabilités

## 4. Objets métier et relations

## 5. Processus métier clés

## 6. Règles métier

## 7. Flux et interconnexions entre systèmes

## 8. Fonctionnalités attendues par domaine

## 9. Matrice des droits d’accès

## 10. Indicateurs et besoins de pilotage

## 11. Questions ouvertes et hypothèses à valider

## 12. Recommandations pour la suite
```

## 6. Consigne finale importante

Ton objectif n’est pas seulement de résumer le cahier des charges. Tu dois **reconstruire le fonctionnement métier d’InovaYa** à partir du document, afin de préparer le cadrage d’un futur ERP de gestion de projets. L’analyse doit être suffisamment précise pour pouvoir ensuite servir à produire des user stories, un modèle de données, des diagrammes de processus, une matrice de permissions et une architecture fonctionnelle.
