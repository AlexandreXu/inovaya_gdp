"""
Remet les données en état demo-ready avant chaque présentation.

1. Recalcule les quadrants Eisenhower (B04) sur toutes les tâches TEE-026
2. Assure les dates/heures de TASK-2026-00110 (Léa Réalisation) → 6h/j, J+21→J+42
3. Remet TASK-2026-00121 (Fabrication IND) à 8h/j (état initial pour démo B05)
4. Remet "Chiffrage & validation" à importance Basse (état initial pour démo B04)
5. Affiche l'état final prêt-à-montrer

Usage : bench --site inovaya.localhost execute inovaya_gdp.setup.demo_reset.run
"""
import frappe
from frappe.utils import today, getdate, add_days

URGENCY_DAYS = 7
_MATRIX = {
    (True,  True):  ("Urgente · Q1 — Critique (Faire en priorité)",    "Urgent"),
    (True,  False): ("Non urgente · Q2 — Important (Planifier)",        "High"),
    (False, True):  ("Urgente · Q3 — Déléguer (Urgent, non important)", "Medium"),
    (False, False): ("Non urgente · Q4 — Reporter / Éliminer",          "Low"),
}

def _recompute_eisenhower(task_name):
    """Recalcule B04 et met à jour les deux champs directement en DB."""
    t = frappe.db.get_value("Task", task_name,
                             ["exp_end_date", "inovaya_importance"], as_dict=True)
    if not t:
        return
    today_d = getdate(today())
    end_d   = getdate(t.exp_end_date) if t.exp_end_date else None
    urgent  = end_d and (end_d - today_d).days <= URGENCY_DAYS
    imp_h   = t.inovaya_importance == "Haute"
    label, prio = _MATRIX[(imp_h, bool(urgent))]
    frappe.db.set_value("Task", task_name, {
        "inovaya_eisenhower_info": label,
        "priority":                prio,
    }, update_modified=False)
    return label, prio


def run():
    today_d = getdate(today())
    print("\n" + "=" * 65)
    print("DEMO RESET — FONCTIONS S (B04 / B05 / B21)")
    print("=" * 65)

    tee026 = (frappe.db.get_all("Project",
              filters={"project_name": ["like", "TEE-026%"]}, pluck="name") or [None])[0]
    ind014 = (frappe.db.get_all("Project",
              filters={"project_name": ["like", "IND-014%"]}, pluck="name") or [None])[0]

    if not tee026 or not ind014:
        print("  ❌ Projets TEE-026 ou IND-014 introuvables — vérifier le jeu d'essai")
        return

    # ── 1. Recalcul B04 sur toutes les tâches TEE-026 ────────────────────────
    print("\n[1] Recalcul Eisenhower (B04) — TEE-026")
    tasks_tee = frappe.db.get_all("Task",
        filters={"project": tee026},
        fields=["name", "subject"],
        order_by="creation"
    )
    for t in tasks_tee:
        result = _recompute_eisenhower(t.name)
        if result:
            label, prio = result
            print(f"  ✅ {t.subject[:40]:<40} → {label} ({prio})")

    # ── 2. Reset "Chiffrage & validation" → importance Basse (état initial) ───
    print("\n[2] Reset 'Chiffrage & validation' → importance Basse")
    chiff = frappe.db.get_all("Task",
        filters={"project": tee026, "subject": ["like", "Chiffrage%"]}, pluck="name")
    if chiff:
        frappe.db.set_value("Task", chiff[0], "inovaya_importance", "Basse", update_modified=False)
        _recompute_eisenhower(chiff[0])
        print(f"  ✅ {chiff[0]} → importance=Basse recalculée")
    else:
        print("  ⚠ Tâche 'Chiffrage & validation' introuvable")

    # ── 3. Assurer TASK Réalisation/assemblage (Léa TEE-026) : J+21→J+42, 6h/j ──
    print("\n[3] Réalisation / assemblage (Léa) — dates J+21→J+42, 6h/j")
    real = frappe.db.get_all("Task",
        filters={"project": tee026, "subject": ["like", "%alisation%"]}, pluck="name")
    if real:
        start_real = str(add_days(today_d, 21))
        end_real   = str(add_days(today_d, 42))
        frappe.db.set_value("Task", real[0], {
            "exp_start_date":        start_real,
            "exp_end_date":          end_real,
            "inovaya_hours_per_day": 6.0,
        }, update_modified=False)
        _recompute_eisenhower(real[0])
        print(f"  ✅ {real[0]} → {start_real} → {end_real} @ 6h/j")
    else:
        print("  ⚠ Tâche 'Réalisation' introuvable")

    # ── 4. Reset Fabrication module IND → 8h/j (état initial démo B05) ───────
    print("\n[4] Fabrication module IND (Léa IND-014) — reset 8h/j")
    fab = frappe.db.get_all("Task",
        filters={"project": ind014, "subject": ["like", "Fabrication%"]}, pluck="name")
    if fab:
        start_fab = str(add_days(today_d, 21))
        end_fab   = str(add_days(today_d, 28))
        frappe.db.set_value("Task", fab[0], {
            "exp_start_date":        start_fab,
            "exp_end_date":          end_fab,
            "inovaya_hours_per_day": 8.0,
        }, update_modified=False)
        print(f"  ✅ {fab[0]} → {start_fab} → {end_fab} @ 8h/j")
    else:
        print("  ⚠ Tâche 'Fabrication module IND' introuvable")

    frappe.db.commit()

    # ── 5. Vérification finale ────────────────────────────────────────────────
    print("\n" + "─" * 65)
    print("ÉTAT FINAL PRÊT POUR LA DÉMO")
    print("─" * 65)

    import json as _json
    tasks = frappe.db.sql("""
        SELECT name, subject, inovaya_eisenhower_info, inovaya_importance,
               inovaya_hours_per_day, exp_start_date, exp_end_date, _assign
        FROM `tabTask`
        WHERE project IN (%s, %s)
        ORDER BY project, creation
    """, (tee026, ind014), as_dict=True)

    current_project = None
    for t in tasks:
        proj = frappe.db.get_value("Project", {"name": t.get("project", "")}, "project_name") if False else ""
        # Récupérer le projet via la tâche
        proj_name = frappe.db.get_value("Task", t.name, "project")
        if proj_name != current_project:
            current_project = proj_name
            print(f"\n  Projet : {proj_name}")
        assigns = _json.loads(t._assign or "[]")
        start = str(t.exp_start_date)[:10] if t.exp_start_date else "—"
        end   = str(t.exp_end_date)[:10]   if t.exp_end_date   else "—"
        print(f"    {t.name} | {t.subject[:35]:<35} | {t.inovaya_eisenhower_info or '—'}")
        print(f"             import={t.inovaya_importance or '—'} | {t.inovaya_hours_per_day}h/j | {start}→{end} | {', '.join(assigns) or '(non assigné)'}")

    print("\n" + "=" * 65)
    print("✅ RESET TERMINÉ — données prêtes pour la démo")
    print("=" * 65)
