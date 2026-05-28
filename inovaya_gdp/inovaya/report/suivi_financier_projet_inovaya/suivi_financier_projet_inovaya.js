// B16 — Vue financière prévu / engagé / réalisé par projet.
// Filtres : Project (obligatoire), plage de dates (optionnel).
// Formatter : tiret sur les cellules sans données per-catégorie,
//             rouge sur dépassement de budget.

frappe.query_reports["Suivi Financier Projet InovaYa"] = {
    filters: [
        {
            fieldname: "project",
            label: __("Projet"),
            fieldtype: "Link",
            options: "Project",
            reqd: 1
        },
        {
            fieldname: "from_date",
            label: __("Du"),
            fieldtype: "Date"
        },
        {
            fieldname: "to_date",
            label: __("Au"),
            fieldtype: "Date"
        }
    ],

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (!data) return value;

        // Ligne TOTAL → gras
        if (data.is_total) {
            value = `<b>${value}</b>`;
        }

        // Colonnes sans données sur les lignes catégorie → tiret
        const no_data_cols = ["amount_engaged", "amount_actual", "variance", "pct_consumed"];
        if (!data.is_total && no_data_cols.includes(column.fieldname)) {
            return "—";
        }

        // Dépassement budget (écart négatif = réalisé > prévu) → rouge
        if (column.fieldname === "variance" && data.variance < 0) {
            value = `<span style="color:var(--red-500)">${value}</span>`;
        }

        // Consommation > 100 % → rouge
        if (column.fieldname === "pct_consumed" && data.pct_consumed > 100) {
            value = `<span style="color:var(--red-500)">${value}</span>`;
        }

        return value;
    }
};
