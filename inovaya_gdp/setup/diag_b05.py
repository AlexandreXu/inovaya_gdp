"""
Diagnostic B05 — Pourquoi le conflit n'est-il pas détecté en UI ?
bench --site inovaya.localhost execute inovaya_gdp.setup.diag_b05.run
"""
import json
import frappe


def run():
    TASK_FAB   = "TASK-2026-00121"  # Fabrication module IND (PROJ-0010)
    TASK_REAL  = "TASK-2026-00110"  # Réalisation / assemblage (PROJ-0009)
    USER_LEA   = "lea.martin@inovaya.com"

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  DIAGNOSTIC B05 — Fabrication module IND vs Réalisation")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # ── 1. Données brutes en base ──────────────────────────────────────
    print("\n[1] DONNÉES BRUTES tabTask")
    for tname in [TASK_FAB, TASK_REAL]:
        row = frappe.db.sql("""
            SELECT name, subject, project, _assign,
                   DATE(exp_start_date) AS s, DATE(exp_end_date) AS e,
                   inovaya_hours_per_day AS h
            FROM tabTask WHERE name = %s
        """, tname, as_dict=True)
        if row:
            r = row[0]
            print(f"  {r.name}: {r.subject} [{r.project}]")
            print(f"    _assign={r._assign!r}  h={r.h}  {r.s}→{r.e}")
        else:
            print(f"  {tname}: ❌ INTROUVABLE")

    # ── 2. Simulation query B05 avec 9h/j ─────────────────────────────
    print(f"\n[2] QUERY B05 simulée (doc_hours=9, user={USER_LEA})")
    print(f"    start=2026-06-17  end=2026-06-24  threshold=8.0")

    conflicts = frappe.db.sql("""
        SELECT name, subject, project,
               DATE(exp_start_date) AS start_date,
               DATE(exp_end_date)   AS end_date,
               COALESCE(NULLIF(inovaya_hours_per_day, 0), 8.0) AS hours_per_day,
               _assign
        FROM `tabTask`
        WHERE name              != %(exclude)s
          AND is_template        = 0
          AND _assign             LIKE %(pattern)s
          AND DATE(exp_end_date)   >= %(start)s
          AND DATE(exp_start_date) <= %(end)s
        LIMIT 10
    """, {
        "exclude": TASK_FAB,
        "pattern": f'%"{USER_LEA}"%',
        "start": "2026-06-17",
        "end":   "2026-06-24",
    }, as_dict=True)

    if conflicts:
        for c in conflicts:
            total = 9.0 + c["hours_per_day"]
            flag = "🔴 CONFLIT" if total > 8.0 else "✅ OK"
            print(f"  {flag}  {c.name}: {c.subject}  h={c.hours_per_day}  total={total}")
            print(f"    _assign={c._assign!r}  {c.start_date}→{c.end_date}")
    else:
        print("  ❌ Aucune tâche retournée par la query")
        # Test LIKE pattern
        raw = frappe.db.sql(
            "SELECT name, _assign FROM tabTask WHERE name = %s", TASK_REAL, as_dict=True
        )
        if raw:
            r = raw[0]
            assign_val = r._assign or ""
            pattern = f'%"{USER_LEA}"%'
            match = USER_LEA in assign_val
            print(f"\n  Test LIKE manuel sur {TASK_REAL}:")
            print(f"    _assign brut = {assign_val!r}")
            print(f"    pattern      = {pattern!r}")
            print(f"    Python match = {match}")

    # ── 3. Vérifier frappe.flags ───────────────────────────────────────
    print(f"\n[3] frappe.flags")
    print(f"  in_import  = {frappe.flags.in_import}")
    print(f"  in_migrate = {frappe.flags.in_migrate}")
    print(f"  in_test    = {frappe.flags.in_test}")

    # ── 4. Simuler le hook directement sur le doc chargé ─────────────
    print(f"\n[4] SIMULATION HOOK — frappe.get_doc + set h=9 + hook direct")
    try:
        frappe.set_user("lea.martin@inovaya.com")
        doc = frappe.get_doc("Task", TASK_FAB)
        print(f"  doc.inovaya_hours_per_day (avant) = {doc.inovaya_hours_per_day}")
        print(f"  doc._assign = {doc._assign!r}")

        doc.inovaya_hours_per_day = 9.0

        from inovaya_gdp.overrides.task import _check_planning_conflicts
        try:
            _check_planning_conflicts(doc)
            print("  ❌ _check_planning_conflicts n'a PAS levé d'exception → bug")
        except frappe.exceptions.ValidationError as e:
            print(f"  ✅ Exception levée (attendue) : {str(e)[:120]}")
        except Exception as e:
            print(f"  ⚠️  Exception inattendue : {type(e).__name__}: {e}")
    finally:
        frappe.set_user("Administrator")

    # ── 5. Vérifier le hook dans doc_events ───────────────────────────
    print(f"\n[5] HOOK ENREGISTRÉ dans Frappe ?")
    hooks = frappe.get_hooks("doc_events")
    task_hooks = hooks.get("Task", {})
    print(f"  Task.before_save = {task_hooks.get('before_save')}")
