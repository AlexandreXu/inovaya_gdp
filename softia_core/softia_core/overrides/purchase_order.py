"""
B14 — Alertes retard commande → impact planning.

Différences vs inovaya_gdp : inovaya_linked_task → softia_linked_task,
sujets email paramétrés via System Settings softia_app_name.
"""
import frappe
from frappe.utils import getdate


def _get_app_name():
    return frappe.db.get_single_value("System Settings", "softia_app_name") or "Softia ERP"


def before_save(doc, method=None):
    doc._b14_alert_data = None
    if frappe.flags.in_import or frappe.flags.in_migrate or frappe.flags.in_test:
        return

    task_name = doc.get("softia_linked_task")
    if not task_name:
        return

    new_schedule_date = doc.get("schedule_date")
    if not new_schedule_date:
        return

    old_schedule_date = None
    if doc.name and not doc.is_new():
        old_schedule_date = frappe.db.get_value("Purchase Order", doc.name, "schedule_date")

    new_date = getdate(new_schedule_date)
    old_date = getdate(old_schedule_date) if old_schedule_date else None

    date_changed = (old_date != new_date)
    if not date_changed and doc.get("docstatus") != 0:
        return

    task = frappe.db.get_value("Task", task_name,
        ["name", "subject", "project", "exp_end_date"], as_dict=True)
    if not task or not task.exp_end_date:
        return

    task_end_date = getdate(task.exp_end_date)
    if new_date <= task_end_date:
        return

    doc._b14_alert_data = {
        "task":     task,
        "old_date": str(old_date) if old_date else None,
        "new_date": str(new_date),
        "task_end": str(task_end_date),
        "supplier": doc.get("supplier_name") or doc.get("supplier") or "—",
        "items":    _get_po_items(doc),
    }


def on_update(doc, method=None):
    data = getattr(doc, "_b14_alert_data", None)
    if not data:
        return
    _send_po_delay_alert(doc, data)


def on_submit(doc, method=None):
    if frappe.flags.in_import or frappe.flags.in_migrate or frappe.flags.in_test:
        return
    before_save(doc)
    data = getattr(doc, "_b14_alert_data", None)
    if data:
        _send_po_delay_alert(doc, data)


def _get_po_items(doc):
    items = []
    for it in (doc.get("items") or []):
        name = getattr(it, "item_name", None) or getattr(it, "item_code", None)
        if name:
            items.append(name)
    if not items and doc.name:
        rows = frappe.db.sql(
            "SELECT item_name FROM `tabPurchase Order Item` WHERE parent=%s LIMIT 5",
            (doc.name,), as_dict=True,
        )
        items = [r.item_name for r in rows if r.item_name]
    return items or ["—"]


def _get_project_owner_email(project_name):
    if not project_name:
        return None
    owner = frappe.db.get_value("Project", project_name, "owner")
    if not owner:
        return None
    return frappe.db.get_value("User", owner, "email") or owner


def _get_task_manager_emails(task_name):
    import json
    assign_raw = frappe.db.get_value("Task", task_name, "_assign") or "[]"
    try:
        user_emails = json.loads(assign_raw)
    except (ValueError, TypeError):
        user_emails = []
    manager_emails = set()
    for user_email in user_emails:
        emp_id = frappe.db.get_value("Employee", {"user_id": user_email}, "name")
        if not emp_id:
            continue
        reports_to = frappe.db.get_value("Employee", emp_id, "reports_to")
        if not reports_to:
            continue
        mgr_user = frappe.db.get_value("Employee", reports_to, "user_id")
        if not mgr_user:
            continue
        mgr_email = frappe.db.get_value("User", mgr_user, "email") or mgr_user
        if mgr_email:
            manager_emails.add(mgr_email)
    return manager_emails


def _send_po_delay_alert(doc, data):
    app_name = _get_app_name()
    task   = data["task"]
    items  = "<br>".join(f"• {i}" for i in data["items"])
    delay  = (getdate(data["new_date"]) - getdate(data["task_end"])).days
    delta_label = (f"({data['old_date']} → {data['new_date']})" if data["old_date"]
                   else f"(date {data['new_date']})")
    message = (
        "<p>Bonjour,</p>"
        f"<p>La commande fournisseur <strong>{doc.name}</strong> a une date de livraison "
        "qui dépasse l'échéance de la tâche projet liée.</p>"
        "<table style='border-collapse:collapse;font-size:14px;margin:8px 0;'>"
        f"<tr><td style='padding:4px 12px;font-weight:bold;'>Fournisseur</td>"
        f"<td style='padding:4px 12px;'>{data['supplier']}</td></tr>"
        f"<tr><td style='padding:4px 12px;font-weight:bold;'>Article(s)</td>"
        f"<td style='padding:4px 12px;'>{items}</td></tr>"
        f"<tr><td style='padding:4px 12px;font-weight:bold;'>Date livraison PO</td>"
        f"<td style='padding:4px 12px;'>{data['new_date']} {delta_label}</td></tr>"
        f"<tr><td style='padding:4px 12px;font-weight:bold;'>Échéance tâche liée</td>"
        f"<td style='padding:4px 12px;'>{data['task_end']}</td></tr>"
        f"<tr><td style='padding:4px 12px;font-weight:bold;color:#e74c3c;'>Retard</td>"
        f"<td style='padding:4px 12px;color:#e74c3c;font-weight:bold;'>+{delay} jour(s)</td></tr>"
        "</table>"
        f"<p><strong>Tâche impactée</strong> : {task.subject} ({task.name})</p>"
        f"<p><strong>Projet</strong> : {task.project or '—'}</p>"
        f"<p style='color:#888;font-size:12px;'>Message automatique {app_name} (B14). "
        "Aucune action automatique — vérification manuelle requise.</p>"
    )
    recipients = set()
    owner_email = _get_project_owner_email(task.project)
    if owner_email:
        recipients.add(owner_email)
    recipients.update(_get_task_manager_emails(task.name))
    if not recipients:
        frappe.logger().warning("[B14] PO %s : aucun destinataire.", doc.name)
        return
    subject = f"[{app_name}] Retard livraison PO {doc.name} — impact tâche {task.name}"
    frappe.sendmail(recipients=list(recipients), subject=subject, message=message, now=True)
    frappe.logger().info("[B14] Alerte retard PO %s (+%d j) envoyée → %s.",
                         doc.name, delay, list(recipients))
