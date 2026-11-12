"""Tests du moteur de calcul des indicateurs.

Jeu de données synthétique et anonyme, avec des valeurs attendues calculées
à la main. Les règles testées sont celles documentées dans
``documentation/01_proposition_architecture.md`` (validées le 28/10/2026).
"""

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kpi.kpi.indicateurs import (  # noqa: E402 - chemin ajusté pour les tests
    NbDemandes,
    NbProspects,
    RdvParCanal,
    TauxGhosting,
)
from kpi.suivi import EvenementSuivi  # noqa: E402 - chemin ajusté pour les tests

#: Jeu de données : 2025-01 (Alice répond, Bob et Chloé ghostent),
#: 2025-02 (Dave réserve en ligne puis paie), 2025-03 (Émilie demande
#: sans réponse, Franck demande et confirme).
EVENEMENTS = [
    EvenementSuivi(
        date=date(2025, 1, 10),
        personne="Alice",
        statut_contact="prospect",
        action_public="Demande",
        canal="formulaire de contact",
    ),
    EvenementSuivi(
        date=date(2025, 1, 15),
        personne="Alice",
        action_public="RDV",
        canal="mail",
    ),
    EvenementSuivi(
        date=date(2025, 1, 10),
        personne="Bob",
        statut_contact="prospect",
        action_public="Demande",
        canal="instagram",
    ),
    EvenementSuivi(
        date=date(2025, 1, 12),
        personne="Chloé",
        statut_contact="client",
        action_public="Demande",
        canal="téléphone",
    ),
    EvenementSuivi(
        date=date(2025, 2, 3),
        personne="Dave",
        statut_contact="prospect",
        action_public="Réservation",
        canal="réservation site",
    ),
    EvenementSuivi(
        date=date(2025, 2, 8),
        personne="Dave",
        action_public="Paiement",
    ),
    EvenementSuivi(
        date=date(2025, 3, 5),
        personne="Émilie",
        statut_contact="prospect",
        action_public="Demande",
        canal="mariages.net",
    ),
    EvenementSuivi(
        date=date(2025, 3, 6),
        personne="Franck",
        statut_contact="prospect",
        action_public="Demande",
        canal="mail",
    ),
    EvenementSuivi(
        date=date(2025, 3, 20),
        personne="Franck",
        action_public="Confirmation",
    ),
    # RDV pris par le photographe (action photographe)
    EvenementSuivi(
        date=date(2025, 1, 15),
        personne="Alice",
        action_photographe="RDV",
        canal2="mail",
    ),
    EvenementSuivi(
        date=date(2025, 2, 9),
        personne="Dave",
        action_photographe="RDV",
        canal2="téléphone",
    ),
]


class TestNbProspects(unittest.TestCase):
    """Tests de l'indicateur « Nombre de prospects »."""

    def test_regroupement_par_mois_et_canal(self) -> None:
        """Les prospects sont comptés par (année, mois, canal)."""
        _lignes = NbProspects().calculer(EVENEMENTS)
        _attendu = [
            ((2025, 1, "formulaire de contact"), 1),  # Alice
            ((2025, 1, "instagram"), 1),  # Bob
            ((2025, 2, "réservation site"), 1),  # Dave
            ((2025, 3, "mail"), 1),  # Franck
            ((2025, 3, "mariages.net"), 1),  # Émilie
        ]
        _obtenu = [(_ligne.dimensions, int(_ligne.valeur)) for _ligne in _lignes]
        self.assertEqual(_obtenu, _attendu)

    def test_client_exclu(self) -> None:
        """Une cliente (Chloé) n'est pas comptée comme prospect."""
        _lignes = NbProspects().calculer(EVENEMENTS)
        _total = sum(int(_ligne.valeur) for _ligne in _lignes)
        self.assertEqual(_total, 5)  # Alice, Bob, Dave, Émilie, Franck


class TestNbDemandes(unittest.TestCase):
    """Tests de l'indicateur « Nombre de demandes »."""

    def test_reservation_comptee_comme_demande(self) -> None:
        """Une réservation en ligne est une demande (règle du classeur)."""
        _lignes = NbDemandes().calculer(EVENEMENTS)
        _canaux_fevrier = [
            _ligne for _ligne in _lignes if _ligne.dimensions[:2] == (2025, 2)
        ]
        self.assertEqual(
            [(_ligne.dimensions[2], int(_ligne.valeur)) for _ligne in _canaux_fevrier],
            [("réservation site", 1)],
        )

    def test_personne_dedoublonnee_par_mois(self) -> None:
        """Une personne ne compte qu'une fois par mois."""
        _evenements_avec_doublon = EVENEMENTS + [
            EvenementSuivi(
                date=date(2025, 1, 20),
                personne="Alice",
                action_public="Demande",
                canal="mail",
            )
        ]
        _lignes = NbDemandes().calculer(_evenements_avec_doublon)
        _janvier = sum(
            int(_ligne.valeur)
            for _ligne in _lignes
            if _ligne.dimensions[:2] == (2025, 1)
        )
        self.assertEqual(_janvier, 3)  # Alice, Bob, Chloé : une seule fois Alice


class TestTauxGhosting(unittest.TestCase):
    """Tests de l'indicateur « Taux de ghosting »."""

    def test_calcul_mensuel(self) -> None:
        """Janvier : 1 réponse sur 3 ; février : 1 sur 1 ; mars : 1 sur 2."""
        _detail = TauxGhosting().calculer_detail(EVENEMENTS)
        _par_mois = {(_ligne.annee, _ligne.mois): _ligne for _ligne in _detail}
        self.assertEqual(_par_mois[(2025, 1)].demandes, 3)
        self.assertEqual(_par_mois[(2025, 1)].reponses, 1)  # Alice (RDV)
        self.assertAlmostEqual(_par_mois[(2025, 1)].taux, 2 / 3)
        self.assertAlmostEqual(_par_mois[(2025, 2)].taux, 0.0)
        self.assertAlmostEqual(_par_mois[(2025, 3)].taux, 0.5)

    def test_reponse_sans_demande_du_mois_comptee(self) -> None:
        """Une réponse d'une personne sans demande ce mois-ci est comptée :
        sa demande peut dater du mois précédent (règle validée)."""
        _evenements = EVENEMENTS + [
            EvenementSuivi(
                date=date(2025, 1, 25),
                personne="Gaby",
                action_public="Réponse",
            )
        ]
        _detail = TauxGhosting().calculer_detail(_evenements)
        _janvier = [_ligne for _ligne in _detail if (_ligne.annee, _ligne.mois) == (2025, 1)][0]
        self.assertEqual(_janvier.demandes, 3)
        self.assertEqual(_janvier.reponses, 2)  # Alice, Gaby
        self.assertAlmostEqual(_janvier.taux, 1 / 3)

    def test_taux_borne_a_zero(self) -> None:
        """Plus de réponses que de demandes : le taux ne devient pas négatif."""
        _evenements = [
            EvenementSuivi(
                date=date(2025, 6, 1),
                personne="Hélène",
                action_public="Demande",
                canal="mail",
            ),
            EvenementSuivi(
                date=date(2025, 6, 2),
                personne="Hélène",
                action_public="Réponse",
            ),
            EvenementSuivi(
                date=date(2025, 6, 3),
                personne="Irène",
                action_public="Confirmation",
            ),
        ]
        _detail = TauxGhosting().calculer_detail(_evenements)
        self.assertEqual(_detail[0].demandes, 1)
        self.assertEqual(_detail[0].reponses, 2)
        self.assertEqual(_detail[0].taux, 0.0)

    def test_relance_non_comptee_comme_reponse(self) -> None:
        """Une relance est une action du photographe, pas une réponse :
        une personne dont la seule action est une relance reste ghostée
        (choix documenté, à confirmer avec l'utilisatrice)."""
        _evenements = [
            EvenementSuivi(
                date=date(2025, 7, 1),
                personne="Julie",
                action_public="Demande",
                canal="mail",
            ),
            EvenementSuivi(
                date=date(2025, 7, 10),
                personne="Julie",
                action_public="Relance",
            ),
        ]
        _detail = TauxGhosting().calculer_detail(_evenements)
        self.assertEqual(_detail[0].demandes, 1)
        self.assertEqual(_detail[0].reponses, 0)
        self.assertEqual(_detail[0].taux, 1.0)

    def test_taux_toujours_positif(self) -> None:
        """Le taux est borné à 0, même si les réponses dépassent les demandes."""
        _lignes = TauxGhosting().calculer(EVENEMENTS)
        for _ligne in _lignes:
            self.assertGreaterEqual(_ligne.valeur, 0.0)
            self.assertLessEqual(_ligne.valeur, 1.0)


class TestRdvParCanal(unittest.TestCase):
    """Tests de l'indicateur « RDV par canal »."""

    def test_regroupement_par_annee_et_canal(self) -> None:
        """Les RDV sont comptés par (année, canal de réponse)."""
        _lignes = RdvParCanal().calculer(EVENEMENTS)
        _obtenu = [(_ligne.dimensions, int(_ligne.valeur)) for _ligne in _lignes]
        self.assertEqual(
            _obtenu,
            [((2025, "mail"), 1), ((2025, "téléphone"), 1)],
        )


if __name__ == "__main__":
    unittest.main()
