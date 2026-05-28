"""
Test corrigé — simule exactement le workflow UI (doc.save() complet avec _doc_before_save).

TEST 1 : Cloisonnement B04 → utilise task.save() après set_user, pas before_save direct
TEST 2 : Déclenchement B05 → utilise task.save() avec valeur modifiée

bench --site inovaya.localhost execute inovaya_gdp.setup.test_demo_behaviors2.run
"""
import frappe
from frappe.exceptions import ValidationError

TASK_CHIFFRAGE   = "TASK-2026-00109"   # Chiffrage & validation — TEE-026
TASK_FABRICATION = "TASK-2026-00121"   # Fabrication module IND — IND-014


def _sep(title):
    print(f"\n{'='*65}\n{title}\n{'='*65}")


def run():
    original_user = frappe.session.user

    # ══════════════════════════════════════════════════════════════════════
    # TEST 1 — CLOISONNEMENT B04
    # ══════════════════════════════════════════════════════════════════════
    _sep("TEST 1 — CLOISONNEMENT B04 (Eisenhower)")

    # ── 1a : attribut read_only du champ ─────────────────────────────────
    cf = frappe.db.get_value(
        "Custom Field", "Task-inovaya_importance",
        ["read_only", "hidden", "permlevel"], as_dict=True
    )
    ro = int(cf.read_only or 0) if cf else 0
    hl = int(cf.hidden    or 0) if cf else 0
    pl = int(cf.permlevel or 0) if cf else 0
    print(f"\n  Champ inovaya_importance : read_only={ro} hidden={hl} permlevel={pl}")

    if hl:
        print("  → (c) INVISIBLE — ⚠ cloisonnement non visible dans l'UI")
    elif ro:
        print("  → (a) READ-ONLY dans l'UI pour tous les rôles")
    elif pl > 0:
        print(f"  → (a/b) permlevel={pl} — visible, modifiable selon perms de rôle")
    else:
        print("  → (b) ÉDITABLE dans l'UI — blocage uniquement au save (hook)")

    # ── 1b : simulation Léa avec doc.save() complet ──────────────────────
    print("\n[1b] Simulation Léa — doc.save() complet :")
    try:
        frappe.set_user("lea.martin@inovaya.com")

        # Lire valeur actuelle
        cur_imp = frappe.db.get_value("Task", TASK_CHIFFRAGE, "inovaya_importance")
        print(f"     Importance actuelle : {cur_imp!r}")

        task = frappe.get_doc("Task", TASK_CHIFFRAGE)
        task.inovaya_importance = "Haute"

        try:
            task.save(ignore_permissions=False)   # simule UI : sans ignore_permissions
            # Rollback pour ne pas altérer les données démo
            frappe.db.rollback()
            print("  ⚠ Save OK pour Léa — blocage non déclenché")
        except frappe.exceptions.ValidationError as e:
            frappe.db.rollback()
            msg = str(e).replace("<br>", " · ").strip()
            print(f"  ✅ Erreur levée pour Léa (comportement b) :")
            print(f"     {msg[:300]}")
        except Exception as e:
            frappe.db.rollback()
            print(f"  ❓ Autre erreur : {type(e).__name__}: {e}")
    finally:
        frappe.set_user(original_user)

    # ── 1c : simulation Camille avec doc.save() complet ──────────────────
    print("\n[1c] Simulation Camille — doc.save() complet :")
    try:
        frappe.set_user("camille.roux@inovaya.com")
        task2 = frappe.get_doc("Task", TASK_CHIFFRAGE)
        task2.inovaya_importance = "Haute"
        try:
            task2.save(ignore_permissions=False)
            frappe.db.commit()
            q = frappe.db.get_value("Task", TASK_CHIFFRAGE, "inovaya_eisenhower_info")
            print(f"  ✅ Save OK pour Camille (Responsable GdP)")
            print(f"     Quadrant après sauvegarde : {q}")
        except frappe.exceptions.ValidationError as e:
            frappe.db.rollback()
            print(f"  ❌ Erreur inattendue pour Camille : {e}")
        except Exception as e:
            frappe.db.rollback()
            print(f"  ❓ Autre erreur : {type(e).__name__}: {e}")
    finally:
        frappe.set_user(original_user)

    # Reset "Chiffrage" → Basse + recalcul B04
    frappe.db.set_value("Task", TASK_CHIFFRAGE, "inovaya_importance", "Basse", update_modified=False)
    frappe.db.set_value("Task", TASK_CHIFFRAGE, "inovaya_eisenhower_info",
                        "Non urgente · Q4 — Reporter / Éliminer", update_modified=False)
    frappe.db.commit()
    print("     [données remises en état initial — Basse / Q4]")

    # ══════════════════════════════════════════════════════════════════════
    # TEST 2 — DÉCLENCHEMENT B05
    # ══════════════════════════════════════════════════════════════════════
    _sep("TEST 2 — DÉCLENCHEMENT B05 (conflits de charge)")

    # ── 2a : form non modifiée dans l'UI ─────────────────────────────────
    print("\n[2a] Form non modifiée — Frappe envoie-t-il quand même un save ?")
    print("     NON : le client JS vérifie si la form est 'dirty' avant POST.")
    print("     Si aucun champ n'est changé → pas de requête serveur → B05 dormant.")
    print("     → Pour la démo, l'animateur DOIT modifier un champ.")

    # ── 2b : test hours_per_day 8→9 (trigger B05) ────────────────────────
    print("\n[2b] Test : hours_per_day 8 → 9 via doc.save() :")
    try:
        frappe.set_user("camille.roux@inovaya.com")
        task = frappe.get_doc("Task", TASK_FABRICATION)
        task.inovaya_hours_per_day = 9.0
        try:
            task.save()
            frappe.db.rollback()
            print("  ⚠ Save OK — B05 non déclenché")
        except frappe.exceptions.ValidationError as e:
            frappe.db.rollback()
            msg = str(e).replace("<br>", "\n     ").strip()
            print(f"  ✅ B05 déclenché :")
            print(f"     {msg[:400]}")
        except Exception as e:
            frappe.db.rollback()
            print(f"  ❓ {type(e).__name__}: {e}")
    finally:
        frappe.set_user(original_user)

    # ── 2c : test hours_per_day 8→2 (résolution) ─────────────────────────
    print("\n[2c] Test : hours_per_day 8 → 2 via doc.save() :")
    try:
        frappe.set_user("camille.roux@inovaya.com")
        task = frappe.get_doc("Task", TASK_FABRICATION)
        task.inovaya_hours_per_day = 2.0
        try:
            task.save()
            frappe.db.commit()
            h = frappe.db.get_value("Task", TASK_FABRICATION, "inovaya_hours_per_day")
            print(f"  ✅ Save OK — 2+6=8 ≤ 8 : aucune erreur (heures enregistrées : {h})")
        except frappe.exceptions.ValidationError as e:
            frappe.db.rollback()
            print(f"  ❌ Erreur inattendue : {e}")
        except Exception as e:
            frappe.db.rollback()
            print(f"  ❓ {type(e).__name__}: {e}")
    finally:
        frappe.set_user(original_user)

    # Remettre à 8h/j pour la démo
    frappe.db.set_value("Task", TASK_FABRICATION, "inovaya_hours_per_day", 8.0, update_modified=False)
    frappe.db.commit()
    print("     [données remises en état initial — 8h/j]")

    # ══════════════════════════════════════════════════════════════════════
    # SYNTHÈSE
    # ══════════════════════════════════════════════════════════════════════
    _sep("SYNTHÈSE — SÉQUENCES DÉMO VALIDÉES")
    print("""
SÉQUENCE 1 — B04 Eisenhower
  Compte Léa → ouvrir TASK-2026-00109 "Chiffrage & validation"
  Changer inovaya_importance : Basse → Haute
  Cliquer Sauvegarder
  → Erreur : "La modification de l'Importance est réservée aux rôles..."
  Basculer onglet Camille → même tâche → même action → Sauvegarder
  → Quadrant change de Q4 à Q2 instantanément

SÉQUENCE 2 — B05 Conflits de charge
  Compte Camille → ouvrir TASK-2026-00121 "Fabrication module IND"
  Changer inovaya_hours_per_day : 8 → 9
  Cliquer Sauvegarder
  → Erreur : "Léa Martin : 9h + 6h = 15h/j > 8h — du 17/06 au 08/07"
  Changer inovaya_hours_per_day : 9 → 2
  Cliquer Sauvegarder → OK
""")
