"""Tests de la couche d'accès aux données (base, référentiels, suivi, GA).

Les tests portent sur des données synthétiques anonymisées : aucune donnée
personne réelle n'est versionnée.
"""

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kpi.bdd.connexion import BaseDonnees  # noqa: E402 - chemin ajusté pour les tests
from kpi.bdd.modeles import (  # noqa: E402 - chemin ajusté pour les tests
    GoogleAnalyticsRepository,
    PersonneRepository,
    ReferentielRepository,
    SuiviRepository,
)
from kpi.suivi import EvenementSuivi  # noqa: E402 - chemin ajusté pour les tests


class TestBaseDonnees(unittest.TestCase):
    """Tests de la création et de l'ouverture de la base."""

    def test_creation_schema(self) -> None:
        """Une base neuve contient toutes les tables attendues."""
        with tempfile.TemporaryDirectory() as _dossier:
            _base = BaseDonnees(Path(_dossier) / "test.sqlite3")
            try:
                _curseur = _base.connexion.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
                _tables = {_ligne["name"] for _ligne in _curseur.fetchall()}
            finally:
                _base.fermer()
        for _attendu in (
            "canal",
            "provenance",
            "statut_contact",
            "prestation",
            "detail_prestation",
            "action",
            "personne",
            "suivi_activite",
            "ga_visiteurs",
            "ga_canaux",
            "ga_requetes",
        ):
            self.assertIn(_attendu, _tables)

    def test_reouverture_sans_doublon(self) -> None:
        """Rouvrir une base existante ne duplique pas les données."""
        with tempfile.TemporaryDirectory() as _dossier:
            _chemin = Path(_dossier) / "test.sqlite3"
            _base = BaseDonnees(_chemin)
            try:
                _referentiels = ReferentielRepository(_base)
                _referentiels.obtenir_ou_creer("canal", "mail")
                _base.valider()
            finally:
                _base.fermer()
            _base = BaseDonnees(_chemin)
            try:
                _referentiels = ReferentielRepository(_base)
                self.assertEqual(_referentiels.lister("canal"), ["mail"])
            finally:
                _base.fermer()

    def test_migration_ordre_saisie(self) -> None:
        """Une base sans la colonne reçoit un ordre_saisie backfillé.

        Valeurs témoins : trois lignes insérées dans l'ordre id 1, 2, 3
        reçoivent ordre_saisie 1, 2, 3, et la migration est idempotente.
        """
        with tempfile.TemporaryDirectory() as _dossier:
            _chemin = Path(_dossier) / "test.sqlite3"
            _base = BaseDonnees(_chemin)
            _base.connexion.execute("DROP INDEX IF EXISTS idx_suivi_ordre")
            _base.connexion.execute(
                "ALTER TABLE suivi_activite DROP COLUMN ordre_saisie"
            )
            _pid = PersonneRepository(_base).obtenir_ou_creer("Alice Martin")
            for _jour in (5, 3, 9):
                _base.connexion.execute(
                    "INSERT INTO suivi_activite (date, personne_id) VALUES (?, ?)",
                    (f"2025-01-{_jour:02d}", _pid),
                )
            _base.valider()
            _base.fermer()

            def _lire_ordres() -> list[int]:
                _base_ouverte = BaseDonnees(_chemin)
                try:
                    return [
                        _ligne["ordre_saisie"]
                        for _ligne in _base_ouverte.connexion.execute(
                            "SELECT ordre_saisie FROM suivi_activite ORDER BY id"
                        ).fetchall()
                    ]
                finally:
                    _base_ouverte.fermer()

            self.assertEqual(_lire_ordres(), [1, 2, 3])
            # La migration est idempotente : réouverture sans changement.
            self.assertEqual(_lire_ordres(), [1, 2, 3])


class TestReferentiels(unittest.TestCase):
    """Tests du dépôt des tables de référence."""

    def setUp(self) -> None:
        """Ouvre une base temporaire pour chaque test."""
        self._dossier = tempfile.TemporaryDirectory()
        self._base = BaseDonnees(Path(self._dossier.name) / "test.sqlite3")
        self._referentiels = ReferentielRepository(self._base)

    def tearDown(self) -> None:
        """Ferme la base et supprime le dossier temporaire."""
        self._base.fermer()
        self._dossier.cleanup()

    def test_table_inconnue_refusee(self) -> None:
        """Une table hors liste blanche lève une erreur (anti-injection)."""
        with self.assertRaises(ValueError):
            self._referentiels.lister("suivi_activite")
        with self.assertRaises(ValueError):
            self._referentiels.identifier("personne", "x")

    def test_obtenir_ou_creer(self) -> None:
        """La création est idempotente : même valeur, même identifiant."""
        _id1 = self._referentiels.obtenir_ou_creer("canal", "mail")
        _id2 = self._referentiels.obtenir_ou_creer("canal", "mail")
        self.assertEqual(_id1, _id2)
        self.assertEqual(self._referentiels.lister("canal"), ["mail"])

    def test_ajouter_existant_retourne_faux(self) -> None:
        """Ajouter une valeur déjà présente ne fait rien."""
        self.assertTrue(self._referentiels.ajouter("action", "Demande"))
        self.assertFalse(self._referentiels.ajouter("action", "Demande"))


class TestSuiviRepository(unittest.TestCase):
    """Tests du dépôt de la table de suivi."""

    def setUp(self) -> None:
        """Ouvre une base temporaire pour chaque test."""
        self._dossier = tempfile.TemporaryDirectory()
        self._base = BaseDonnees(Path(self._dossier.name) / "test.sqlite3")
        self._suivi = SuiviRepository(self._base)

    def tearDown(self) -> None:
        """Ferme la base et supprime le dossier temporaire."""
        self._base.fermer()
        self._dossier.cleanup()

    def test_ajout_puis_liste(self) -> None:
        """Un événement ajouté est restitué à l'identique."""
        _evenement = EvenementSuivi(
            date=date(2025, 1, 14),
            personne="Alice Martin",
            statut_contact="prospect",
            action_public="Demande",
            canal="formulaire de contact",
            prestation="Séances",
            detail_prestation="Famille",
            commentaire="Premier contact",
        )
        self._suivi.ajouter(_evenement)
        _lus = self._suivi.lister()
        self.assertEqual(len(_lus), 1)
        self.assertEqual(_lus[0].personne, "Alice Martin")
        self.assertEqual(_lus[0].canal, "formulaire de contact")
        self.assertEqual(_lus[0].commentaire, "Premier contact")
        self.assertEqual(_lus[0].annee, 2025)
        self.assertEqual(_lus[0].mois, 1)

    def test_valeur_inconnue_creee_automatiquement(self) -> None:
        """Une valeur absente des listes est créée, jamais rejetée."""
        self._suivi.ajouter(
            EvenementSuivi(
                date=date(2025, 2, 1),
                personne="Bob Dupont",
                action_public="Action libre saisie",
            )
        )
        self.assertIn("Action libre saisie", self._suivi.lister()[0].action_public or "")
        _referentiels = ReferentielRepository(self._base)
        self.assertIn("Action libre saisie", _referentiels.lister("action"))

    def test_personne_dedoublonnee(self) -> None:
        """Deux événements d'une même personne ne créent qu'une personne."""
        for _jour in (10, 20):
            self._suivi.ajouter(
                EvenementSuivi(date=date(2025, 3, _jour), personne="Chloé Bernard")
            )
        _personnes = PersonneRepository(self._base)
        self.assertEqual(_personnes.lister(), ["Chloé Bernard"])

    def test_ordre_saisie_incremente(self) -> None:
        """Chaque ajout reçoit MAX(ordre_saisie)+1 : 1, 2, 3."""
        _ids = [
            self._suivi.ajouter(
                EvenementSuivi(date=date(2025, 4, _jour), personne="Alice Martin")
            )
            for _jour in (1, 2, 3)
        ]
        _ordres = [self._suivi.obtenir(_id).ordre_saisie for _id in _ids]
        self.assertEqual(_ordres, [1, 2, 3])

    def test_ordre_saisie_non_reutilise_apres_suppression(self) -> None:
        """Après suppression, le prochain ordre_saisie continue la séquence."""
        _id1 = self._suivi.ajouter(
            EvenementSuivi(date=date(2025, 4, 1), personne="Alice Martin")
        )
        self._suivi.ajouter(
            EvenementSuivi(date=date(2025, 4, 2), personne="Bob Dupont")
        )
        self._suivi.supprimer(_id1)
        _id3 = self._suivi.ajouter(
            EvenementSuivi(date=date(2025, 4, 3), personne="Chloé Bernard")
        )
        self.assertEqual(self._suivi.obtenir(_id3).ordre_saisie, 3)

    def test_mettre_a_jour_conserve_ordre_saisie(self) -> None:
        """Modifier un événement ne change pas son rang de saisie."""
        _id = self._suivi.ajouter(
            EvenementSuivi(
                date=date(2025, 5, 1), personne="Alice Martin", commentaire="avant"
            )
        )
        self._suivi.mettre_a_jour(
            _id,
            EvenementSuivi(
                date=date(2025, 5, 2), personne="Alice Martin", commentaire="après"
            ),
        )
        _lu = self._suivi.obtenir(_id)
        self.assertEqual(_lu.ordre_saisie, 1)
        self.assertEqual(_lu.commentaire, "après")


class TestGoogleAnalyticsRepository(unittest.TestCase):
    """Tests du dépôt des relevés Google Analytics."""

    def setUp(self) -> None:
        """Ouvre une base temporaire pour chaque test."""
        self._dossier = tempfile.TemporaryDirectory()
        self._base = BaseDonnees(Path(self._dossier.name) / "test.sqlite3")
        self._ga = GoogleAnalyticsRepository(self._base)

    def tearDown(self) -> None:
        """Ferme la base et supprime le dossier temporaire."""
        self._base.fermer()
        self._dossier.cleanup()

    def test_rechargement_mois_idempotent(self) -> None:
        """Recharger un mois remplace la valeur au lieu de la dupliquer."""
        self._ga.enregistrer_visiteurs(2025, 9, 877)
        self._ga.enregistrer_visiteurs(2025, 9, 900)  # correction du relevé
        self._base.connexion.commit()
        _releves = self._ga.lister_visiteurs()
        self.assertEqual(_releves, [(2025, 9, 900)])


if __name__ == "__main__":
    unittest.main()
