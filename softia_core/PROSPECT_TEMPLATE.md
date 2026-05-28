# PROSPECT_TEMPLATE.md — Template analyse CDC
# Version : 1.0 — Mai 2026
# Usage : copier ce fichier, renommer en ANALYSE_[NOM_PROSPECT].md
# Remplir les sections marquées [À COMPLÉTER]

---

## 0. Instructions pour Claude Code

Lis ce fichier de haut en bas.
Lis ensuite CLAUDE.md et ERPNEXT_V16_REALITY.md.
Puis exécute le pipeline dans l'ordre des sections.

---

## 1. Contexte prospect

**Nom prospect :** [À COMPLÉTER]
**Secteur :** [À COMPLÉTER]
**Outil actuel :** [À COMPLÉTER — ex: Monday, Excel, Odoo]
**Objectif principal :** [À COMPLÉTER en 1 phrase]
**CDC fourni :** [À COMPLÉTER — nom du fichier PDF/Word]

---

## 2. Contraintes techniques

**Version ERPNext cible :** v16
**Modules ERPNext requis :** [À COMPLÉTER — ex: HR, Buying, Accounts]
**Outil RH absences :** [À COMPLÉTER — ERPNext HR / Lucca / Payfit / Autre]
**ERP Finance :** [À COMPLÉTER — même instance ERPNext / outil externe]
**Hébergement :** Frappe Cloud — site dédié
**Nom de l'app :** [À COMPLÉTER — ex: prospect_gdp]
**Nom du module :** [À COMPLÉTER — ex: "ProspectGdP" — JAMAIS le même scrub que l'app]

---

## 3. Matrice de couverture CDC

> À remplir par Claude Code après lecture du CDC.
> Légende : N = Natif | P = Paramétrage | S = Spécifique custom

| # | Fonctionnalité CDC | Couverture | Module ERPNext | Notes |
|---|---|---|---|---|
| A1 | [À COMPLÉTER] | N/P/S | | |
| A2 | | | | |
| ... | | | | |

**Synthèse :**
- Natif (N) : X fonctionnalités
- Paramétrage (P) : X fonctionnalités
- Spécifique (S) : X fonctionnalités

---

## 4. Backlog priorisé

> À générer par Claude Code depuis la matrice de couverture.
> Format identique au backlog InovaYa pour cohérence Softia.

| # | Fonctionnalité | Priorité | Complexité | Dépendances | Questions ouvertes |
|---|---|---|---|---|---|
| B01 | | Haute/Moyenne/Basse | Très haute/Haute/Moyenne/Faible | | |
| B02 | | | | | |
| ... | | | | | |

**Ordre de développement recommandé :**
```
Sprint 1 : [items faible complexité, sans dépendances]
Sprint 2 : [items moyenne complexité]
Sprint 3 : [items haute complexité]
Sprint 4 : [interfaces Vue.js — après validation maquettes client]
```

---

## 5. Questions bloquantes

> Ces questions doivent être répondues par le prospect AVANT le développement.
> Claude Code ne peut pas les trancher seul.

| # | Question | Impact si non répondue | Hypothèse par défaut |
|---|---|---|---|
| Q1 | | | |
| Q2 | | | |
| ... | | | |

---

## 6. Hypothèses prises

> Claude Code documente ici les hypothèses prises pour les items
> dont les questions sont ouvertes.
> À valider avec le prospect avant la mise en production.

| # | Hypothèse | Item concerné | Risque si fausse |
|---|---|---|---|
| H1 | | | |
| H2 | | | |
| ... | | | |

---

## 7. Fixtures socle à créer

> Liste des données de configuration à créer en fixtures.

### Rôles
```json
[À COMPLÉTER — liste des rôles métier du prospect]
```

### Types de projets
```
[À COMPLÉTER — ex: IND, CLIENT, R&D, Digital, Interne]
```

### Templates de projet
```
[À COMPLÉTER — un template par type avec phases standard]
```

### Workspaces
```
[À COMPLÉTER — espaces de travail par profil utilisateur]
```

---

## 8. Commandes de démarrage

> À exécuter par Claude Code une fois ce fichier complété.

```bash
# 1. Créer le dépôt GitHub
# Créer manuellement sur github.com/AlexandreXu/[nom_app]

# 2. Initialiser l'app Frappe
cd ~/frappe-bench-inovaya/apps
bench new-app [nom_app]

# 3. Installer sur le site de dev
bench --site inovaya.localhost install-app [nom_app]

# 4. Développer sprint par sprint
# Suivre l'ordre du backlog section 4
```

---

## 9. Checklist de livraison

> À compléter par Claude Code à la fin de chaque sprint.

- [ ] Tous les items du sprint sont développés
- [ ] Tests console passent (counts fixtures corrects)
- [ ] Scénario fonctionnel de base validé (créer un projet depuis template)
- [ ] Commités et poussés sur GitHub
- [ ] RAPPORT_LIVRAISON.md mis à jour
- [ ] Questions ouvertes documentées dans section 5
