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

    # B09/B26 — Dashboard Charts et Workspaces InovaYa.
    # Gérés via setup scripts (pas fixtures) car l'ORM Dashboard Chart valide
    # group_by_based_on et bloque bench migrate lors de sync_fixtures.
    # Ces fonctions sont idempotentes (skip si déjà existants).
    try:
        from inovaya_gdp.setup.setup_b09 import run as _run_b09
        _run_b09()
        _log("B09 : Workspace InovaYa Pôle GdP + Dashboard Charts créés.")
    except Exception as exc:  # pragma: no cover
        _log(f"Avertissement setup B09 : {exc}")

    try:
        from inovaya_gdp.setup.setup_b26 import run as _run_b26
        _run_b26()
        _log("B26 : Workspace InovaYa Direction + Charts budget créés.")
    except Exception as exc:  # pragma: no cover
        _log(f"Avertissement setup B26 : {exc}")

    try:
        from inovaya_gdp.setup.setup_b24_b25 import run as _run_pages
        _run_pages()
        _log("B24/B25 : Pages Frappe enregistrées.")
    except Exception as exc:  # pragma: no cover
        _log(f"Avertissement setup B24/B25 : {exc}")

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
