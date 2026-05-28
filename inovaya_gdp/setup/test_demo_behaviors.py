"""
Vérifie les deux comportements clés avant la démo :

TEST 1 — Cloisonnement B04 (Eisenhower)
  → Simule Léa tentant de passer importance Basse→Haute sur TASK-2026-00109
  → Simule Camille faisant la même chose

TEST 2 — Déclenchement B05 (conflits de charge)
  → Teste si un save "à vide" (form non modifiée) est possible depuis l'UI
  → Teste le déclenchement réel avec hook before_save

bench --site inovaya.localhost execute inovaya_gdp.setup.test_demo_behaviors.run
"""
import frappe
from frappe.exceptions import ValidationError

TASK_CHIFFRAGE = "TASK-2026-00109"   # Chiffrage & validation — TEE-026
TASK_FABRICATION = "TASK-2026-00121" # Fabrication module IND — IND-014


def _section(title):
    print("\n" + "=" * 65)
    print(title)
    print("=" * 65)


def test_b04_cloisonnement():
    _section("TEST 1 — CLOISONNEMENT B04 (Eisenhower)")

    # ── Vérification du champ dans la fixture ──────────────────────────────
    print("\n[1a] Attributs du champ inovaya_importance sur Task :")
    cf = frappe.db.get_value(
        "Custom Field",
        "Task-inovaya_importance",
        ["fieldtype", "read_only", "permlevel", "hidden"],
        as_dict=True,
    )
    if cf:
        print(f"  fieldtype  : {cf.fieldtype}")
        print(f"  read_only  : {cf.read_only}   (0=éditable, 1=lecture seule)")
        print(f"  permlevel  : {cf.permlevel}   (0=tous, 1+=restreint)")
        print(f"  hidden     : {cf.hidden}")
        ro  = int(cf.read_only  or 0)
        hl  = int(cf.hidden     or 0)
        pl  = int(cf.permlevel  or 0)
        if hl:
            verdict = "c) INVISIBLE — ⚠ cloisonnement non visible"
        elif ro:
            verdict = "a) READ-ONLY pour tous — le cloisonnement est visuel (non-modifiable)"
        elif pl > 0:
            verdict = "a/b) PERMLEVEL — seuls les rôles avec write_permlevel peuvent modifier"
        else:
            verdict = "b) ÉDITABLE par tous — blocage uniquement au save (hook before_save)"
        print(f"\n  → VERDICT UI : {verdict}")
    else:
        print("  ❌ Custom Field 'Task-inovaya_importance' introuvable")

    # ── Simulation : Léa tente de changer importance (hook before_save) ───
    print("\n[1b] Simulation Léa (lea.martin) : Basse → Haute → save")
    original_user = frappe.session.user
    try:
        frappe.set_user("lea.martin@inovaya.com")
        task = frappe.get_doc("Task", TASK_CHIFFRAGE)
        task.inovaya_importance = "Haute"
        task.flags.ignore_permissions = False  # simuler droits réels Léa
        try:
            # Appel direct du hook (simule exactly ce que before_save fait)
            from inovaya_gdp.overrides.task import before_save
            before_save(task)
            print("  ⚠ Aucune erreur levée — blocage non déclenché")
        except frappe.exceptions.ValidationError as e:
            msg = str(e).replace("<br>", " | ").replace("\n", " ")
            print(f"  ✅ Erreur levée (comportement b) :")
            print(f"     {msg[:200]}")
    finally:
        frappe.set_user(original_user)

    # ── Simulation : Camille tente la même chose ───────────────────────────
    print("\n[1c] Simulation Camille (camille.roux) : Basse → Haute → save")
    try:
        frappe.set_user("camille.roux@inovaya.com")
        task2 = frappe.get_doc("Task", TASK_CHIFFRAGE)
        task2.inovaya_importance = "Haute"
        try:
            from inovaya_gdp.overrides.task import before_save
            before_save(task2)
            print(f"  ✅ Aucune erreur — Camille peut modifier (rôle Responsable GdP autorisé)")
            print(f"     Quadrant recalculé : {task2.inovaya_eisenhower_info}")
        except frappe.exceptions.ValidationError as e:
            print(f"  ❌ Erreur inattendue pour Camille : {e}")
    finally:
        frappe.set_user(original_user)


def test_b05_declenchement():
    _section("TEST 2 — DÉCLENCHEMENT B05 (conflits de charge)")

    # ── Rappel des dates en place ─────────────────────────────────────────
    print("\n[2a] Vérification de l'état des tâches :")
    for task_name in [TASK_FABRICATION, "TASK-2026-00110"]:
        t = frappe.db.get_value(
            "Task", task_name,
            ["subject", "exp_start_date", "exp_end_date",
             "inovaya_hours_per_day", "_assign"],
            as_dict=True,
        )
        import json
        assigns = json.loads(t._assign or "[]") if t else []
        start = str(t.exp_start_date)[:10] if t and t.exp_start_date else "—"
        end   = str(t.exp_end_date)[:10]   if t and t.exp_end_date   else "—"
        print(f"  {task_name} | {t.subject[:35]:<35} | {t.inovaya_hours_per_day}h/j | {start}→{end} | {', '.join(assigns)}")

    # ── Test A : save sans modification (simule form non-dirty) ───────────
    print("\n[2b] Test A — save à vide (form non modifiée) :")
    print("  ℹ Dans l'UI Frappe, si aucun champ n'est modifié,")
    print("    le bouton Save n'envoie PAS de requête au serveur.")
    print("    → before_save NE se déclenche PAS.")
    print("    → B05 ne peut pas être activé sans modification d'un champ.")
    print("  → Action démo nécessaire : modifier au moins un champ pour rendre la form 'dirty'.")

    # ── Test B : sauvegarder avec inovaya_hours_per_day = 9 ──────────────
    print("\n[2c] Test B — hours_per_day : 8 → 9 (simulation hook) :")
    original_user = frappe.session.user
    try:
        frappe.set_user("camille.roux@inovaya.com")
        task = frappe.get_doc("Task", TASK_FABRICATION)
        task.inovaya_hours_per_day = 9.0
        try:
            from inovaya_gdp.overrides.task import before_save
            before_save(task)
            print("  ⚠ Aucune erreur — B05 non déclenché")
        except frappe.exceptions.ValidationError as e:
            msg = str(e).replace("<br>", "\n     ")
            print(f"  ✅ B05 déclenché (9+6=15 > 8) :\n     {msg[:400]}")
    finally:
        frappe.set_user(original_user)

    # ── Test C : sauvegarder avec inovaya_hours_per_day = 2 ──────────────
    print("\n[2d] Test C — hours_per_day : 8 → 2 (résolution) :")
    try:
        frappe.set_user("camille.roux@inovaya.com")
        task = frappe.get_doc("Task", TASK_FABRICATION)
        task.inovaya_hours_per_day = 2.0
        try:
            from inovaya_gdp.overrides.task import before_save
            before_save(task)
            print("  ✅ Aucune erreur — 2+6=8 ≤ 8 : save autorisé")
        except frappe.exceptions.ValidationError as e:
            print(f"  ❌ Erreur inattendue : {e}")
    finally:
        frappe.set_user(original_user)

    # ── Synthèse séquence démo recommandée ───────────────────────────────
    print("\n[2e] SÉQUENCE DÉMO RECOMMANDÉE pour B05 :")
    print("  Action 1 : Ouvrir TASK-2026-00121 (Fabrication module IND)")
    print("             → Montrer : heures/jour = 8, Léa assignée, 17/06→24/06")
    print("  Action 2 : Changer 'Heures / jour allouées' de 8 → 9")
    print("             (commentaire : 'Je valide la charge à 9h/j pour cette tâche')")
    print("  Action 3 : Cliquer Sauvegarder")
    print("             → RÉSULTAT : erreur B05 '9h + 6h = 15h/j > 8h'")
    print("  Action 4 : Changer 'Heures / jour allouées' de 9 → 2")
    print("             (commentaire : 'Je réalloue à 2h/j')")
    print("  Action 5 : Cliquer Sauvegarder")
    print("             → RÉSULTAT : save OK, aucune erreur")
    print()
    print("  OU (alternative — plus direct) :")
    print("  Action 2bis : Changer description (ajouter un mot)")
    print("  Action 3bis : Cliquer Sauvegarder")
    print("                → erreur B05 '8h + 6h = 14h/j > 8h'")
    print("  Action 4bis : Changer heures_per_day de 8 → 2, Sauvegarder → OK")


def run():
    test_b04_cloisonnement()
    test_b05_declenchement()

    print("\n" + "=" * 65)
    print("FIN DES TESTS — voir résultats ci-dessus")
    print("=" * 65)
