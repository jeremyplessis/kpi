"""Tests de l'import initial du classeur KPI.xlsx.

Un classeur synthétique, de structure identique à l'original mais aux
données anonymes, est construit puis importé : cela valide l'outils sans
versionner de données personnelles réelles.
"""

import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from openpyxl import Workbook  # noqa: E402 - chemin ajusté pour les tests

from kpi.bdd.connexion import BaseDonnees  # noqa: E402 - chemin ajusté pour les tests
from kpi.kpi.indicateurs import NbDemandes, NbProspects  # noqa: E402 - chemin ajusté pour les tests
from outils.import_initial import ImportateurClasseur  # noqa: E402 - chemin ajusté pour les tests

#: En-tête de l'onglet « Suivi » (une ligne de données d'exemple suit).
LIGNES_SUIVI = [
    (
        "Année",
        "Mois",
        "Date",
        "Nom",
        "Contact",
        "Action public",
        "Canal",
        "Provenance",
        "Type",
        "Séances",
        "Action photographe",
        "Canal2",
        "Commentaire",
    ),
    (2025, "janvier", datetime(2025, 1, 14), "Alice", "prospect", "Demande",
     "formulaire de contact", "Google", "Séances", "Famille", "Réponse", "mail", None),
    (2025, "janvier", datetime(2025, 1, 30), "Alice", None, "Paiement",
     None, None, None, None, "Confirmation", None, None),
    (2025, "février", datetime(2025, 2, 5), "Bob", "prospect", "Réservation",
     "réservation site", None, "Carte cadeau", "Famille", "-", None, None),
    (2025, "février", datetime(2025, 2, 6), "Bob", None, "Paiement",
     None, None, None, None, "Confirmation", None, "paiement ok"),
    (2026, "mars", datetime(2026, 3, 2), "Chloé", "prospect", "Demande",
     "instagram", "Instagram", "Séances", "Portrait", "Réponse", "instagram", None),
]

#: En-tête et lignes de l'onglet « Listes » (une valeur par référentiel).
LIGNES_LISTES = [
    ("Canal", "Provenance", "Contact", "Prestation", "DetailPrestation",
     None, None, None, None, "Action", None, None, "Personne"),
    ("Nom", "Nom", "Nom", "Nom", "Nom", None, None, None, None, "Nom",
     None, None, "Nom"),
    ("mail", "Google", "prospect", "Séances", "Famille", None, None, None,
     None, "Demande", None, None, "Alice"),
    ("instagram", "Instagram", "client", "Carte cadeau", "Portrait", None,
     None, None, None, "Paiement", None, None, "Bob"),
    ("réservation site", "Bouche à oreille", None, None, None, None, None,
     None, None, "Réservation", None, None, None),
    (None, None, None, None, None, None, None, None, None, "Réponse",
     None, None, None),
]

#: En-tête de l'onglet « Google Analytics » (mois en colonnes).
EN_TETE_GA = ("Année", "Colonne1", "Colonne2") + tuple(
    f"Mois{_indice}" for _indice in range(1, 13)
) + ("Moyenne/mois",)
LIGNES_GA = [
    EN_TETE_GA,
    (2025, "Nb de visiteurs", 100, 10, 20, None, None, None, None, None,
     None, None, None, None, None, None),
    (2025, "Canaux", "Direct", 5, 12, None, None, None, None, None, None,
     None, None, None, None),
    (2025, "Requêtes", "photographe cahors", 2, 4, None, None, None, None,
     None, None, None, None, None, None),
]


def construire_classeur(_chemin: Path) -> None:
    """Écrit un classeur synthétique de structure identique à KPI.xlsx."""
    _classeur = Workbook()
    _feuil1 = _classeur.active
    _feuil1.title = "Feuil1"
    _listes = _classeur.create_sheet("Listes")
    for _ligne in LIGNES_LISTES:
        _listes.append(_ligne)
    _donnees = _classeur.create_sheet("Données")
    _ga = _classeur.create_sheet("Google Analytics")
    for _ligne in LIGNES_GA:
        _ga.append(_ligne)
    _kpi = _classeur.create_sheet("KPI")
    _donnees_kpi = _classeur.create_sheet("Données KPI")
    _suivi = _classeur.create_sheet("Suivi")
    for _ligne in LIGNES_SUIVI:
        _suivi.append(_ligne)
    _classeur.save(_chemin)


class TestImportInitial(unittest.TestCase):
    """Tests de l'import du classeur vers la base SQLite."""

    def setUp(self) -> None:
        """Prépare un classeur synthétique et une base temporaire."""
        self._dossier = tempfile.TemporaryDirectory()
        _racine = Path(self._dossier.name)
        self._chemin_classeur = _racine / "KPI.xlsx"
        construire_classeur(self._chemin_classeur)
        self._chemin_base = _racine / "kpi.sqlite3"
        self._base = BaseDonnees(self._chemin_base)

    def tearDown(self) -> None:
        """Ferme la base et supprime le dossier temporaire."""
        self._base.fermer()
        self._dossier.cleanup()

    def test_import_complet(self) -> None:
        """Référentiels, personnes, suivi et relevés GA sont importés."""
        _importateur = ImportateurClasseur(self._base)
        _rapport = _importateur.importer(self._chemin_classeur)
        self.assertEqual(_rapport.nb_suivi, 5)
        self.assertEqual(_rapport.nb_ga_visiteurs, 2)  # janv. et févr.
        self.assertEqual(_rapport.nb_ga_canaux, 2)
        self.assertEqual(_rapport.nb_ga_requetes, 2)
        # Les valeurs manquantes dans les listes sont créées automatiquement
        # (ici « Confirmation » et « - » n'existent pas dans le jeu).
        self.assertGreater(_rapport.nb_referentiels, 0)

    def test_indicateurs_apres_import(self) -> None:
        """Les indicateurs se calculent sur les données importées."""
        _importateur = ImportateurClasseur(self._base)
        _importateur.importer(self._chemin_classeur)
        from kpi.bdd.modeles import SuiviRepository

        _evenements = SuiviRepository(self._base).lister()
        _prospects = sum(int(_l.valeur) for _l in NbProspects().calculer(_evenements))
        _demandes = sum(int(_l.valeur) for _l in NbDemandes().calculer(_evenements))
        self.assertEqual(_prospects, 3)  # Alice, Bob, Chloé
        self.assertEqual(_demandes, 3)  # Demande x2 + Réservation

    def test_import_protege_contre_doublons(self) -> None:
        """Un second import sans --force est refusé."""
        _importateur = ImportateurClasseur(self._base)
        _importateur.importer(self._chemin_classeur)
        with self.assertRaises(ValueError):
            _importateur.importer(self._chemin_classeur)

    def test_import_force_sans_doublons(self) -> None:
        """Un import forcé remplace les données au lieu de les doubler."""
        _importateur = ImportateurClasseur(self._base)
        _importateur.importer(self._chemin_classeur)
        _rapport = _importateur.importer(self._chemin_classeur, _force=True)
        self.assertEqual(_rapport.nb_suivi, 5)
        from kpi.bdd.modeles import SuiviRepository  # noqa: E402

        self.assertEqual(SuiviRepository(self._base).compter(), 5)

    def test_import_atomique_sur_erreur(self) -> None:
        """Un import forcé qui échoue laisse la base dans son état initial.

        Scénario couvert : la suppression de l'ancien suivi est annulée si
        le classeur ne peut pas être lu (l'import est atomique).
        """
        _importateur = ImportateurClasseur(self._base)
        _importateur.importer(self._chemin_classeur)
        _classeur_corrompu = Path(self._dossier.name) / "corrompu.xlsx"
        _classeur_corrompu.write_bytes(b"ceci n'est pas un classeur")
        with self.assertRaises(Exception):
            _importateur.importer(_classeur_corrompu, _force=True)
        # La base contient toujours les 5 événements d'origine.
        from kpi.bdd.modeles import SuiviRepository  # noqa: E402

        self.assertEqual(SuiviRepository(self._base).compter(), 5)

    def test_valeurs_ga_importees(self) -> None:
        """Les relevés GA sont importés avec leurs valeurs exactes."""
        _importateur = ImportateurClasseur(self._base)
        _importateur.importer(self._chemin_classeur)
        from kpi.bdd.modeles import GoogleAnalyticsRepository  # noqa: E402

        _ga = GoogleAnalyticsRepository(self._base)
        self.assertEqual(_ga.lister_visiteurs(), [(2025, 1, 10), (2025, 2, 20)])
        _curseur = self._base.connexion.execute(
            "SELECT visiteurs FROM ga_canaux "
            "WHERE annee = 2025 AND mois = 2 AND canal = 'Direct'"
        )
        self.assertEqual(_curseur.fetchone()["visiteurs"], 12)
        _curseur = self._base.connexion.execute(
            "SELECT occurrences FROM ga_requetes "
            "WHERE annee = 2025 AND mois = 1 AND requete = 'photographe cahors'"
        )
        self.assertEqual(_curseur.fetchone()["occurrences"], 2)

    def test_avertissement_date_suspecte(self) -> None:
        """Une date manifestement ancienne est conservée mais signalée."""
        _classeur = Workbook()
        _suivi = _classeur.active
        _suivi.title = "Suivi"
        _suivi.append(("Année", "Mois", "Date", "Nom", "Contact", "Action public"))
        _suivi.append((2009, "juin", datetime(2009, 6, 11), "Personne X"))
        _classeur.create_sheet("Listes")
        _classeur.create_sheet("Google Analytics")
        _chemin_bis = Path(self._dossier.name) / "bis.xlsx"
        _classeur.save(_chemin_bis)
        _importateur = ImportateurClasseur(self._base)
        _rapport = _importateur.importer(_chemin_bis)
        self.assertEqual(len(_rapport.avertissements), 1)
        self.assertIn("2009-06-11", _rapport.avertissements[0])


if __name__ == "__main__":
    unittest.main()
