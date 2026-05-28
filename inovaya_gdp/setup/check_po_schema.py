"""
Vérification schéma Purchase Order + Dashboard Charts v16 pour Sprint C.
bench --site inovaya.localhost execute inovaya_gdp.setup.check_po_schema.run
"""
import frappe


def run():
    # ── 1. PO schema clés ─────────────────────────────────────────────────
    print("\n=== PURCHASE ORDER — CHAMPS CLÉS ===")
    cols = frappe.db.sql("DESCRIBE `tabPurchase Order`", as_dict=True)
    keys = ['name', 'status', 'schedule_date', 'supplier', 'supplier_name',
            'inovaya_linked_task', 'transaction_date', 'owner']
    for c in cols:
        if c['Field'] in keys:
            print(f"  {c['Field']} ({c['Type']})")

    # ── 2. PO Items schema ────────────────────────────────────────────────
    print("\n=== PURCHASE ORDER ITEM — CHAMPS CLÉS ===")
    cols2 = frappe.db.sql("DESCRIBE `tabPurchase Order Item`", as_dict=True)
    keys2 = ['item_code', 'item_name', 'qty', 'schedule_date', 'project']
    for c in cols2:
        if c['Field'] in keys2:
            print(f"  {c['Field']} ({c['Type']})")

    # ── 3. PO en démo ─────────────────────────────────────────────────────
    print("\n=== PURCHASE ORDERS EN BASE ===")
    pos = frappe.db.sql("""
        SELECT po.name, po.status, po.supplier_name, po.schedule_date,
               po.inovaya_linked_task, po.docstatus
        FROM `tabPurchase Order` po
        LIMIT 5
    """, as_dict=True)
    for p in pos:
        print(f"  {p.name} | {p.status} | {p.supplier_name} | schedule={p.schedule_date} "
              f"| task={p.inovaya_linked_task} | docstatus={p.docstatus}")

    # ── 4. Tâche liée à la PO ─────────────────────────────────────────────
    print("\n=== TÂCHE LIÉE AU PO ===")
    for p in pos:
        if p.inovaya_linked_task:
            t = frappe.db.get_value("Task", p.inovaya_linked_task,
                                     ["name", "subject", "project", "exp_end_date"], as_dict=True)
            if t:
                print(f"  PO {p.name} → Task {t.name} | {t.subject} | project={t.project} | exp_end={t.exp_end_date}")

    # ── 5. Dashboard Chart — types disponibles v16 ─────────────────────────
    print("\n=== DASHBOARD CHART TYPES V16 ===")
    chart_cols = frappe.db.sql("DESCRIBE `tabDashboard Chart`", as_dict=True)
    relevant = ['chart_type', 'document_type', 'based_on', 'group_by_type',
                'filters_json', 'time_interval', 'chart_name']
    for c in chart_cols:
        if c['Field'] in relevant:
            print(f"  {c['Field']} ({c['Type']})")

    print("\n=== DASHBOARD CHARTS EXISTANTS ===")
    charts = frappe.db.sql(
        "SELECT chart_name, chart_type, document_type FROM `tabDashboard Chart` ORDER BY chart_name LIMIT 10",
        as_dict=True,
    )
    for c in charts:
        print(f"  {c.chart_name} | type={c.chart_type} | doctype={c.document_type}")

    # ── 6. Workspace structure ────────────────────────────────────────────
    print("\n=== WORKSPACE INOVAYA EXISTANT ===")
    ws = frappe.db.sql(
        "SELECT name, module, public FROM `tabWorkspace` WHERE name LIKE 'InovaYa%'",
        as_dict=True,
    )
    for w in ws:
        print(f"  {w.name} | module={w.module} | public={w.public}")

    # ── 7. Document Chart Field (shortcut) ────────────────────────────────
    print("\n=== WORKSPACE LINK TABLE ===")
    link_cols = frappe.db.sql("DESCRIBE `tabWorkspace Link`", as_dict=True)
    for c in link_cols:
        print(f"  {c['Field']} ({c['Type']})")
    print()
