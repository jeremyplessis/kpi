"""Point d'entrée de l'application KPI.

Pour l'instant, l'application se réduit au socle de données : l'interface
web locale (étapes 3 et 4 de la feuille de route) viendra s'y brancher.
L'import initial du classeur s'effectue avec ``outils/import_initial.py``.
"""

import sys


def main() -> int:
    """Démarre l'application (interface web à venir)."""
    print("Application KPI : interface web en cours de développement.")
    print("En attendant : python -m outils.import_initial KPI.xlsx [base.sqlite3]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
