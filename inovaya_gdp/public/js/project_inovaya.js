// B17 — Jauges budgétaires dynamiques
// Affiche un indicateur coloré « % budget consommé » dans le dashboard
// de la fiche Projet InovaYa, à partir des lignes Budget Detaille InovaYa.
//
// Règles couleur :
//   vert   → consommé ≤ 80 %
//   orange → 80 % < consommé ≤ 100 %
//   rouge  → consommé > 100 %
//   gris   → aucune ligne de budget ou prévu = 0 €

frappe.ui.form.on("Project", {

    refresh: function(frm) {
        // Ne s'applique pas aux nouveaux docs non encore sauvegardés
        if (frm.doc.__islocal) return;
        _inovaya_refresh_budget_gauge(frm);
    }

});

function _inovaya_refresh_budget_gauge(frm) {
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Budget Detaille InovaYa",
            filters: [
                ["parent",     "=", frm.doc.name],
                ["parenttype", "=", "Project"],
            ],
            fields: ["amount_planned", "amount_actual"],
            limit_page_length: 100,
        },
        callback: function(r) {
            var rows = (r && r.message) ? r.message : [];

            // Cas : aucune ligne de budget
            if (!rows.length) {
                frm.dashboard.add_indicator(__("Budget : non renseigné"), "grey");
                return;
            }

            // Agrégation
            var total_planned = 0;
            var total_actual  = 0;
            rows.forEach(function(row) {
                total_planned += (row.amount_planned || 0);
                total_actual  += (row.amount_actual  || 0);
            });

            // Cas : prévu = 0 (budget saisi mais vide)
            if (total_planned === 0) {
                frm.dashboard.add_indicator(__("Budget prévu : 0 €"), "grey");
                return;
            }

            // Calcul %
            var pct   = Math.round(total_actual / total_planned * 100);
            var color = pct > 100 ? "red" : pct > 80 ? "orange" : "green";

            // Formatage montants
            var p_fmt = frappe.format(total_planned, {fieldtype: "Currency"});
            var a_fmt = frappe.format(total_actual,  {fieldtype: "Currency"});

            // Indicateur dans le dashboard du formulaire
            frm.dashboard.add_indicator(
                __("Budget {0}% consommé — {1} réalisé / {2} prévu", [pct, a_fmt, p_fmt]),
                color
            );
        }
    });
}
