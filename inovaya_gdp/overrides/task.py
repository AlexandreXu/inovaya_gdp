"""
B04 — Priorisation automatique Eisenhower (Task + Annexe Task).

Matrice :
  Importance Haute + Urgente     → Q1 Critique   → priority = Urgent
  Importance Haute + Non urgente → Q2 Important  → priority = High
  Importance Basse + Urgente     → Q3 Déléguer   → priority = Medium
  Importance Basse + Non urgente → Q4 Reporter   → priority = Low

Seuil d'urgence : exp_end_date ≤ URGENCY_DAYS jours à partir d'aujourd'hui.
Limitation POC : urgence calculée sur échéance seule, sans tenir compte de la
durée de la tâche (Task.duration). Affiner en Phase 3 (voir BACKLOG B04).

Restriction importance : Responsable GdP, Responsable Operations, Direction Generale
  — appliquée sur Task projet uniquement.
  — Annexe Task : aucune restriction (Manager InovaYa gère librement).
"""
import frappe
from frappe import _

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
    """
    Bloque la modification de inovaya_importance aux rôles non autorisés.
    Comportement sur nouvelle tâche (pas de doc_before) : reset silencieux à Basse.
    """
    new_val = doc.get("inovaya_importance") or ""
    if not new_val or new_val == "Basse":
        return  # pas de changement vers Haute, rien à garder

    doc_before = doc.get_doc_before_save()
    old_val = (doc_before.get("inovaya_importance") if doc_before else None) or ""

    if old_val == new_val:
        return  # valeur inchangée

    user_roles = frozenset(frappe.get_roles(frappe.session.user))
    if ALLOWED_ROLES_IMPORTANCE & user_roles:
        return  # rôle autorisé

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


def before_save(doc, method=None):
    """B04 — Calcul Eisenhower sur Task projet et Annexe Task."""
    # Ignorer les tâches-modèles
    if doc.get("is_template"):
        return

    # Restriction de rôle uniquement sur les Task projet (pas Annexe Task)
    if doc.doctype == "Task":
        _guard_importance_change(doc)

    importance_haute = doc.get("inovaya_importance") == "Haute"
    end_date = _get_end_date(doc)
    urgent = _is_urgent(end_date)

    quadrant_label, priority = _MATRIX[(importance_haute, urgent)]
    urgence_str = "Urgente" if urgent else "Non urgente"

    doc.inovaya_eisenhower_info = f"{urgence_str} · {quadrant_label}"

    # Met à jour le priority natif uniquement si importance est explicitement définie
    if doc.get("inovaya_importance"):
        doc.priority = priority
