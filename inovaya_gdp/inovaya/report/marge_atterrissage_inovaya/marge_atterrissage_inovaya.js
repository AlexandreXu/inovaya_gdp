// B21 — Rapport "Marge Atterrissage InovaYa"
// Filtre : Project (obligatoire)
// Formatter : séparateur visuel, gras sur résultats,
//             rouge/vert sur marges, % sécurisé sur Atterrissage

frappe.query_reports["Marge Atterrissage InovaYa"] = {
    filters: [
        {
            fieldname: "project",
            label: __("Projet"),
            fieldtype: "Link",
            options: "Project",
            reqd: 1
        }
    ],

    formatter: function (value, row, column, data, default_formatter) {
        if (!data) return default_formatter(value, row, column, data);

        // ── Ligne séparateur ──────────────────────────────────────────────
        if (data._is_sep) {
            return column.fieldname === "poste"
                ? `<span style="display:block;border-top:1px solid var(--gray-300);margin:4px 0">&nbsp;</span>`
                : "";
        }

        // ── Colonne "poste" ───────────────────────────────────────────────
        if (column.fieldname === "poste") {
            const txt = value || "";
            return data._bold ? `<b>${txt}</b>` : txt;
        }

        // ── Colonne "montant" ─────────────────────────────────────────────

        // Atterrissage % — override totale pour afficher X.X % (pas en €)
        // parseFloat avec fallback sécurisé : nettoie tout caractère non numérique
        // au cas où Frappe formate la valeur avant de la passer au formatter.
        if (data._is_pct) {
            const raw = String(data.montant == null ? "" : data.montant);
            const pct = parseFloat(raw.replace(/[^0-9.\-]/g, ""));
            if (isNaN(pct)) return "—";
            const display = pct.toFixed(1) + " %";
            if (data._color === "rouge")
                return `<b><span style="color:var(--red-500)">${display}</span></b>`;
            if (data._color === "vert")
                return `<b><span style="color:var(--green-500)">${display}</span></b>`;
            return `<b>${display}</b>`;
        }

        // Valeur nulle → tiret
        if (value === null || value === undefined) return "—";

        let formatted = default_formatter(value, row, column, data);

        // Couleur sur marge
        if (data._color === "rouge") {
            formatted = `<span style="color:var(--red-500)">${formatted}</span>`;
        } else if (data._color === "vert") {
            formatted = `<span style="color:var(--green-500)">${formatted}</span>`;
        }

        // Gras sur lignes résultats
        if (data._bold) {
            formatted = `<b>${formatted}</b>`;
        }

        return formatted;
    }
};
