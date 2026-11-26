"""Tests du moteur de calcul des indicateurs.

Jeu de données synthétique et anonyme, avec des valeurs attendues calculées
à la main. Les règles testées sont celles documentées dans
``documentation/01_proposition_architecture.md`` (validées le 28/10/2026).
"""

import sys
import unittest
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kpi.kpi.indicateurs import (  # noqa: E402 - chemin ajusté pour les tests
    NbConversions,
    NbDemandes,
    NbProspects,
    RdvParCanal,
    TauxConversion,
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


class TestNbConversions(unittest.TestCase):
    """Tests de l'indicateur « Nombre de conversions »."""

    #: Jeu de données dédié pour les conversions.
    #: Période testée P = mars 2025 ((2025, 3), (2025, 3)).
    #: - Alice : demande janv (avant P), pas de Confirmation → demande ouverte
    #: - Bob : demande janv (avant P), Confirmation fév (avant P) → demande FERMÉE
    #:   (la Confirmation n'est pas dans P mais avant fin P, donc la demande est fermée)
    #: - Chloé : demande mars (dans P), Confirmation mars → demande ouverte + conversion
    #: - Dave : demande fév (avant P), pas de Confirmation → demande ouverte
    #: - Émilie : demande mars (dans P), pas de Confirmation → demande ouverte
    #: - Franck : pas de demande, Confirmation mars → conversion seule (statut (vide), exclue du dépliement)
    _TOUS = [
        EvenementSuivi(
            date=date(2025, 1, 10), personne="Alice",
            statut_contact="prospect", action_public="Demande", canal="mail",
        ),
        EvenementSuivi(
            date=date(2025, 1, 10), personne="Bob",
            statut_contact="prospect", action_public="Demande", canal="mail",
        ),
        EvenementSuivi(
            date=date(2025, 2, 1), personne="Bob",
            action_photographe="Confirmation",  # avant P, mais ≤ fin P → ferme la demande
        ),
        EvenementSuivi(
            date=date(2025, 2, 5), personne="Dave",
            statut_contact="prospect", action_public="Demande", canal="tel",
        ),
        EvenementSuivi(
            date=date(2025, 3, 1), personne="Chloé",
            statut_contact="client", action_public="Demande", canal="mail",
        ),
        EvenementSuivi(
            date=date(2025, 3, 2), personne="Émilie",
            statut_contact="prospect", action_public="Demande", canal="site",
        ),
        # Confirmations dans P (mars)
        EvenementSuivi(
            date=date(2025, 3, 10), personne="Bob",
            action_photographe="Confirmation",
        ),
        EvenementSuivi(
            date=date(2025, 3, 12), personne="Chloé",
            action_photographe="Confirmation",
        ),
        EvenementSuivi(
            date=date(2025, 3, 20), personne="Franck",
            action_photographe="Confirmation",
        ),
    ]
    _DEBUT = (2025, 3)
    _FIN = (2025, 3)

    def test_ligne_tous(self) -> None:
        """3 Confirmations dans P (Bob, Chloé, Franck) — somme des canaux sous « Tous »."""
        _lignes = NbConversions().calculer_periode(
            self._TOUS, self._DEBUT, self._FIN
        )
        _total = sum(_l.valeur for _l in _lignes if _l.dimensions[0] == "Tous")
        self.assertEqual(int(_total), 3)

    def test_depliement_par_statut(self) -> None:
        """client=1 (Chloé), prospect=2 (Bob + Franck)."""
        _lignes = NbConversions().calculer_periode(
            self._TOUS, self._DEBUT, self._FIN
        )
        _par_statut = {}
        for _l in _lignes:
            if _l.dimensions[0] in ("client", "prospect"):
                _par_statut[_l.dimensions[0]] = _par_statut.get(_l.dimensions[0], 0) + int(_l.valeur)
        self.assertEqual(_par_statut.get("client"), 1)
        self.assertEqual(_par_statut.get("prospect"), 2)

    def test_confirmation_hors_periode_ignoree(self) -> None:
        """Une Confirmation en avril n'est pas comptée pour P=mars."""
        _ev = self._TOUS + [
            EvenementSuivi(
                date=date(2025, 4, 1), personne="Alice",
                action_photographe="Confirmation",
            )
        ]
        _lignes = NbConversions().calculer_periode(_ev, self._DEBUT, self._FIN)
        _total = sum(_l.valeur for _l in _lignes if _l.dimensions[0] == "Tous")
        self.assertEqual(int(_total), 3)  # pas 4


class TestTauxConversion(unittest.TestCase):
    """Tests de l'indicateur « Taux de conversion »."""

    _TOUS = TestNbConversions._TOUS
    _DEBUT = TestNbConversions._DEBUT
    _FIN = TestNbConversions._FIN

    def test_taux_global(self) -> None:
        """Vérifie le détail par canal sous « Tous ».
        Demandeurs ouverts: Alice(mail), Chloé(mail), Dave(tel), Émilie(site).
        Confirmations P: Bob(mail), Chloé(mail), Franck((vide)).
        → Tous/mail = 2 conf / 2 demandeurs = 100 %."""
        _lignes = TauxConversion().calculer_periode(
            self._TOUS, self._DEBUT, self._FIN
        )
        _lignes_tous = [_l for _l in _lignes if _l.dimensions[0] == "Tous"]
        self.assertTrue(len(_lignes_tous) > 0)
        _mail = [_l for _l in _lignes_tous if _l.dimensions[1] == "mail"][0]
        self.assertAlmostEqual(_mail.valeur, 100.0)  # 2 conf / 2 demandeurs

    def test_demande_avant_periode_sans_confirmation_ouverte(self) -> None:
        """Alice (demande janv mail, aucune Confirmation) est ouverte :
        elle est dans les demandeurs mail → 2 demandeurs mail, 2 conf → 100 %."""
        _lignes = TauxConversion().calculer_periode(
            self._TOUS, self._DEBUT, self._FIN
        )
        _mail = [_l for _l in _lignes if _l.dimensions == ("Tous", "mail")][0]
        self.assertAlmostEqual(_mail.valeur, 100.0)

    def test_demande_avant_periode_confirmation_avant_fin_fermee(self) -> None:
        """Bob (demande janv mail, Confirmation fév ≤ fin P) : demande FERMÉE, pas demandeur.
        Mais sa Confirmation de mars compte quand même → mail = 2 conf / 2 demandeurs = 100 %.
        Si Bob était demandeur : 3 demandeurs, taux = 2/3 = 66,7 %."""
        _lignes = TauxConversion().calculer_periode(
            self._TOUS, self._DEBUT, self._FIN
        )
        _mail = [_l for _l in _lignes if _l.dimensions == ("Tous", "mail")][0]
        self.assertAlmostEqual(_mail.valeur, 100.0)  # et pas 66,7 %

    def test_composante_clients(self) -> None:
        """Client canal mail : Chloé = 1 demandeur, 1 Confirmation → 100 %."""
        _lignes = TauxConversion().calculer_periode(
            self._TOUS, self._DEBUT, self._FIN
        )
        _client_mail = [_l for _l in _lignes if _l.dimensions == ("client", "mail")][0]
        self.assertAlmostEqual(_client_mail.valeur, 100.0)

    def test_composante_prospects(self) -> None:
        """Prospect canal mail : Alice = 1 demandeur, Bob = 1 Confirmation → 100 %."""
        _lignes = TauxConversion().calculer_periode(
            self._TOUS, self._DEBUT, self._FIN
        )
        _prospect_mail = [_l for _l in _lignes if _l.dimensions == ("prospect", "mail")][0]
        self.assertAlmostEqual(_prospect_mail.valeur, 100.0)

    def test_statut_vide_devient_prospect(self) -> None:
        """Une Demande avec statut=None est classée 'prospect' (pas '(vide)')."""
        _ev = self._TOUS + [
            EvenementSuivi(
                date=date(2025, 3, 5), personne="TestVide",
                statut_contact=None, action_public="Demande",
            ),
            EvenementSuivi(
                date=date(2025, 3, 10), personne="TestVide",
                action_photographe="Confirmation",
            ),
        ]
        _lignes = NbConversions().calculer_periode(_ev, self._DEBUT, self._FIN)
        _statuts = {_l.dimensions[0] for _l in _lignes}
        self.assertIn("prospect", _statuts)
        self.assertNotIn("(vide)", _statuts)

    def test_aucune_demande_ouverte(self) -> None:
        """Période avant toutes les demandes (2024) → aucune ligne."""
        _lignes = TauxConversion().calculer_periode(
            self._TOUS, (2024, 1), (2024, 1)
        )
        self.assertEqual(len(_lignes), 0)

    def test_taux_borne_0_100(self) -> None:
        """Le taux est toujours entre 0 et 100 %."""
        _lignes = TauxConversion().calculer_periode(
            self._TOUS, self._DEBUT, self._FIN
        )
        for _l in _lignes:
            self.assertGreaterEqual(_l.valeur, 0.0)
            self.assertLessEqual(_l.valeur, 100.0)

    def test_statut_premiere_demande(self) -> None:
        """Le statut retenu est celui de la première demande chronologique."""
        _ev = [
            EvenementSuivi(
                date=date(2025, 1, 1), personne="Test",
                statut_contact="prospect", action_public="Demande",
            ),
            EvenementSuivi(
                date=date(2025, 3, 15), personne="Test",
                statut_contact="client", action_public="Demande",
            ),
            EvenementSuivi(
                date=date(2025, 3, 20), personne="Test",
                action_photographe="Confirmation",
            ),
        ]
        _lignes = NbConversions().calculer_periode(_ev, (2025, 3), (2025, 3))
        _statuts = {_l.dimensions[0] for _l in _lignes}
        self.assertIn("prospect", _statuts)
        self.assertNotIn("client", _statuts)

    def test_detail_periode_compteurs(self) -> None:
        """Détail demandes/confirmations par (« Tous »/statut, canal).

        Avec le jeu _TOUS sur P = mars 2025 : demandeurs ouverts =
        Alice (prospect, mail), Chloé (client, mail), Dave (prospect, tel),
        Émilie (prospect, site) ; Confirmations = Bob (prospect, mail),
        Chloé (client, mail), Franck (prospect, canal (vide)).
        Les combinaisons à 0 % (tel, site) sont présentes aussi : elles
        doivent peser dans le dénominateur du taux agrégé par statut.
        """
        _detail = TauxConversion().calculer_detail_periode(
            self._TOUS, self._DEBUT, self._FIN
        )
        _par_cle = {
            _d.dimensions: (_d.demandes, _d.confirmations) for _d in _detail
        }
        self.assertEqual(_par_cle[("Tous", "mail")], (2, 2))
        self.assertEqual(_par_cle[("Tous", "tel")], (1, 0))
        self.assertEqual(_par_cle[("Tous", "site")], (1, 0))
        self.assertEqual(_par_cle[("Tous", "(vide)")], (0, 1))
        self.assertEqual(_par_cle[("client", "mail")], (1, 1))
        self.assertEqual(_par_cle[("prospect", "mail")], (1, 1))
        self.assertEqual(_par_cle[("prospect", "tel")], (1, 0))

    def test_taux_global_recalcule_depuis_compteurs(self) -> None:
        """Taux global = somme confirmations / somme demandes = 3/4 = 75 %.

        Ce n'est PAS la moyenne des taux par canal (qui donnerait
        (100 + 0 + 0)/3 ≈ 33,3 % sur les canaux avec demande).
        """
        _taux = TauxConversion().taux_global_periode(
            self._TOUS, self._DEBUT, self._FIN
        )
        self.assertAlmostEqual(_taux, 75.0)

    def test_taux_agrege_par_statut_depuis_detail(self) -> None:
        """Taux agrégé par statut, recalculé depuis le détail (non sommé).

        prospect = 2 confirmations / 3 demandes ≈ 66,7 % (et pas 100 %),
        client = 1/1 = 100 %.
        """
        _detail = TauxConversion().calculer_detail_periode(
            self._TOUS, self._DEBUT, self._FIN
        )
        _dem: dict[str, int] = defaultdict(int)
        _conf: dict[str, int] = defaultdict(int)
        for _d in _detail:
            if _d.dimensions[0] != "Tous":
                _dem[_d.dimensions[0]] += _d.demandes
                _conf[_d.dimensions[0]] += _d.confirmations
        _taux_prospect = _conf["prospect"] / _dem["prospect"] * 100
        self.assertAlmostEqual(_taux_prospect, 200 / 3)
        self.assertAlmostEqual(_conf["client"] / _dem["client"] * 100, 100.0)

    def test_taux_global_sans_demande(self) -> None:
        """Aucune demande ouverte sur la période → taux global = 0."""
        _taux = TauxConversion().taux_global_periode(
            self._TOUS, (2024, 1), (2024, 1)
        )
        self.assertEqual(_taux, 0.0)


if __name__ == "__main__":
    unittest.main()
