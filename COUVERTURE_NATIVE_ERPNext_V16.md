# Matrice de couverture — InovaYa GdP vs ERPNext v16

Légende : ✅ Natif complet | ⚠️ Natif partiel / paramétrage | ❌ Non natif → Phase 2

---

## A — Coordination générale & planification

| # | Besoin CDC | Couverture | Implémentation Phase 1 | Backlog |
|---|---|---|---|---|
| A1 | Plan de charge manager (hebdo/mensuel) | ❌ | — | B01 |
| A2 | Espace "Pôle" — tâches hors projet pour équipes | ❌ | — | B02 |
| A3 | Tableau de bord collaborateur (priorité, temps alloué, statut) | ❌ | Vue Liste filtrée par "Assigné à" | B03, B24 |
| A4 | Tâches "Mon Travail" hors projet | ❌ | ToDo natif (déconnecté du projet) | B02 |
| A5 | Priorisation automatique Eisenhower | ❌ | Champ Priority natif (manuel Low/Medium/High/Urgent) | B04 |
| A6 | Suivi des heures à la demi-heure | ✅ | Timesheet natif — convention 0,5h | — |
| A7 | Alimentation automatique timesheets depuis planning | ❌ | Saisie manuelle documentée | B06 |
| A8 | Vue consolidée heures — chef de projet | ⚠️ | Daily Timesheet Summary filtré par projet | B03 |
| A9 | Vue consolidée heures — manager par verticale | ⚠️ | Champ `inovaya_task_vertical` créé + rapport à construire | B08 |
| A10 | Alertes dépassement heures hebdomadaires | ❌ | — | B07 |
| A11 | Feuille de route Pôle GdP | ❌ | Workspace "InovaYa Projets" comme substitut temporaire | B09 |
| A12 | Suivi d'impact des projets | ❌ | Champ `inovaya_project_impact_summary` (texte libre) | B10 |

## B — Coordination projet

| # | Besoin CDC | Couverture | Implémentation Phase 1 | Backlog |
|---|---|---|---|---|
| B1 | Modèles auto-générés par typologie | ⚠️ | 5 templates créés — sélection manuelle | B11 |
| B2 | Modification autonome des modèles | ✅ | Project Template modifiable sans code | — |
| B3 | Fiche projet complète (client, équipe, budget, jalons) | ⚠️ | Champs natifs + 3 champs custom InovaYa | B15, B18 |
| B4 | Planning multi-vues auto-généré | ⚠️ | Liste + Gantt + Kanban natifs | B03 |
| B5 | Détection conflits de planning/charge | ❌ | — | B05 |
| B6 | Vue Kanban | ✅ | Kanban natif sur Task | — |

## C — Logistique / Achats

| # | Besoin CDC | Couverture | Implémentation Phase 1 | Backlog |
|---|---|---|---|---|
| C1 | Lien achat ↔ tâche projet (granularité tâche) | ⚠️ | Lien achat ↔ projet natif ; lien tâche absent | B12 |
| C2 | Alertes retard commande → impact planning | ❌ | — | B14 |
| C3 | Lien transport ↔ tâche projet | ❌ | — | B13 |

## D — Finance / Budget

| # | Besoin CDC | Couverture | Implémentation Phase 1 | Backlog |
|---|---|---|---|---|
| D1 | Budget initial ventilé par type d'achat | ⚠️ | Champ `estimated_costing` natif (global) | B15 |
| D2 | Suivi dépenses via ERP achats | ⚠️ | PO + PI liées au projet (si même instance) | B16 |
| D3 | Alertes dépassement + jauges dynamiques | ⚠️ | Module Budget ERPNext par Cost Center | B17 |
| D4 | Vue prévu/engagé/réalisé | ❌ | — | B16 |
| D5 | Jalons de facturation liés aux tâches | ⚠️ | Payment Schedule sur Sales Order (sans lien tâche) | B18 |
| D6 | Génération auto facture depuis jalon validé | ❌ | Création manuelle Sales Invoice | B19 |
| D7 | Retour statut factures dans vue projet | ⚠️ | Statut natif Sales Invoice consultable | B18 |
| D8 | Alimentation budget par heures (coût ETP) | ❌ | — | B20 |
| D9 | Calcul marge et atterrissage | ❌ | — | B21 |

## E — RH / Absences

| # | Besoin CDC | Couverture | Implémentation Phase 1 | Backlog |
|---|---|---|---|---|
| E1 | Prise en compte auto congés dans plannings | ❌ | Leave Application indépendante du Project | B22 |
| E2 | Blocage périodes indisponibles | ❌ | — | B22 |
| E3 | Alertes manager + chef de projet (conflit congé/tâche) | ❌ | — | B23 |

## F — Interconnexions

| # | Besoin CDC | Couverture | Implémentation Phase 1 | Backlog |
|---|---|---|---|---|
| F1 | ERP GdP ↔ Planification individuelle | ✅ | Natif si même instance ERPNext | — |
| F2 | ERP GdP ↔ Plan de charge Manager | ⚠️ | Données disponibles, vue dédiée absente | B01 |
| F3 | ERP GdP ↔ ERP Finance | ✅ | Natif si même instance ERPNext | — |
| F4 | ERP GdP ↔ ERP Logistique/Achats | ✅ | Natif si même instance ERPNext | — |
| F5 | ERP GdP ↔ Outil gestion absences externe | ⚠️ | Natif si ERPNext HR ; API REST si outil externe | — |
| F6 | Architecture ouverte (futur parc machines) | ✅ | API REST + Webhooks Frappe natifs | — |

## G — Droits d'accès

| # | Besoin CDC | Couverture | Implémentation Phase 1 | Backlog |
|---|---|---|---|---|
| G1 | Cloisonnement par rôle | ✅ | 9 rôles InovaYa créés via fixtures | — |
| G2 | Restriction modification "Importance" tâche | ⚠️ | Champ Priority natif — permission par champ à configurer | B04 |

## H — Transversal

| # | Besoin CDC | Couverture | Implémentation Phase 1 | Backlog |
|---|---|---|---|---|
| H1 | Souveraineté numérique | ✅ | ERPNext open source, auto-hébergeable | — |
| H2 | Autonomie de paramétrage InovaYa | ✅ | Templates, champs, workflows modifiables sans code | — |
| H3 | Ergonomie et adoption | ⚠️ | Workspaces InovaYa dédiés — UX avancée Phase 2 | B24, B25, B26 |

---

## Synthèse

| Statut | Nombre |
|---|---|
| ✅ Natif complet | 10 |
| ⚠️ Natif partiel | 14 |
| ❌ Non natif (Phase 2) | 20 |
| **Total** | **44** |
