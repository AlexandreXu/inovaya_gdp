// B08 — Heures par Verticale Métier InovaYa
// Rapport Script Report — filtres et mise en forme colonnes.
frappe.query_reports["Heures par Verticale InovaYa"] = {
    "filters": [
        {
            fieldname: "from_date",
            label: __("Du"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            reqd: 1,
        },
        {
            fieldname: "to_date",
            label: __("Au"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1,
        },
        {
            fieldname: "employee",
            label: __("Collaborateur"),
            fieldtype: "Link",
            options: "Employee",
        },
        {
            fieldname: "verticale",
            label: __("Verticale Métier"),
            fieldtype: "Select",
            options: "\nTraitement Eau Industriel\nTEE Collectivités\nR&D\nDigital\nTransversal",
        },
    ],

    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        // Lignes sans verticale : afficher en gris
        if (column.fieldname === "verticale" && (!data || !data.verticale)) {
            value = `<span style="color:#aaa;font-style:italic;">(non renseignée)</span>`;
        }
        // Heures > 40h par semaine : rouge
        if (column.fieldname === "heures_realisees" && data && data.heures_realisees > 40) {
            value = `<span style="color:#e74c3c;font-weight:bold;">${data.heures_realisees}</span>`;
        }
        return value;
    },
};
