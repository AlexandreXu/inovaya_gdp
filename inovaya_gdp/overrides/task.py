"""
B04 — Priorisation automatique Eisenhower (Task + Annexe Task).
B05 — Détection automatique des conflits de planning (blocage dur).

B04 : Matrice urgence × importance → priority natif mis à jour.
B05 : Chevauchement de plages de dates (granularité jour, DATE()) pour un même
      collaborateur. Périmètre : Task intra-projet + inter-projets + Annexe Task.
      Collaborateur identifié via _assign JSON (Task) ou assigned_to (Annexe Task).
      Blocage dur via frappe.throw avant sauvegarde.
      Limitation POC : tâches sans _assign non détectées (voir BACKLOG B05).
      LIMIT 10 : seuls les 10 premiers conflits sont affichés (voir BACKLOG B05).
"""
import json
import frappe
from frappe import _

# ---------------------------------------------------------------------------
# B04 — Eisenhower
# ---------------------------------------------------------------------------

# Jours en-dessous desquels une tâche est considérée urgente
URGENCY_DAYS = 7

# Rôles autorisés à modifier inovaya_importance sur les Task projet
ALLOWED_ROLES_IMPORTANCE = frozenset([
    "Responsable GdP",
    "Responsable Operations",
    "Direction Generale",
    "System Manager",
    "Administrator",
])

# (importance_haute, urgent) → (label_quadrant, frappe_priority)
_MATRIX = {
    (True,  True):  ("Q1 — Critique (Faire en priorité)",      "Urgent"),
    (True,  False): ("Q2 — Important (Planifier)",              "High"),
    (False, True):  ("Q3 — Déléguer (Urgent, non important)",  "Medium"),
    (False, False): ("Q4 — Reporter / Éliminer",                "Low"),
}


def _get_end_date(doc):
    """Normalise exp_end_date → date, compatible Date (Annexe Task) et Datetime (Task)."""
    val = doc.get("exp_end_date")
    return frappe.utils.getdate(val) if val else None


def _is_urgent(end_date):
    """True si l'échéance est dans ≤ URGENCY_DAYS jours (ou déjà dépassée)."""
    if not end_date:
        return False
    today = frappe.utils.getdate(frappe.utils.today())
    return (end_date - today).days <= URGENCY_DAYS


def _guard_importance_change(doc):
    """Bloque la modification de inovaya_importance aux rôles non autorisés."""
    new_val = doc.get("inovaya_importance") or ""
    if not new_val or new_val == "Basse":
        return

    doc_before = doc.get_doc_before_save()
    old_val = (doc_before.get("inovaya_importance") if doc_before else None) or ""
    if old_val == new_val:
        return

    user_roles = frozenset(frappe.get_roles(frappe.session.user))
    if ALLOWED_ROLES_IMPORTANCE & user_roles:
        return

    if doc_before:
        frappe.throw(
            _(
                "La modification de l'Importance (matrice Eisenhower) est réservée "
                "aux rôles : Responsable GdP, Responsable Opérations, Direction Générale."
            ),
            title=_("Permission insuffisante — B04"),
        )
    else:
        # Nouvelle tâche créée par un non-autorisé → reset silencieux
        doc.inovaya_importance = "Basse"


def _run_eisenhower(doc):
    """B04 — Calcul Eisenhower. Ne lève jamais d'exception."""
    if doc.get("is_template"):
        return

    if doc.doctype == "Task":
        _guard_importance_change(doc)

    importance_haute = doc.get("inovaya_importance") == "Haute"
    end_date = _get_end_date(doc)
    urgent = _is_urgent(end_date)

    quadrant_label, priority = _MATRIX[(importance_haute, urgent)]
    doc.inovaya_eisenhower_info = (
        f"{'Urgente' if urgent else 'Non urgente'} · {quadrant_label}"
    )

    if doc.get("inovaya_importance"):
        doc.priority = priority


# ---------------------------------------------------------------------------
# B05 — Conflits de planning
# ---------------------------------------------------------------------------

def _get_daily_hours(doc):
    """Retourne inovaya_hours_per_day avec fallback 8h si absent ou nul."""
    val = doc.get("inovaya_hours_per_day")
    try:
        v = float(val)
        return v if v > 0 else 8.0
    except (TypeError, ValueError):
        return 8.0


def _get_daily_threshold():
    """Lit inovaya_daily_hours_threshold depuis System Settings (défaut 8h)."""
    val = frappe.db.get_single_value(
        "System Settings", "inovaya_daily_hours_threshold"
    )
    try:
        return float(val) if val else 8.0
    except (TypeError, ValueError):
        return 8.0


def _get_assigned_users(doc):
    """
    Retourne la liste des users assignés au document (nom Frappe, pas email).

    Frappe v16 : le champ _assign est géré par l'assignation (sidebar "Assign To").
    Lors d'un save depuis le formulaire web, _assign peut être absent du payload
    si l'utilisateur n'a pas touché aux assignations. Dans ce cas, on lit la valeur
    courante depuis la base de données (fallback DB).
    """
    if doc.doctype == "Annexe Task":
        return [doc.assigned_to] if doc.assigned_to else []

    # Valeur dans le payload de sauvegarde
    assign_val = doc.get("_assign")

    # Fallback DB : si vide et document existant → lire depuis tabTask
    if not assign_val and doc.name:
        try:
            assign_val = frappe.db.get_value("Task", doc.name, "_assign")
        except Exception:
            pass

    try:
        return json.loads(assign_val or "[]")
    except (ValueError, TypeError):
        return []


def _get_doc_date_range(doc):
    """Retourne (start_str, end_str) en 'YYYY-MM-DD', ou (None, None) si incomplet."""
    start = doc.get("exp_start_date")
    end   = doc.get("exp_end_date")
    if not start or not end:
        return None, None
    return str(frappe.utils.getdate(start)), str(frappe.utils.getdate(end))


def _find_conflicts_for_user(doc, user_name, start_str, end_str, doc_hours, threshold):
    """
    Retourne les Task et Annexe Task chevauchant [start_str, end_str] pour user_name
    dont doc_hours + leurs inovaya_hours_per_day > threshold.
    COALESCE(NULLIF(..., 0), 8.0) : fallback 8h/j si champ NULL ou 0.
    LIMIT 10 par table (voir BACKLOG B05).
    Limitation pairwise documentée en B29.
    """
    exclude = doc.name or ""
    results = []

    # Task — chevauchement via _assign LIKE (granularité jour : DATE())
    for row in frappe.db.sql(
        """
        SELECT subject,
               project,
               DATE(exp_start_date) AS start_date,
               DATE(exp_end_date)   AS end_date,
               COALESCE(NULLIF(inovaya_hours_per_day, 0), 8.0) AS hours_per_day
        FROM `tabTask`
        WHERE name              != %(exclude)s
          AND is_template        = 0
          AND _assign             LIKE %(pattern)s
          AND DATE(exp_end_date)   >= %(start)s
          AND DATE(exp_start_date) <= %(end)s
        LIMIT 10
        """,
        {
            "exclude": exclude,
            "pattern": f'%"{user_name}"%',
            "start":   start_str,
            "end":     end_str,
        },
        as_dict=True,
    ):
        if doc_hours + row["hours_per_day"] > threshold:
            row["source_doctype"] = "Task"
            row["total_hours"]    = doc_hours + row["hours_per_day"]
            results.append(row)

    # Annexe Task — chevauchement via assigned_to (Date : comparaison directe sans DATE())
    for row in frappe.db.sql(
        """
        SELECT subject,
               ''              AS project,
               exp_start_date  AS start_date,
               exp_end_date    AS end_date,
               COALESCE(NULLIF(inovaya_hours_per_day, 0), 8.0) AS hours_per_day
        FROM `tabAnnexe Task`
        WHERE name          != %(exclude)s
          AND assigned_to    = %(user)s
          AND exp_start_date IS NOT NULL
          AND exp_end_date    >= %(start)s
          AND exp_start_date  <= %(end)s
        LIMIT 10
        """,
        {
            "exclude": exclude,
            "user":    user_name,
            "start":   start_str,
            "end":     end_str,
        },
        as_dict=True,
    ):
        if doc_hours + row["hours_per_day"] > threshold:
            row["source_doctype"] = "Annexe Task"
            row["total_hours"]    = doc_hours + row["hours_per_day"]
            results.append(row)

    return results


def _fmt_date(val):
    """Formate une valeur date en 'jj/mm'."""
    try:
        d = frappe.utils.getdate(val)
        return f"{d.day:02d}/{d.month:02d}"
    except Exception:
        return str(val)


def _check_planning_conflicts(doc):
    """
    B05 — Blocage dur si charge journalière cumulée > seuil.
    Logique pairwise : nouvelle tâche vs chaque tâche existante.
    Seuil lu depuis System Settings.inovaya_daily_hours_threshold (défaut 8h).
    Limitation pairwise documentée en B29 (Phase 3).
    """
    if frappe.flags.in_import or frappe.flags.in_migrate or frappe.flags.in_test:
        return

    if doc.get("is_template"):
        return  # tâches-modèles hors périmètre

    users = _get_assigned_users(doc)
    if not users:
        return  # early-exit O(1) — cas le plus fréquent en pratique

    start_str, end_str = _get_doc_date_range(doc)
    if not start_str or not end_str:
        return  # dates incomplètes → pas de détection

    doc_hours = _get_daily_hours(doc)
    threshold = _get_daily_threshold()

    conflict_lines = []
    for user_name in users:
        full_name = (
            frappe.db.get_value("User", user_name, "full_name") or user_name
        )
        for c in _find_conflicts_for_user(
            doc, user_name, start_str, end_str, doc_hours, threshold
        ):
            d_from = _fmt_date(c["start_date"])
            d_to   = _fmt_date(c["end_date"])
            if c["source_doctype"] == "Annexe Task":
                ref = f"« {c['subject']} » (Tâche Annexe)"
            elif c["project"]:
                ref = f"« {c['subject']} » ({c['project']})"
            else:
                ref = f"« {c['subject']} » (tâche sans projet)"
            conflict_lines.append(
                f"• {full_name} : {doc_hours}h (cette tâche)"
                f" + {c['hours_per_day']}h {ref}"
                f" = {c['total_hours']}h/j > {threshold}h"
                f" — du {d_from} au {d_to}."
            )

    if conflict_lines:
        msg = (
            _("Dépassement de charge journalière détecté :") + "<br>"
            + "<br>".join(conflict_lines)
        )
        frappe.throw(msg, title=_("Conflit de planning — B05"))


# ---------------------------------------------------------------------------
# B06 — Alimentation automatique de Timesheet draft lors d'une assignation Task
# ---------------------------------------------------------------------------

def _compute_new_assignees(doc):
    """
    Compare _assign du payload (doc) avec la valeur DB avant save.
    Stocke les nouveaux users dans doc._b06_new_users pour after_save.
    Silencieux si frappe.flags.in_import/in_migrate/in_test.
    """
    doc._b06_new_users = []

    if frappe.flags.in_import or frappe.flags.in_migrate or frappe.flags.in_test:
        return
    if doc.get("is_template"):
        return
    if not doc.get("exp_start_date") or not doc.get("exp_end_date"):
        return

    # _assign du payload courant (absent si l'utilisateur ne l'a pas modifié)
    new_assign_raw = doc.get("_assign")
    if not new_assign_raw:
        return

    try:
        new_users = set(json.loads(new_assign_raw))
    except (ValueError, TypeError):
        return

    if not new_users:
        return

    # Ancien _assign en DB (avant ce save — lu avant la transaction de mise à jour)
    if doc.name and not doc.is_new():
        old_raw = frappe.db.get_value("Task", doc.name, "_assign") or "[]"
    else:
        old_raw = "[]"  # Nouveau document → tous les users sont "nouveaux"

    try:
        old_users = set(json.loads(old_raw))
    except (ValueError, TypeError):
        old_users = set()

    doc._b06_new_users = list(new_users - old_users)


def _create_draft_timesheets_b06(doc, new_users):
    """
    Crée un Timesheet en draft (docstatus=0) pour chaque nouvel assigné.
    Idempotent : skip si un Timesheet draft existe déjà pour (task, employee).

    Plage horaire : date de début de la tâche, 09:00 → 09:00+hours (même jour).
    La plage est intentionnellement limitée à une journée pour éviter les
    conflits de chevauchement ERPNext (OverlapError). Si un chevauchement est
    détecté malgré tout, on log un warning sans lever d'exception (bloquant).
    Le collaborateur ajuste le draft dans l'UI.
    """
    company = frappe.db.get_default("Company") or frappe.db.get_value("Company", {}, "name")

    # Heures planifiées : expected_time de la tâche, fallback inovaya_hours_per_day
    hours = float(doc.get("expected_time") or 0) or _get_daily_hours(doc)

    # Plage d'1 jour (09:00 → 09:00 + hours) pour minimiser les OverlapErrors
    from datetime import timedelta as _td
    start_date = frappe.utils.getdate(doc.exp_start_date)
    start_dt   = f"{start_date} 09:00:00"
    end_dt     = str(
        frappe.utils.get_datetime(start_dt) + _td(hours=hours)
    )

    for user_email in new_users:
        emp_id = frappe.db.get_value("Employee", {"user_id": user_email}, "name")
        if not emp_id:
            frappe.logger().warning(
                "[B06] Aucun Employee pour user '%s' — Timesheet non créée.", user_email
            )
            continue

        # Idempotence : Timesheet draft déjà existante pour cette tâche + employé ?
        already = frappe.db.sql(
            """
            SELECT td.parent
            FROM `tabTimesheet Detail` td
            INNER JOIN `tabTimesheet` ts ON ts.name = td.parent
            WHERE td.task = %s AND ts.employee = %s AND ts.docstatus = 0
            LIMIT 1
            """,
            (doc.name, emp_id),
        )
        if already:
            frappe.logger().info(
                "[B06] Timesheet draft déjà existante — task=%s employee=%s, skip.",
                doc.name, emp_id,
            )
            continue

        emp_name = frappe.db.get_value("Employee", emp_id, "employee_name") or user_email
        try:
            # Insertion directe en SQL pour bypasser la validation d'overlap ERPNext.
            # Les Timesheets B06 sont des drafts de planification (non soumises) :
            # le collaborateur les ajuste librement dans l'UI.
            # L'ORM ERPNext (Projects Settings.ignore_employee_time_overlap) est
            # contourné volontairement — comportement documenté en ERPNEXT_V16_REALITY.md.
            ts_name = frappe.generate_hash(length=10)
            now_str = str(frappe.utils.now_datetime())
            user    = frappe.session.user or "Administrator"

            frappe.db.sql("""
                INSERT INTO `tabTimesheet`
                    (name, creation, modified, modified_by, owner, docstatus,
                     employee, employee_name, company, parent_project, total_hours)
                VALUES
                    (%s, %s, %s, %s, %s, 0,
                     %s, %s, %s, %s, %s)
            """, (ts_name, now_str, now_str, user, user,
                  emp_id, emp_name, company, doc.project or None, hours))

            td_name = frappe.generate_hash(length=10)
            frappe.db.sql("""
                INSERT INTO `tabTimesheet Detail`
                    (name, creation, modified, modified_by, owner, docstatus,
                     parent, parentfield, parenttype,
                     task, project, from_time, to_time,
                     hours, expected_hours, is_billable, completed, description, idx)
                VALUES
                    (%s, %s, %s, %s, %s, 0,
                     %s, 'time_logs', 'Timesheet',
                     %s, %s, %s, %s,
                     %s, %s, 0, 0, %s, 1)
            """, (td_name, now_str, now_str, user, user,
                  ts_name,
                  doc.name, doc.project or None, start_dt, end_dt,
                  hours, hours, f"[B06] Planification auto — {doc.subject}"))

            frappe.db.commit()
            frappe.logger().info(
                "[B06] Timesheet draft %s créée (SQL direct) : employee=%s task=%s.",
                ts_name, emp_name, doc.name,
            )
            frappe.msgprint(
                f"[B06] Timesheet draft créée pour {emp_name} — « {doc.subject} ».",
                indicator="green",
                alert=True,
            )
        except Exception as exc:
            frappe.logger().error(
                "[B06] Erreur création Timesheet — employee=%s task=%s : %s",
                emp_id, doc.name, str(exc),
            )


def after_save(doc, method=None):
    """
    B06 — Crée des Timesheets draft pour les utilisateurs nouvellement assignés.
    Uniquement sur Task (pas Annexe Task).
    """
    if doc.doctype != "Task":
        return
    new_users = getattr(doc, "_b06_new_users", [])
    if not new_users:
        return
    _create_draft_timesheets_b06(doc, new_users)


# ---------------------------------------------------------------------------
# Hook principal (appelé par doc_events sur Task et Annexe Task)
# ---------------------------------------------------------------------------

def before_save(doc, method=None):
    """
    B04 Eisenhower (non bloquant)
    B05 conflits de planning (bloquant si détecté)
    B06 pré-calcul nouveaux assignés (stocké pour after_save)
    """
    _run_eisenhower(doc)
    _check_planning_conflicts(doc)
    if doc.doctype == "Task":
        _compute_new_assignees(doc)
