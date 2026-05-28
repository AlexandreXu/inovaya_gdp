"""
Vérifie l'état exact des données de démo avant de rédiger le script.
bench --site inovaya.localhost execute inovaya_gdp.setup.check_demo_state.run
"""
import frappe
import json

def run():
    print("=" * 65)
    print("ÉTAT DES DONNÉES — DÉMO FONCTIONS S")
    print("=" * 65)

    # ── TEE-026 ──────────────────────────────────────────────────────────────
    tee = frappe.db.get_all("Project", filters={"project_name": ["like", "TEE-026%"]}, pluck="name")
    ind = frappe.db.get_all("Project", filters={"project_name": ["like", "IND-014%"]}, pluck="name")
    tee026 = tee[0] if tee else None
    ind014 = ind[0] if ind else None
    print(f"\nTEE-026 : {tee026}   IND-014 : {ind014}")

    # ── Tâches TEE-026 avec quadrant Eisenhower ───────────────────────────────
    print("\n--- TÂCHES TEE-026 (B04 Eisenhower) ---")
    tasks_tee = frappe.db.sql("""
        SELECT name, subject, exp_end_date, expected_time,
               inovaya_importance, inovaya_eisenhower_info,
               priority, _assign
        FROM `tabTask`
        WHERE project = %s
        ORDER BY creation
    """, tee026, as_dict=True)

    for t in tasks_tee:
        assigns = json.loads(t._assign or "[]")
        print(f"\n  Tâche   : {t.name}")
        print(f"  Sujet   : {t.subject}")
        print(f"  Échéance: {t.exp_end_date}")
        print(f"  Heures  : {t.expected_time}h")
        print(f"  Assigné : {', '.join(assigns)}")
        print(f"  Import. : {t.inovaya_importance}")
        print(f"  Quadrant: {t.inovaya_eisenhower_info}")
        print(f"  Priorité: {t.priority}")

    # ── Tâche IND-014 Fabrication (B05) ─────────────────────────────────────
    print("\n--- TÂCHES IND-014 (B05 Conflits) ---")
    if ind014:
        tasks_ind = frappe.db.sql("""
            SELECT name, subject, exp_start_date, exp_end_date,
                   expected_time, inovaya_hours_per_day, _assign
            FROM `tabTask`
            WHERE project = %s
            ORDER BY creation
        """, ind014, as_dict=True)
        for t in tasks_ind:
            assigns = json.loads(t._assign or "[]")
            print(f"\n  Tâche    : {t.name}")
            print(f"  Sujet    : {t.subject}")
            print(f"  Début    : {t.exp_start_date}")
            print(f"  Fin      : {t.exp_end_date}")
            print(f"  Heures   : {t.expected_time}h — {t.inovaya_hours_per_day}h/j")
            print(f"  Assigné  : {', '.join(assigns)}")

    # ── Tâche TEE-026 Réalisation (Léa) ─────────────────────────────────────
    print("\n--- TÂCHE RÉALISATION/ASSEMBLAGE (Léa TEE-026) ---")
    if tee026:
        lea_tasks = frappe.db.sql("""
            SELECT name, subject, exp_start_date, exp_end_date,
                   expected_time, inovaya_hours_per_day, _assign
            FROM `tabTask`
            WHERE project = %s AND subject LIKE '%alisation%'
        """, tee026, as_dict=True)
        for t in lea_tasks:
            assigns = json.loads(t._assign or "[]")
            print(f"  Tâche    : {t.name}")
            print(f"  Sujet    : {t.subject}")
            print(f"  Début    : {t.exp_start_date}")
            print(f"  Fin      : {t.exp_end_date}")
            print(f"  Heures   : {t.expected_time}h — {t.inovaya_hours_per_day}h/j")
            print(f"  Assigné  : {', '.join(assigns)}")

    # ── B21 TEE-026 ──────────────────────────────────────────────────────────
    print("\n--- B21 MARGE TEE-026 ---")
    if tee026:
        eac = frappe.db.get_value("Project", tee026, "inovaya_eac")
        jalons = frappe.db.sql("""
            SELECT label, amount FROM `tabJalon Facturation InovaYa`
            WHERE project = %s ORDER BY creation
        """, tee026, as_dict=True)
        print(f"  EAC     : {eac}€")
        for j in jalons:
            print(f"  Jalon   : {j.label} — {j.amount}€")
        ca = sum(j.amount or 0 for j in jalons)
        print(f"  CA total: {ca}€")
