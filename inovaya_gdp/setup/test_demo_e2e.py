"""
Test de bout en bout — toutes les séquences démo.

bench --site inovaya.localhost execute inovaya_gdp.setup.test_demo_e2e.run
"""
import json
import frappe


def _sep(t):
    print(f"\n{'='*65}\n{t}\n{'='*65}")


def _ok(label):
    print(f"  ✅ {label}")


def _fail(label, detail=""):
    d = f" — {detail}" if detail else ""
    print(f"  ❌ {label}{d}")


# ═══════════════════════════════════════════════════════════════════
# HELPER : simuler _guard_importance_change avec _doc_before_save
# ═══════════════════════════════════════════════════════════════════
def _sim_guard(user, task_name, new_importance):
    from inovaya_gdp.overrides.task import _guard_importance_change
    original = frappe.session.user
    try:
        frappe.set_user(user)
        doc_before = frappe.get_doc("Task", task_name)
        doc = frappe.get_doc("Task", task_name)
        doc.inovaya_importance = new_importance
        doc._doc_before_save = doc_before
        try:
            _guard_importance_change(doc)
            return "OK", doc
        except frappe.exceptions.ValidationError as e:
            return "BLOCKED", str(e)
    finally:
        frappe.set_user(original)


def _sim_b05(task_name, new_hours, user="camille.roux@inovaya.com"):
    from inovaya_gdp.overrides.task import _check_planning_conflicts
    original = frappe.session.user
    try:
        frappe.set_user(user)
        doc = frappe.get_doc("Task", task_name)
        doc.inovaya_hours_per_day = new_hours
        try:
            _check_planning_conflicts(doc)
            return "OK", ""
        except frappe.exceptions.ValidationError as e:
            return "BLOCKED", str(e).replace("<br>", " | ")
    finally:
        frappe.set_user(original)


def run():
    results = {}  # label → bool

    # ── PRÉ-REQUIS : reset données ─────────────────────────────────
    _sep("0 — RESET DONNÉES DÉMO")
    try:
        from inovaya_gdp.setup.demo_reset import run as do_reset
        do_reset()
        _ok("demo_reset.run exécuté")
        results["Reset demo_reset.run"] = True
    except Exception as e:
        _fail("demo_reset.run", str(e))
        results["Reset demo_reset.run"] = False

    # ═══════════════════════════════════════════════════════════════
    # SÉQUENCE 1 — B04 EISENHOWER
    # ═══════════════════════════════════════════════════════════════
    _sep("SÉQUENCE 1 — B04 EISENHOWER")

    # 1.1 PROJ-0009 : 4 tâches avec quadrants
    print("\n[S1.1] Tâches PROJ-0009 avec quadrants :")
    tasks = frappe.get_all(
        "Task",
        filters={"project": "PROJ-0009"},
        fields=["name", "subject", "inovaya_importance",
                "inovaya_eisenhower_info", "priority", "exp_end_date"],
        order_by="name",
    )
    expected_quadrants = {
        "TASK-2026-00107": "Q3",  # Diagnostic, Basse, urgent
        "TASK-2026-00108": "Q2",  # Conception P&ID, Haute, non urgent
        "TASK-2026-00109": "Q4",  # Chiffrage, Basse, non urgent
        "TASK-2026-00110": "Q4",  # Réalisation, Basse, non urgent
        "TASK-2026-00111": "Q4",  # Mise en service
        "TASK-2026-00112": "Q2",  # Essais terrain, Haute
    }
    all_q_ok = True
    for t in tasks:
        q = t.inovaya_eisenhower_info or ""
        expected_q = expected_quadrants.get(t.name, "")
        ok = expected_q in q if expected_q else bool(q)
        sym = "✅" if ok else "❌"
        print(f"  {sym} {t.name}  {t.subject[:28]:<28}  "
              f"imp={t.inovaya_importance or '—':<6}  quadrant={q[:30]}")
        if not ok:
            all_q_ok = False
    results["S1.1 — Quadrants PROJ-0009 corrects"] = all_q_ok

    # 1.2 TASK-2026-00109 état initial (Basse, Q4)
    print("\n[S1.2] TASK-2026-00109 état initial :")
    t109 = frappe.db.get_value(
        "Task", "TASK-2026-00109",
        ["inovaya_importance", "inovaya_eisenhower_info", "priority"],
        as_dict=True,
    )
    imp_ok  = t109.inovaya_importance == "Basse"
    q4_ok   = "Q4" in (t109.inovaya_eisenhower_info or "")
    prio_ok = t109.priority in ("Low", "Medium", None, "")
    print(f"  importance={t109.inovaya_importance!r}  "
          f"quadrant={t109.inovaya_eisenhower_info!r}  priority={t109.priority!r}")
    results["S1.2 — Chiffrage importance=Basse"] = imp_ok
    results["S1.2 — Chiffrage quadrant=Q4"]      = q4_ok
    if imp_ok: _ok("importance=Basse")
    else:      _fail("importance attendue Basse", t109.inovaya_importance)
    if q4_ok:  _ok("quadrant=Q4")
    else:      _fail("quadrant attendu Q4", t109.inovaya_eisenhower_info)

    # 1.3 Léa bloquée
    print("\n[S1.3] Simulation Léa — Basse → Haute :")
    status, detail = _sim_guard("lea.martin@inovaya.com", "TASK-2026-00109", "Haute")
    lea_blocked = status == "BLOCKED"
    results["S1.3 — Léa bloquée B04"] = lea_blocked
    if lea_blocked:
        _ok(f"BLOQUÉ → {str(detail)[:80]}")
    else:
        _fail("Léa NON bloquée — problème cloisonnement B04")

    # 1.4 Camille autorisée → Q4→Q2
    print("\n[S1.4] Simulation Camille — Basse → Haute :")
    status2, doc2 = _sim_guard("camille.roux@inovaya.com", "TASK-2026-00109", "Haute")
    camille_ok = status2 == "OK"
    results["S1.4 — Camille autorisée B04"] = camille_ok
    if camille_ok:
        from inovaya_gdp.overrides.task import _run_eisenhower
        doc2.inovaya_importance = "Haute"
        doc2._doc_before_save = frappe.get_doc("Task", "TASK-2026-00109")
        _run_eisenhower(doc2)
        q2_ok = "Q2" in (doc2.inovaya_eisenhower_info or "")
        results["S1.4 — Q4→Q2 après save Camille"] = q2_ok
        _ok(f"AUTORISÉ → quadrant={doc2.inovaya_eisenhower_info}")
        if q2_ok: _ok("Quadrant = Q2 ✓")
        else:     _fail("Quadrant attendu Q2", doc2.inovaya_eisenhower_info)
    else:
        results["S1.4 — Q4→Q2 après save Camille"] = False
        _fail("Camille bloquée inattendu", str(doc2)[:100])

    # Reset après S1
    frappe.db.set_value("Task", "TASK-2026-00109", "inovaya_importance", "Basse", update_modified=False)
    frappe.db.set_value("Task", "TASK-2026-00109", "inovaya_eisenhower_info",
                        "Non urgente · Q4 — Reporter / Éliminer", update_modified=False)
    frappe.db.commit()

    # ═══════════════════════════════════════════════════════════════
    # SÉQUENCE 2 — B05 CONFLITS DE CHARGE
    # ═══════════════════════════════════════════════════════════════
    _sep("SÉQUENCE 2 — B05 CONFLITS DE CHARGE")

    # 2.1 État TASK-2026-00110 (Réalisation)
    print("\n[S2.1] TASK-2026-00110 Réalisation / assemblage :")
    t110 = frappe.db.get_value(
        "Task", "TASK-2026-00110",
        ["subject", "inovaya_hours_per_day", "exp_start_date",
         "exp_end_date", "_assign"],
        as_dict=True,
    )
    assigns_110 = json.loads(t110._assign or "[]")
    h110_ok  = float(t110.inovaya_hours_per_day or 0) == 6.0
    lea_ok   = "lea.martin@inovaya.com" in assigns_110
    s110_ok  = str(t110.exp_start_date)[:10] == "2026-06-17"
    e110_ok  = str(t110.exp_end_date)[:10]   == "2026-07-08"
    print(f"  heures/j={t110.inovaya_hours_per_day}  "
          f"assignés={assigns_110}  "
          f"{str(t110.exp_start_date)[:10]}→{str(t110.exp_end_date)[:10]}")
    results["S2.1 — Réalisation 6h/j"]              = h110_ok
    results["S2.1 — Réalisation assignée à Léa"]    = lea_ok
    results["S2.1 — Réalisation dates 17/06→08/07"] = s110_ok and e110_ok
    for ok, label in [(h110_ok, "6h/j"), (lea_ok, "Léa assignée"),
                      (s110_ok and e110_ok, "dates 17/06→08/07")]:
        if ok: _ok(label)
        else:  _fail(label)

    # 2.2 État TASK-2026-00121 (Fabrication)
    print("\n[S2.2] TASK-2026-00121 Fabrication module IND :")
    t121 = frappe.db.get_value(
        "Task", "TASK-2026-00121",
        ["subject", "inovaya_hours_per_day", "exp_start_date",
         "exp_end_date", "_assign"],
        as_dict=True,
    )
    assigns_121 = json.loads(t121._assign or "[]")
    h121_ok = float(t121.inovaya_hours_per_day or 0) == 8.0
    lea_121 = "lea.martin@inovaya.com" in assigns_121
    s121_ok = str(t121.exp_start_date)[:10] == "2026-06-17"
    e121_ok = str(t121.exp_end_date)[:10]   == "2026-06-24"
    print(f"  heures/j={t121.inovaya_hours_per_day}  "
          f"assignés={assigns_121}  "
          f"{str(t121.exp_start_date)[:10]}→{str(t121.exp_end_date)[:10]}")
    results["S2.2 — Fabrication 8h/j"]              = h121_ok
    results["S2.2 — Fabrication assignée à Léa"]    = lea_121
    results["S2.2 — Fabrication dates 17/06→24/06"] = s121_ok and e121_ok
    for ok, label in [(h121_ok, "8h/j"), (lea_121, "Léa assignée"),
                      (s121_ok and e121_ok, "dates 17/06→24/06")]:
        if ok: _ok(label)
        else:  _fail(label)

    # 2.3 Blocage 8→9
    print("\n[S2.3] Blocage B05 — 8→9 h/j :")
    st3, msg3 = _sim_b05("TASK-2026-00121", 9.0)
    blocked_ok = st3 == "BLOCKED"
    results["S2.3 — Blocage B05 à 9h/j"] = blocked_ok
    if blocked_ok:
        _ok(f"BLOQUÉ : {msg3[:120]}")
        # Vérifier que le message contient les valeurs exactes
        msg_ok = "9.0" in msg3 and "6.0" in msg3 and "15.0" in msg3
        results["S2.3 — Message B05 contient 9.0+6.0=15.0"] = msg_ok
        if msg_ok: _ok("Message contient 9.0h + 6.0h = 15.0h ✓")
        else:      _fail("Message incomplet", msg3[:200])
    else:
        results["S2.3 — Message B05 contient 9.0+6.0=15.0"] = False
        _fail("B05 NON déclenché — problème hook")

    # 2.4 Résolution 9→2
    print("\n[S2.4] Résolution B05 — 9→2 h/j :")
    st4, msg4 = _sim_b05("TASK-2026-00121", 2.0)
    resolved_ok = st4 == "OK"
    results["S2.4 — Save OK à 2h/j (2+6=8≤8)"] = resolved_ok
    if resolved_ok: _ok("Save autorisé — 2+6=8 ≤ 8")
    else:           _fail("Save bloqué inattendu", msg4[:200])

    # Remettre à 8h/j
    frappe.db.set_value("Task", "TASK-2026-00121", "inovaya_hours_per_day", 8.0, update_modified=False)
    frappe.db.commit()

    # ═══════════════════════════════════════════════════════════════
    # SÉQUENCE 3 — B21 MARGE & ATTERRISSAGE
    # ═══════════════════════════════════════════════════════════════
    _sep("SÉQUENCE 3 — B21 MARGE & ATTERRISSAGE")

    # 3.1 Champ EAC visible sur PROJ-0009
    print("\n[S3.1] Champ EAC sur PROJ-0009 :")
    eac_field = frappe.db.get_value("Custom Field", "Project-inovaya_eac", "fieldname")
    eac_cf_ok = eac_field == "inovaya_eac"
    eac_val   = frappe.db.get_value("Project", "PROJ-0009", "inovaya_eac") or 0
    eac_set   = float(eac_val) == 45000.0
    results["S3.1 — Custom Field Project-inovaya_eac existe"] = eac_cf_ok
    results["S3.1 — EAC = 45 000 € sur PROJ-0009"]           = eac_set
    if eac_cf_ok: _ok("Custom Field Project-inovaya_eac présent")
    else:         _fail("Custom Field manquant")
    if eac_set:   _ok(f"EAC = {eac_val} € ✓")
    else:         _fail(f"EAC attendu 45000, trouvé {eac_val}")

    # 3.2 Rapport B21 — EAC=45k → 55.1%
    print("\n[S3.2] Rapport B21 avec EAC=45 000 € :")
    try:
        from inovaya_gdp.inovaya.report.marge_atterrissage_inovaya.marge_atterrissage_inovaya import execute as b21_exec
        data_45k = b21_exec({"project": "PROJ-0009"})
        rows_45k = data_45k[1] if isinstance(data_45k, (list, tuple)) and len(data_45k) > 1 else []
        att_row  = next((r for r in rows_45k if r.get("_is_pct")), None)
        depenses = next((r for r in rows_45k if "penses" in (r.get("poste") or "")), None)
        etp_row  = next((r for r in rows_45k if "ETP" in (r.get("poste") or "")), None)

        dep_ok = depenses and abs(float(depenses.get("montant") or 0) - 8500) < 1
        etp_ok = etp_row  and abs(float(etp_row.get("montant")  or 0) - 350)  < 1

        if depenses: print(f"  Dépenses (PO)    : {depenses.get('montant')} € (attendu 8500)")
        if etp_row:  print(f"  ETP (timesheets) : {etp_row.get('montant')} € (attendu 350)")

        results["S3.2 — Dépenses PO = 8 500 €"] = bool(dep_ok)
        results["S3.2 — ETP = 350 €"]            = bool(etp_ok)
        if dep_ok: _ok("Dépenses = 8 500 € ✓")
        else:      _fail(f"Dépenses attendu 8500, trouvé {depenses.get('montant') if depenses else 'N/A'}")
        if etp_ok: _ok("ETP = 350 € ✓")
        else:      _fail(f"ETP attendu 350, trouvé {etp_row.get('montant') if etp_row else 'N/A'}")

        if att_row:
            pct_45k = float(att_row.get("montant") or 0)
            pct_ok  = abs(pct_45k - 55.1) < 0.5
            color_ok = att_row.get("_color") == "vert"
            print(f"  Atterrissage % (EAC=45k) : {pct_45k:.1f}% (attendu ~55.1%)  couleur={att_row.get('_color')}")
            results["S3.2 — Atterrissage 55.1% vert (EAC=45k)"] = pct_ok and color_ok
            if pct_ok and color_ok: _ok(f"55.1% VERT ✓")
            else:                   _fail(f"Attendu 55.1% vert, obtenu {pct_45k:.1f}% {att_row.get('_color')}")
        else:
            results["S3.2 — Atterrissage 55.1% vert (EAC=45k)"] = False
            _fail("Ligne Atterrissage % introuvable dans le rapport")

    except Exception as e:
        import traceback
        results["S3.2 — Dépenses PO = 8 500 €"]              = False
        results["S3.2 — ETP = 350 €"]                        = False
        results["S3.2 — Atterrissage 55.1% vert (EAC=45k)"] = False
        _fail("Rapport B21 erreur", str(e))
        traceback.print_exc()

    # 3.3 EAC=100k → 9.3%
    print("\n[S3.3] Rapport B21 avec EAC=100 000 € :")
    try:
        # Changer temporairement EAC
        frappe.db.set_value("Project", "PROJ-0009", "inovaya_eac", 100000.0, update_modified=False)
        frappe.db.commit()
        data_100k = b21_exec({"project": "PROJ-0009"})
        rows_100k = data_100k[1] if isinstance(data_100k, (list, tuple)) and len(data_100k) > 1 else []
        att_100   = next((r for r in rows_100k if r.get("_is_pct")), None)
        if att_100:
            pct_100k = float(att_100.get("montant") or 0)
            pct100_ok = abs(pct_100k - 9.3) < 0.5
            print(f"  Atterrissage % (EAC=100k) : {pct_100k:.1f}% (attendu ~9.3%)")
            results["S3.3 — Atterrissage 9.3% neutre (EAC=100k)"] = pct100_ok
            if pct100_ok: _ok(f"9.3% ✓")
            else:         _fail(f"Attendu 9.3%, obtenu {pct_100k:.1f}%")
        else:
            results["S3.3 — Atterrissage 9.3% neutre (EAC=100k)"] = False
            _fail("Ligne Atterrissage % introuvable")
    except Exception as e:
        results["S3.3 — Atterrissage 9.3% neutre (EAC=100k)"] = False
        _fail("Rapport B21 EAC=100k erreur", str(e))
    finally:
        # Remettre EAC à 45 000
        frappe.db.set_value("Project", "PROJ-0009", "inovaya_eac", 45000.0, update_modified=False)
        frappe.db.commit()

    # 3.4 EAC=120k → ≤0% rouge
    print("\n[S3.4] Rapport B21 avec EAC=120 000 € :")
    try:
        frappe.db.set_value("Project", "PROJ-0009", "inovaya_eac", 120000.0, update_modified=False)
        frappe.db.commit()
        data_120k = b21_exec({"project": "PROJ-0009"})
        rows_120k = data_120k[1] if isinstance(data_120k, (list, tuple)) and len(data_120k) > 1 else []
        att_120   = next((r for r in rows_120k if r.get("_is_pct")), None)
        if att_120:
            pct_120k = float(att_120.get("montant") or 0)
            rouge_ok = att_120.get("_color") == "rouge"
            print(f"  Atterrissage % (EAC=120k) : {pct_120k:.1f}%  couleur={att_120.get('_color')}")
            results["S3.4 — Atterrissage ≤0% rouge (EAC=120k)"] = pct_120k <= 0 and rouge_ok
            if pct_120k <= 0 and rouge_ok: _ok(f"{pct_120k:.1f}% ROUGE ✓")
            else:                          _fail(f"Attendu ≤0% rouge, obtenu {pct_120k:.1f}% {att_120.get('_color')}")
        else:
            results["S3.4 — Atterrissage ≤0% rouge (EAC=120k)"] = False
            _fail("Ligne Atterrissage % introuvable")
    except Exception as e:
        results["S3.4 — Atterrissage ≤0% rouge (EAC=120k)"] = False
        _fail("Rapport B21 EAC=120k erreur", str(e))
    finally:
        frappe.db.set_value("Project", "PROJ-0009", "inovaya_eac", 45000.0, update_modified=False)
        frappe.db.commit()

    # ═══════════════════════════════════════════════════════════════
    # VÉRIFICATION RESET FINAL
    # ═══════════════════════════════════════════════════════════════
    _sep("VÉRIFICATION RESET FINAL")
    try:
        from inovaya_gdp.setup.demo_reset import run as do_reset2
        do_reset2()
        # Vérifier l'état après reset
        t109r = frappe.db.get_value("Task", "TASK-2026-00109",
                                    ["inovaya_importance", "inovaya_eisenhower_info"], as_dict=True)
        t121r = frappe.db.get_value("Task", "TASK-2026-00121",
                                    "inovaya_hours_per_day")
        eac_r = frappe.db.get_value("Project", "PROJ-0009", "inovaya_eac")
        r1 = t109r.inovaya_importance == "Basse"
        r2 = "Q4" in (t109r.inovaya_eisenhower_info or "")
        r3 = float(t121r or 0) == 8.0
        r4 = float(eac_r or 0) == 45000.0
        results["Reset final — Chiffrage→Basse/Q4"]       = r1 and r2
        results["Reset final — Fabrication→8h/j"]         = r3
        results["Reset final — EAC PROJ-0009 = 45 000 €"] = r4
        for ok, label in [(r1 and r2, "Chiffrage→Basse Q4"),
                          (r3, "Fabrication→8h/j"),
                          (r4, "EAC PROJ-0009=45 000 €")]:
            if ok: _ok(label)
            else:  _fail(label)
    except Exception as e:
        results["Reset final"] = False
        _fail("Reset final erreur", str(e))

    # ═══════════════════════════════════════════════════════════════
    # RAPPORT FINAL
    # ═══════════════════════════════════════════════════════════════
    _sep("RAPPORT FINAL — DÉMO PRÊTE ?")
    total  = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    for label, ok in results.items():
        sym = "✅" if ok else "❌"
        print(f"  {sym}  {label}")

    print(f"\n  Score : {passed}/{total} tests passés", end="")
    if failed == 0:
        print("  🎉 DÉMO PRÊTE — tous les tests sont verts")
    else:
        print(f"  ⚠ {failed} test(s) à corriger avant la démo")
