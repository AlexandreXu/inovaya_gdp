// B18 — Customisation formulaire Jalon Facturation InovaYa
// Filtre le champ "task" (Tâche liée) par le projet sélectionné.
// Réinitialise la tâche si le projet change après qu'une tâche ait été choisie.

frappe.ui.form.on("Jalon Facturation InovaYa", {

    // Applique le filtre dès l'ouverture du formulaire
    refresh: function (frm) {
        frm.set_query("task", function () {
            return {
                filters: {
                    project: frm.doc.project || "",
                    is_template: 0,
                }
            };
        });
    },

    // Réapplique le filtre et vide la tâche si le projet change
    project: function (frm) {
        frm.set_query("task", function () {
            return {
                filters: {
                    project: frm.doc.project || "",
                    is_template: 0,
                }
            };
        });

        // Vider la tâche si elle ne correspond plus au nouveau projet
        if (frm.doc.task) {
            frappe.db.get_value("Task", frm.doc.task, "project", function (r) {
                if (r && r.project !== frm.doc.project) {
                    frm.set_value("task", "");
                }
            });
        }
    }
});
