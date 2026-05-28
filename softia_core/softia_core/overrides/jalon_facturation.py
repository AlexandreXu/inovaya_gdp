"""
B19 — Génération automatique Sales Invoice draft depuis un Jalon Facturation.
DocType : "Jalon Facturation" (générique — renommé depuis "Jalon Facturation InovaYa").
"""
import frappe
from frappe import _


def on_update(doc, method=None):
    if frappe.flags.in_import or frappe.flags.in_migrate or frappe.flags.in_test:
        return
    if doc.status != "Validé":
        return
    if doc.sales_invoice:
        return
    doc_before = doc.get_doc_before_save()
    if doc_before and doc_before.status == "Validé":
        return

    project = frappe.get_doc("Project", doc.project)
    if not project.customer:
        frappe.msgprint(
            _("Aucun client renseigné sur le projet {0} — "
              "la facture n'a pas pu être générée automatiquement.").format(
                frappe.bold(doc.project)),
            title=_("Facture non générée — B19"),
            indicator="orange",
        )
        return

    company = (
        frappe.defaults.get_user_default("company")
        or frappe.db.get_single_value("Global Defaults", "default_company")
    )
    currency = (
        frappe.db.get_value("Customer", project.customer, "default_currency")
        or frappe.db.get_single_value("Global Defaults", "default_currency")
        or "EUR"
    )

    si = frappe.get_doc({
        "doctype": "Sales Invoice",
        "customer": project.customer,
        "company": company,
        "currency": currency,
        "project": doc.project,
        "items": [{
            "item_name":   doc.label,
            "description": f"Jalon : {doc.label} — Projet : {doc.project}",
            "qty":  1,
            "rate": doc.amount or 0,
            "uom":  "Nos",
        }],
    })
    si.flags.ignore_mandatory = True
    si.flags.ignore_validate  = True
    si.insert(ignore_permissions=True)

    frappe.db.set_value(
        "Jalon Facturation", doc.name, "sales_invoice", si.name,
        update_modified=False,
    )
    doc.sales_invoice = si.name

    frappe.msgprint(
        _("Facture draft {0} créée pour le jalon {1}.").format(
            frappe.bold(si.name), frappe.bold(doc.label)),
        title=_("Facture générée — B19"),
        indicator="green",
    )
