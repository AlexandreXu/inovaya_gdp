// B01 — Plan de charge manager
// Filtres, formatage couleur Charge % (rouge > 100%, orange > 80%)

frappe.query_reports["Plan de Charge InovaYa"] = {

    filters: [
        {
            fieldname: "from_date",
            label: __("Du"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.month_start(),
        },
        {
            fieldname: "to_date",
            label: __("Au"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.month_end(),
        },
        {
            fieldname: "employee",
            label: __("Collaborateur"),
            fieldtype: "Link",
            options: "User",
        },
    ],

    // Formatage conditionnel de la colonne Charge %
    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (column.fieldname === "charge_pct" && data) {
            var pct = data.charge_pct;
            if (pct > 100) {
                value = "<span style=\"color:red;font-weight:bold\">" + value + "</span>";
            } else if (pct > 80) {
                value = "<span style=\"color:orange;font-weight:bold\">" + value + "</span>";
            }
        }
        return value;
    },
};
