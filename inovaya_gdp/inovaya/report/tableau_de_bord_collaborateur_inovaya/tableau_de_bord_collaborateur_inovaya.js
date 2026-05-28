// B03 — Tableau de bord collaborateur avancé
// Filtres : collaborateur (reqd) + période (défaut : semaine en cours) + statut
//
// Formatage conditionnel :
//   • Ligne rouge    : is_late == 1  (échéance dépassée, tâche non terminée)
//   • Gras           : eisenhower commence par "Q1" (Critique — Faire en priorité)
//   • Orange gras    : actual_hours > allocated_hours > 0  (sur la cellule réalisé)
//   • Colonne Retard : "⚠ Retard" en rouge ou vide

frappe.query_reports["Tableau de Bord Collaborateur InovaYa"] = {

    filters: [
        {
            fieldname: "employee",
            label: __("Collaborateur"),
            fieldtype: "Link",
            options: "User",
            reqd: 1,
            // Pré-remplir avec l'utilisateur connecté
            default: frappe.session.user,
        },
        {
            fieldname: "from_date",
            label: __("Du"),
            fieldtype: "Date",
            default: frappe.datetime.week_start(),
        },
        {
            fieldname: "to_date",
            label: __("Au"),
            fieldtype: "Date",
            default: frappe.datetime.week_end(),
        },
        {
            fieldname: "status",
            label: __("Statut"),
            fieldtype: "Select",
            options: [
                { value: "",               label: __("Tous")           },
                { value: "Open",           label: __("Open")           },
                { value: "Working",        label: __("Working")        },
                { value: "Pending Review", label: __("Pending Review") },
            ],
        },
    ],

    formatter: function(value, row, column, data, default_formatter) {
        // Laisser Frappe formatter faire le travail de base (dates, floats, etc.)
        value = default_formatter(value, row, column, data);

        if (!data) return value;

        var isLate  = data.is_late == 1;
        var isQ1    = data.eisenhower && data.eisenhower.indexOf("Q1") === 0;
        var isOver  = data.actual_hours > 0
                      && data.actual_hours > data.allocated_hours;

        // ── Colonne "Retard" : rendu personnalisé ──────────────────────────
        if (column.fieldname === "is_late") {
            return isLate
                ? "<span style=\"color:red;font-weight:bold\">⚠ Retard</span>"
                : "";
        }

        // ── Colonne "Temps réalisé" : "—" pour Annexe Tasks (pas de Timesheet) ─
        if (column.fieldname === "actual_hours" && data.is_annexe == 1) {
            return "<span style=\"color:#aaa\">—</span>";
        }

        // ── Colonne "Temps réalisé" : orange si dépassement (hors retard) ─
        if (column.fieldname === "actual_hours" && isOver && !isLate) {
            return "<span style=\"color:darkorange;font-weight:bold\">"
                   + value + "</span>";
        }

        // ── Appliquer couleur rouge (retard) + gras (Q1) ──────────────────
        // Les deux peuvent se combiner : tâche Q1 en retard → rouge + gras
        if (isLate && isQ1
            && (column.fieldname === "task_subject"
                || column.fieldname === "eisenhower")) {
            return "<span style=\"color:red\"><b>" + value + "</b></span>";
        }
        if (isLate) {
            return "<span style=\"color:red\">" + value + "</span>";
        }
        if (isQ1
            && (column.fieldname === "task_subject"
                || column.fieldname === "eisenhower")) {
            return "<b>" + value + "</b>";
        }

        return value;
    },
};
