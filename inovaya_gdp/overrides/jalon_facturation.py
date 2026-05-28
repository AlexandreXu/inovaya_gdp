"""
B19 — Génération automatique Sales Invoice draft depuis un Jalon Facturation InovaYa.
Déclenchement : statut passe à "Validé" ET sales_invoice encore vide.
Doc event : on_update sur "Jalon Facturation InovaYa".

Note POC : si.flags.ignore_mandatory + ignore_validate = True sur l'insert →
la facture draft est créée sans item_code (Finance complète avant soumission).
frappe.db.set_value avec update_modified=False pour écrire sales_invoice
sans déclencher une seconde passe on_update.
"""
import frappe
from frappe import _


def on_update(doc, method=None):
    """
    B19 — Crée une Sales Invoice draft quand le statut passe à "Validé".
    Idempotent : sort immédiatement si sales_invoice déjà renseigné
    ou si le statut était déjà "Validé" avant cette save.
    """

    # ── Ignorer les contextes système ─────────────────────────────
    if frappe.flags.in_import or frappe.flags.in_migrate or frappe.flags.in_test:
        return

    # ── [1] Détecter la transition vers "Validé" ──────────────────
    if doc.status != "Validé":
        return

    # Idempotence — éviter les doublons si sales_invoice déjà créée
    if doc.sales_invoice:
        return

    # Idempotence — statut était déjà "Validé" avant cette save
    doc_before = doc.get_doc_before_save()
    if doc_before and doc_before.status == "Validé":
        return

    # ── [2] Vérifier la présence du client sur le projet ──────────
    project = frappe.get_doc("Project", doc.project)
    if not project.customer:
        frappe.msgprint(
            _(
                "Aucun client renseigné sur le projet {0} — "
                "la facture n'a pas pu être générée automatiquement."
            ).format(frappe.bold(doc.project)),
            title=_("Facture non générée — B19"),
            indicator="orange",
        )
        return

    # ── [3] Société et devise ─────────────────────────────────────
    company = (
        frappe.defaults.get_user_default("company")
        or frappe.db.get_single_value("Global Defaults", "default_company")
    )
    currency = (
        frappe.db.get_value("Customer", project.customer, "default_currency")
        or frappe.db.get_single_value("Global Defaults", "default_currency")
        or "EUR"
    )

    # ── [4] Créer la Sales Invoice draft ──────────────────────────
    si = frappe.get_doc({
        "doctype": "Sales Invoice",
        "customer": project.customer,
        "company": company,
        "currency": currency,
        "project": doc.project,
        "items": [
            {
                "item_name":   doc.label,
                "description": "Jalon : {} — Projet : {}".format(
                    doc.label, doc.project
                ),
                "qty":  1,
                "rate": doc.amount or 0,
                "uom":  "Nos",          # vérifié présent (stock_uom par défaut)
            }
        ],
    })

    # POC : draft sans item_code — Finance doit compléter avant soumission
    si.flags.ignore_mandatory = True
    si.flags.ignore_validate  = True
    si.insert(ignore_permissions=True)

    # ── [5] Lier la facture au jalon sans déclencher on_update ────
    # update_modified=False → pas de mise à jour modified/modified_by
    # → pas de re-trigger on_update → pas de boucle infinie
    frappe.db.set_value(
        "Jalon Facturation InovaYa",
        doc.name,
        "sales_invoice",
        si.name,
        update_modified=False,
    )
    doc.sales_invoice = si.name  # cohérence du doc en mémoire

    # ── [6] Confirmation utilisateur ──────────────────────────────
    frappe.msgprint(
        _("Facture draft {0} créée pour le jalon {1}.").format(
            frappe.bold(si.name), frappe.bold(doc.label)
        ),
        title=_("Facture générée — B19"),
        indicator="green",
    )
