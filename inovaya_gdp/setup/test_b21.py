"""
Validation B21 — Marge Atterrissage InovaYa
1. Pose EAC = 45 000 € sur TEE-026
2. Exécute get_data() et affiche le tableau de résultats
3. Vérifie les valeurs attendues

Usage : bench --site inovaya.localhost execute inovaya_gdp.setup.test_b21.run
"""
import frappe


def run():
    # ── Trouver TEE-026 ───────────────────────────────────────────────────────
    found = frappe.db.get_all(
        "Project",
        filters={"project_name": ["like", "TEE-026%"]},
        pluck="name",
    )
    if not found:
        print("  ❌ Projet TEE-026 introuvable")
        return
    project = found[0]
    print(f"\nProjet : {project}")

    # ── Définir EAC ───────────────────────────────────────────────────────────
    frappe.db.set_value("Project", project, "inovaya_eac", 45000, update_modified=False)
    frappe.db.commit()
    print(f"  ✅ EAC défini à 45 000 € sur {project}")

    # ── Exécuter le rapport ───────────────────────────────────────────────────
    from inovaya_gdp.inovaya.report.marge_atterrissage_inovaya.marge_atterrissage_inovaya import get_data
    data = get_data({"project": project})

    # ── Affichage ─────────────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    print("RAPPORT B21 — MARGE ATTERRISSAGE INOVAYA — " + project)
    print("=" * 62)

    results = {}
    for row in data:
        if row.get("_is_sep"):
            print("  " + "─" * 50)
            continue
        poste   = row["poste"]
        montant = row["montant"]
        key     = row.get("_key", "")

        if montant is None:
            display = "—"
        elif row.get("_is_pct"):
            display = f"{montant:.1f} %"
        else:
            display = f"{montant:>14,.0f} €"

        color_flag = f"  [{row['_color'].upper()}]" if row.get("_color") else ""
        bold       = "** " if row.get("_bold") else "   "
        print(f"  {bold}{poste:<45} {display}{color_flag}")

        if key:
            results[key] = montant

    # ── Vérification automatique ──────────────────────────────────────────────
    print("\n" + "=" * 62)
    print("VÉRIFICATION vs ATTENDU")
    print("=" * 62)

    def chk(c): return "✅" if c else "❌"

    attendu = {
        "ca":           120_000,
        "budget":       120_000,
        "depenses":       8_500,
        "eac":           45_000,
        "cout_total":    53_850,
        "marge_prev":         0,
        "marge_proj":    66_150,
        "atterrissage":    55.1,
    }

    # ETP peut varier selon les heures enregistrées — on vérifie juste que c'est > 0
    etp_ok = results.get("etp", 0) > 0
    print(f"  Coût ETP > 0            : {chk(etp_ok)}  ({results.get('etp', 0):.0f}€)")

    for k, expected in attendu.items():
        got = results.get(k, "MANQUANT")
        if k == "atterrissage":
            ok = isinstance(got, float) and abs(got - expected) < 0.15
        else:
            ok = isinstance(got, (int, float)) and abs(got - expected) < 1
        label = k.replace("_", " ").capitalize()
        print(f"  {label:<25} : {chk(ok)}  attendu={expected:,.1f}  obtenu={got}")

    all_ok = all(
        abs(results.get(k, -1) - v) < (0.15 if k == "atterrissage" else 1)
        for k, v in attendu.items()
    ) and etp_ok

    print(f"\n{'='*62}")
    print(f"{'✅ B21 VALIDÉ — rapport conforme aux attendus' if all_ok else '⚠ ÉCART DÉTECTÉ — voir ci-dessus'}")
    print(f"{'='*62}")
