import frappe


def after_install():
    _print_banner()
    _log("Installation de l'app InovaYa GdP terminée.")

    # Frappe charge les fixtures par ordre alphabétique des fichiers.
    # project_template.json (p) est chargé avant task.json (t), donc les
    # Project Templates sont ignorés en première passe (Task records absents).
    # Cette deuxième passe garantit leur chargement maintenant que les Tasks existent.
    try:
        from frappe.utils.fixtures import sync_fixtures as _sync
        _sync("inovaya_gdp")
        _log("Deuxième passe fixtures : Project Templates chargés.")
    except Exception as exc:  # pragma: no cover
        _log(f"Avertissement deuxième passe fixtures : {exc}")

    _log("Les fixtures (rôles, champs, modèles, workspaces) ont été chargées.")
    _log("Prochaine étape : consultez README.md pour la configuration post-install.")


def after_migrate():
    _log("Migration InovaYa GdP — fixtures synchronisées.")


# ---------------------------------------------------------------------------

def _log(msg):
    frappe.logger("inovaya_gdp").info(msg)
    print(f"  [inovaya_gdp] {msg}")


def _print_banner():
    print()
    print("=" * 60)
    print("  InovaYa GdP — ERPNext v16 Native-First  v1.0.0")
    print("  Phase 1 : socle de configuration ERPNext standard")
    print("=" * 60)
    print()
