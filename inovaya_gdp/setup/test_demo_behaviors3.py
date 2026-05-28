"""
Test ciblé — contourne les permissions DocType (qui bloquent bench execute)
et teste directement la logique métier des hooks B04 et B05.

bench --site inovaya.localhost execute inovaya_gdp.setup.test_demo_behaviors3.run
"""
import frappe
import json

TASK_CHIFFRAGE   = "TASK-2026-00109"   # Chiffrage & validation — TEE-026
TASK_FABRICATION = "TASK-2026-00121"   # Fabrication module IND — IND-014


def _sep(title):
    print(f"\n{'='*65}\n{title}\n{'='*65}")


def _get_roles(user):
    """Retourne les rôles d'un utilisateur (hors All/Guest)."""
    roles = frappe.get_roles(user)
    return [r for r in roles if r not in ("All", "Guest")]


def _simulate_guard(user, task_name, new_importance):
    """
    Simule _guard_importance_change exactement comme le ferait un save UI :
    - Charge le doc courant (état en DB = "avant save")
    - Simule la modification du champ
    - Exécute la garde avec le bon _doc_before_save
    """
    from inovaya_gdp.overrides.task import _guard_importance_change, ALLOWED_ROLES_IMPORTANCE

    original_user = frappe.session.user
    try:
        frappe.set_user(user)

        # Charger le doc "avant save" (état DB actuel)
        doc_before = frappe.get_doc("Task", task_name)

        # Créer le doc "modifié" (ce que l'UI enverrait)
        doc = frappe.get_doc("Task", task_name)
        doc.inovaya_importance = new_importance
        doc._doc_before_save = doc_before   # simuler ce que Frappe set avant before_save

        try:
            _guard_importance_change(doc)
            return "OK", doc.inovaya_eisenhower_info if hasattr(doc, "inovaya_eisenhower_info") else None
        except frappe.exceptions.ValidationError as e:
            return "BLOQUE", str(e).replace("<br>", " | ")
    finally:
        frappe.set_user(original_user)


def _simulate_b05(task_name, new_hours, user="camille.roux@inovaya.com"):
    """
    Simule _check_planning_conflicts avec la valeur hours_per_day modifiée.
    """
    from inovaya_gdp.overrides.task import _check_planning_conflicts

    original_user = frappe.session.user
    try:
        frappe.set_user(user)
        doc = frappe.get_doc("Task", task_name)
        doc.inovaya_hours_per_day = new_hours
        # frappe.flags.in_test est FALSE ici → B05 s'exécute
        try:
            _check_planning_conflicts(doc)
            return "OK"
        except frappe.exceptions.ValidationError as e:
            return str(e).replace("<br>", "\n     ")
    finally:
        frappe.set_user(original_user)


def run():
    # ══════════════════════════════════════════════════════════════════════
    # CONTEXTE — rôles des utilisateurs
    # ══════════════════════════════════════════════════════════════════════
    _sep("CONTEXTE — RÔLES UTILISATEURS")
    for user in ["lea.martin@inovaya.com", "camille.roux@inovaya.com"]:
        roles = _get_roles(user)
        print(f"  {user:<40} : {', '.join(roles)}")

    from inovaya_gdp.overrides.task import ALLOWED_ROLES_IMPORTANCE
    print(f"\n  Rôles autorisés B04 : {', '.join(sorted(ALLOWED_ROLES_IMPORTANCE))}")

    lea_roles     = set(_get_roles("lea.martin@inovaya.com"))
    camille_roles = set(_get_roles("camille.roux@inovaya.com"))
    lea_auth     = bool(ALLOWED_ROLES_IMPORTANCE & lea_roles)
    camille_auth = bool(ALLOWED_ROLES_IMPORTANCE & camille_roles)
    print(f"  Léa autorisée       : {'OUI' if lea_auth else 'NON'}")
    print(f"  Camille autorisée   : {'OUI' if camille_auth else 'NON'}")

    # ══════════════════════════════════════════════════════════════════════
    # TEST 1 — CLOISONNEMENT B04
    # ══════════════════════════════════════════════════════════════════════
    _sep("TEST 1 — CLOISONNEMENT B04")

    print("\n[1a] Champ inovaya_importance dans l'UI :")
    cf = frappe.db.get_value("Custom Field", "Task-inovaya_importance",
                             ["read_only", "hidden", "permlevel"], as_dict=True)
    ro, hl, pl = int(cf.read_only or 0), int(cf.hidden or 0), int(cf.permlevel or 0)
    print(f"     read_only={ro}  hidden={hl}  permlevel={pl}")
    if hl:
        verdict = "(c) INVISIBLE — cloisonnement non visible"
    elif ro:
        verdict = "(a) READ-ONLY pour tous"
    else:
        verdict = "(b) ÉDITABLE par tous — blocage au save via hook"
    print(f"     → Comportement UI : {verdict}")

    print(f"\n[1b] Simulation Léa — tente Basse → Haute :")
    status, detail = _simulate_guard("lea.martin@inovaya.com", TASK_CHIFFRAGE, "Haute")
    if status == "BLOQUE":
        print(f"  ✅ BLOQUÉ → message :")
        print(f"     {detail[:300]}")
    else:
        print(f"  ⚠ Non bloqué (detail: {detail})")

    print(f"\n[1c] Simulation Camille — tente Basse → Haute :")
    status2, detail2 = _simulate_guard("camille.roux@inovaya.com", TASK_CHIFFRAGE, "Haute")
    if status2 == "OK":
        from inovaya_gdp.overrides.task import _run_eisenhower
        # vérifier le quadrant après passage par Eisenhower
        doc = frappe.get_doc("Task", TASK_CHIFFRAGE)
        doc.inovaya_importance = "Haute"
        doc._doc_before_save = frappe.get_doc("Task", TASK_CHIFFRAGE)
        _run_eisenhower(doc)
        print(f"  ✅ AUTORISÉ")
        print(f"     Quadrant calculé : {doc.inovaya_eisenhower_info}")
        print(f"     Priorité calculée : {doc.priority}")
    else:
        print(f"  ❌ Bloqué inattendu pour Camille : {detail2}")

    # ══════════════════════════════════════════════════════════════════════
    # TEST 2 — DÉCLENCHEMENT B05
    # ══════════════════════════════════════════════════════════════════════
    _sep("TEST 2 — DÉCLENCHEMENT B05")

    print("\n[2a] Vérification des tâches Léa en chevauchement :")
    t_fab = frappe.db.get_value("Task", TASK_FABRICATION,
                                 ["subject", "exp_start_date", "exp_end_date",
                                  "inovaya_hours_per_day", "_assign"], as_dict=True)
    t_real = frappe.db.get_value("Task", "TASK-2026-00110",
                                  ["subject", "exp_start_date", "exp_end_date",
                                   "inovaya_hours_per_day", "_assign"], as_dict=True)

    for label, t in [("Fabrication IND  (IND-014)", t_fab),
                     ("Réalisation Asm  (TEE-026)", t_real)]:
        assigns = json.loads(t._assign or "[]") if t else []
        s = str(t.exp_start_date)[:10] if t and t.exp_start_date else "—"
        e = str(t.exp_end_date)[:10]   if t and t.exp_end_date   else "—"
        print(f"  {label} : {t.inovaya_hours_per_day}h/j | {s}→{e} | {', '.join(assigns)}")

    chevauch = "2026-06-17 → 2026-06-24"
    cumul    = (t_fab.inovaya_hours_per_day or 8) + (t_real.inovaya_hours_per_day or 6)
    print(f"\n  Chevauchement : {chevauch}")
    print(f"  Charge cumulée Léa : {t_fab.inovaya_hours_per_day}h + {t_real.inovaya_hours_per_day}h = {cumul}h/j")

    print(f"\n[2b] Form non-dirty dans l'UI :")
    print("  → Frappe ne POST pas si aucun champ modifié.")
    print("  → B05 ne se déclenche PAS sur un Save 'à vide'.")
    print("  → L'animateur DOIT changer un champ pour rendre la form dirty.")

    print(f"\n[2c] Simulation : hours_per_day 8 → 9 (Camille sauvegarde) :")
    result_9 = _simulate_b05(TASK_FABRICATION, 9.0)
    if result_9 == "OK":
        print("  ⚠ Pas de blocage")
    else:
        print("  ✅ B05 déclenché :")
        for line in result_9.split("\n"):
            print(f"     {line}")

    print(f"\n[2d] Simulation : hours_per_day 8 → 2 (résolution) :")
    result_2 = _simulate_b05(TASK_FABRICATION, 2.0)
    if result_2 == "OK":
        print("  ✅ Aucune erreur — 2+6=8 ≤ 8 : save autorisé")
    else:
        print(f"  ❌ Erreur inattendue :\n     {result_2[:200]}")

    print(f"\n[2e] frappe.flags.in_test dans l'UI (context de la démo) :")
    print(f"  Valeur actuelle in_test = {frappe.flags.in_test}")
    print("  Dans l'UI web, in_test=False → B05 s'exécute TOUJOURS.")
    print("  in_test=True uniquement lors des bench execute avec le flag explicite.")

    # ══════════════════════════════════════════════════════════════════════
    _sep("SYNTHÈSE FINALE")
    print("""
SÉQUENCE 1 — B04 Eisenhower
  ┌─ Compte Léa ──────────────────────────────────────────────────────
  │  URL : http://inovaya.localhost:8002/task/TASK-2026-00109
  │  Action : changer inovaya_importance → Haute → Sauvegarder
  │  Résultat attendu : ERREUR "Permission insuffisante — B04"
  │  → le champ est visible et modifiable, mais le hook bloque au save
  └────────────────────────────────────────────────────────────────────
  ┌─ Compte Camille ──────────────────────────────────────────────────
  │  URL : http://inovaya.localhost:8002/task/TASK-2026-00109
  │  Action : changer inovaya_importance → Haute → Sauvegarder
  │  Résultat attendu : OK — quadrant passe Q4 → Q2 (vert "High")
  └────────────────────────────────────────────────────────────────────

SÉQUENCE 2 — B05 Conflits de charge
  ┌─ Compte Camille ──────────────────────────────────────────────────
  │  URL : http://inovaya.localhost:8002/task/TASK-2026-00121
  │  Action 1 : Montrer heures/jour=8, Léa assignée, 17/06→24/06
  │  Action 2 : Changer inovaya_hours_per_day : 8 → 9 → Sauvegarder
  │  Résultat : ERREUR "9h + 6h = 15h/j > 8h — du 17/06 au 08/07"
  │  Action 3 : Changer inovaya_hours_per_day : 9 → 2 → Sauvegarder
  │  Résultat : OK (2+6=8 ≤ 8)
  └────────────────────────────────────────────────────────────────────
""")
