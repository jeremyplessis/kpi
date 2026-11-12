"""Point d'entrée de l'application KPI.

Démarre le serveur web local (accessible uniquement depuis ce poste, sur
127.0.0.1) et ouvre le navigateur sur l'écran de saisie. L'import initial
du classeur s'effectue avec ``outils/import_initial.py``.

Lancement usuel (depuis la racine du projet, où se trouve la base) :

    kpi                     # ouvre le navigateur sur l'écran de saisie
    kpi --sans-navigateur   # n'ouvre pas le navigateur
    kpi --base autre.sqlite3 --port 9000
"""

import argparse
import socket
import threading
import time
import webbrowser

import uvicorn

from kpi.web.routes import ApplicationWeb

#: Adresse d'écoute : boucle locale uniquement, l'application reste privée.
HOTE_LOCAL = "127.0.0.1"

#: Port par défaut, choisi pour éviter les usages courants.
PORT_DEFAUT = 8765


def main() -> int:
    """Démarre le serveur local puis ouvre le navigateur.

    :returns: code de retour (1 si le port est déjà occupé).
    """
    _analyseur = argparse.ArgumentParser(
        prog="kpi",
        description="Écran local de saisie du suivi d'activité.",
    )
    _analyseur.add_argument(
        "--base",
        default="kpi.sqlite3",
        help="chemin du fichier de base (défaut : kpi.sqlite3)",
    )
    _analyseur.add_argument(
        "--port",
        type=int,
        default=PORT_DEFAUT,
        help=f"port d'écoute local (défaut : {PORT_DEFAUT})",
    )
    _analyseur.add_argument(
        "--sans-navigateur",
        action="store_true",
        help="ne pas ouvrir le navigateur au démarrage",
    )
    _arguments = _analyseur.parse_args()

    if not _port_est_libre(HOTE_LOCAL, _arguments.port):
        print(
            f"Le port {_arguments.port} est déjà occupé : "
            "une autre instance de l'application est peut-être déjà ouverte "
            "(sinon, relancez avec --port)."
        )
        return 1

    _application = ApplicationWeb(_arguments.base).application
    _configuration = uvicorn.Config(
        _application,
        host=HOTE_LOCAL,
        port=_arguments.port,
        log_level="warning",
    )
    _serveur = uvicorn.Server(_configuration)
    _fil = threading.Thread(target=_serveur.run, daemon=True)
    _fil.start()

    # On attend que le serveur accepte réellement les connexions avant
    # d'ouvrir le navigateur : l'utilisatrice ne doit jamais tomber sur une
    # page « connexion refusée ».
    _delai = 0.05
    while not _serveur.started:
        time.sleep(_delai)
    if not _arguments.sans_navigateur:
        webbrowser.open(f"http://{HOTE_LOCAL}:{_arguments.port}")

    try:
        _fil.join()
    except KeyboardInterrupt:
        print("Arrêt de l'application…")
        _serveur.should_exit = True
        _fil.join(timeout=2)
    return 0


def _port_est_libre(_hote: str, _port: int) -> bool:
    """Vérifie qu'aucun autre service n'écoute déjà sur ce port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as _sonde:
        _sonde.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            _sonde.bind((_hote, _port))
        except OSError:
            return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
