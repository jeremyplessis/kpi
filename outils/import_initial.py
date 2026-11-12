"""Import initial du classeur KPI.xlsx vers la base SQLite.

Outil à usage unique : il reprend les données déjà saisies dans le classeur
d'origine (référentiels, personnes, suivi d'activité, relevés Google
Analytics) afin que la base ne soit pas vide et que les tests utilisateurs
se fassent sur des données réelles.

Utilisation :

    python -m outils.import_initial chemin/vers/KPI.xlsx [chemin/base.sqlite3]

L'import est protégé : si la base contient déjà un suivi, il ne double pas
les données (relancer avec ``--force`` vide alors la table avant import).
"""

import sys
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook

from kpi.bdd.connexion import BaseDonnees
from kpi.bdd.modeles import GoogleAnalyticsRepository, SuiviRepository
from kpi.suivi import EvenementSuivi

#: Correspondance nom de mois -> numéro (onglet « Suivi » du classeur).
NUMEROS_MOIS = {
    "janvier": 1,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
}


@dataclass
class RapportImport:
    """Bilan chiffré d'un import, affiché à l'utilisatrice."""

    nb_referentiels: int = 0
    nb_personnes: int = 0
    nb_suivi: int = 0
    nb_ga_visiteurs: int = 0
    nb_ga_canaux: int = 0
    nb_ga_requetes: int = 0
    avertissements: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        """Restitue le rapport sous forme lisible."""
        _lignes = [
            f"Référentiels créés : {self.nb_referentiels}",
            f"Personnes créées : {self.nb_personnes}",
            f"Événements de suivi importés : {self.nb_suivi}",
            f"Relevés GA : {self.nb_ga_visiteurs} mois de visiteurs, "
            f"{self.nb_ga_canaux} lignes de canaux, "
            f"{self.nb_ga_requetes} requêtes",
        ]
        if self.avertissements:
            _lignes.append("Avertissements :")
            _lignes.extend(f"  - {_avert}" for _avert in self.avertissements)
        return "\n".join(_lignes)


class ImportateurClasseur:
    """Importe le classeur KPI.xlsx dans la base SQLite.

    :param _base: base ouverte (le schéma est créé à l'ouverture).
    """

    def __init__(self, _base: BaseDonnees) -> None:
        """Prépare les dépôts utilisés pendant l'import."""
        self._base = _base
        self._suivi = SuiviRepository(_base)
        self._ga = GoogleAnalyticsRepository(_base)
        self._rapport = RapportImport()

    def importer(self, _chemin_classeur: Path, _force: bool = False) -> RapportImport:
        """Importe l'intégralité du classeur et retourne le bilan.

        L'import est atomique : si le classeur ne peut être lu ou qu'une
        erreur survient en cours de route, la base reste dans son état
        initial (la suppression éventuelle de l'ancien suivi est annulée).

        :param _chemin_classeur: chemin du fichier KPI.xlsx.
        :param _force: si vrai, vide la table de suivi avant import.
        :raises ValueError: si la base contient déjà un suivi et que ``_force``
            est faux (protection contre les doublons).
        """
        if self._suivi.compter() > 0 and not _force:
            raise ValueError(
                "La base contient déjà un suivi : relancez avec --force pour "
                "vider puis réimporter (les doublons seront évités)."
            )
        # Un nouvel import repart d'un bilan vierge (l'instance peut servir
        # plusieurs fois, notamment avec --force).
        self._rapport = RapportImport()
        try:
            if _force:
                self._base.connexion.execute("DELETE FROM suivi_activite")

            _classeur = load_workbook(filename=_chemin_classeur, data_only=True)
            self._importer_listes(_classeur["Listes"])
            self._importer_suivi(_classeur["Suivi"])
            self._importer_google_analytics(_classeur["Google Analytics"])
        except Exception:
            # Annule tout l'import (y compris la suppression de l'ancien
            # suivi) : la base reste dans son état initial.
            self._base.annuler()
            raise
        self._base.valider()
        return self._rapport

    def _importer_listes(self, _onglet) -> None:
        """Crée les référentiels à partir de l'onglet « Listes »."""
        from kpi.bdd.modeles import TABLES_REFERENTIELLES

        _colonnes = {
            "canal": 0,
            "provenance": 1,
            "statut_contact": 2,
            "prestation": 3,
            "detail_prestation": 4,
            "action": 9,
        }
        for _ligne in _onglet.iter_rows(min_row=3, values_only=True):
            for _table, _colonne in _colonnes.items():
                _valeur = _ligne[_colonne]
                if _valeur is None or str(_valeur).strip() == "":
                    continue
                self.creer_valeur_referentiel(_table, str(_valeur).strip())

    def creer_valeur_referentiel(self, _table: str, _valeur: str) -> None:
        """Ajoute une valeur à un référentiel si elle n'existe pas."""
        _curseur = self._base.connexion.execute(
            f"SELECT COUNT(*) AS total FROM {_table} WHERE nom = ?",  # noqa: S608 - table listée blanche
            (_valeur,),
        )
        if _curseur.fetchone()["total"] == 0:
            self._base.connexion.execute(
                f"INSERT INTO {_table} (nom) VALUES (?)",  # noqa: S608 - table listée blanche
                (_valeur,),
            )
            self._rapport.nb_referentiels += 1

    def _importer_suivi(self, _onglet) -> None:
        """Importe les événements de l'onglet « Suivi ».

        Les colonnes Année et Mois sont ignorées : la date seule fait foi
        (elles sont d'ailleurs parfois incohérentes dans le classeur).
        Les lignes incomplètes (colonnes manquantes en fin de ligne) sont
        acceptées : les valeurs absentes valent simplement None.
        """
        _curseur_personnes = self._base.connexion.execute(
            "SELECT COUNT(*) AS total FROM personne"
        )
        _nb_personnes_avant = _curseur_personnes.fetchone()["total"]
        for _ligne in _onglet.iter_rows(min_row=2, values_only=True):
            _date = _valeur_colonne(_ligne, 2)
            _nom = _valeur_colonne(_ligne, 3)
            if _date is None or _nom is None:
                continue
            _evenement = EvenementSuivi(
                date=_date.date() if isinstance(_date, datetime) else _date,
                personne=str(_nom).strip(),
                statut_contact=_nettoyer(_valeur_colonne(_ligne, 4)),
                action_public=_nettoyer(_valeur_colonne(_ligne, 5)),
                canal=_nettoyer(_valeur_colonne(_ligne, 6)),
                provenance=_nettoyer(_valeur_colonne(_ligne, 7)),
                prestation=_nettoyer(_valeur_colonne(_ligne, 8)),
                detail_prestation=_nettoyer(_valeur_colonne(_ligne, 9)),
                action_photographe=_nettoyer(_valeur_colonne(_ligne, 10)),
                canal2=_nettoyer(_valeur_colonne(_ligne, 11)),
                commentaire=_nettoyer(_valeur_colonne(_ligne, 12)),
            )
            self._suivi.ajouter(_evenement)
            self._rapport.nb_suivi += 1
            if _evenement.annee < 2020:
                self._rapport.avertissements.append(
                    f"Date suspecte conservée telle quelle : "
                    f"{_evenement.date.isoformat()} ({_evenement.personne})"
                )
        _curseur_personnes = self._base.connexion.execute(
            "SELECT COUNT(*) AS total FROM personne"
        )
        self._rapport.nb_personnes = _curseur_personnes.fetchone()["total"] - _nb_personnes_avant

    def _importer_google_analytics(self, _onglet) -> None:
        """Importe les relevés mensuels de l'onglet « Google Analytics ».

        L'onglet contient trois blocs en colonnes : nombre de visiteurs,
        répartition par canal et requêtes de recherche. Les valeurs se
        lisent en colonnes mensuelles (janvier à décembre).
        """
        for _ligne in _onglet.iter_rows(min_row=2, values_only=True):
            _annee = _ligne[0]
            if not isinstance(_annee, int):
                continue
            _bloc = _ligne[1]
            if _bloc == "Nb de visiteurs":
                self._importer_ligne_visiteurs(_annee, _ligne)
            elif _bloc == "Canaux":
                self._importer_ligne_canaux(_annee, _ligne)
            elif _bloc == "Requêtes":
                self._importer_ligne_requetes(_annee, _ligne)

    def _mois_valeurs(self, _ligne) -> Iterator[tuple[int, int]]:
        """Yield (numéro de mois, valeur) pour les colonnes mensuelles."""
        for _indice, _valeur in enumerate(_ligne[3:15]):
            if _valeur is None:
                continue
            yield _indice + 1, int(_valeur)

    def _importer_ligne_visiteurs(self, _annee: int, _ligne) -> None:
        """Enregistre une ligne « Nb de visiteurs »."""
        for _mois, _visiteurs in self._mois_valeurs(_ligne):
            self._ga.enregistrer_visiteurs(_annee, _mois, _visiteurs)
            self._rapport.nb_ga_visiteurs += 1

    def _importer_ligne_canaux(self, _annee: int, _ligne) -> None:
        """Enregistre une ligne « Canaux » (canal en colonne 2)."""
        _canal = _ligne[2]
        if _canal is None:
            return
        for _mois, _visiteurs in self._mois_valeurs(_ligne):
            self._ga.enregistrer_canal(_annee, _mois, str(_canal), _visiteurs)
            self._rapport.nb_ga_canaux += 1

    def _importer_ligne_requetes(self, _annee: int, _ligne) -> None:
        """Enregistre une ligne « Requêtes » (requête en colonne 2)."""
        _requete = _ligne[2]
        if _requete is None:
            return
        for _mois, _occurrences in self._mois_valeurs(_ligne):
            self._ga.enregistrer_requete(_annee, _mois, str(_requete), _occurrences)
            self._rapport.nb_ga_requetes += 1


def _valeur_colonne(_ligne: tuple, _indice: int):
    """Retourne la valeur d'une colonne d'une ligne, None si elle manque.

    Les lignes d'un classeur Excel peuvent être incomplètes en fin de ligne :
    ce garde-fou évite un échec d'import sur une saisie tronquée.
    """
    return _ligne[_indice] if _indice < len(_ligne) else None


def _nettoyer(_valeur) -> str | None:
    """Normalise une cellule : vide si absente, texte sinon."""
    if _valeur is None:
        return None
    _texte = str(_valeur).strip()
    return _texte or None


def main() -> int:
    """Point d'entrée en ligne de commande de l'import initial."""
    _arguments = sys.argv[1:]
    _force = "--force" in _arguments
    _arguments = [_a for _a in _arguments if _a != "--force"]
    if not 1 <= len(_arguments) <= 2:
        print(__doc__)
        return 1
    _classeur = Path(_arguments[0])
    _base_donnees = Path(_arguments[1]) if len(_arguments) == 2 else Path("kpi.sqlite3")
    _base = BaseDonnees(_base_donnees)
    try:
        _importateur = ImportateurClasseur(_base)
        _rapport = _importateur.importer(_classeur, _force=_force)
    finally:
        _base.fermer()
    print(_rapport)
    return 0


if __name__ == "__main__":
    sys.exit(main())
