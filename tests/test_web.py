"""Tests de l'écran web de saisie du suivi.

Les tests utilisent une base temporaire et des données synthétiques
anonymes. Le client de test suit les redirections comme un navigateur :
un enregistrement réussi aboutit donc à la page de saisie avec message de
confirmation, jamais à un double enregistrement lors du rafraîchissement.
"""

import re
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient  # noqa: E402 - chemin ajusté pour les tests

from kpi.bdd.connexion import BaseDonnees  # noqa: E402 - chemin ajusté pour les tests
from kpi.bdd.modeles import ReferentielRepository, SuiviRepository  # noqa: E402 - chemin ajusté pour les tests
from kpi.suivi import EvenementSuivi  # noqa: E402 - chemin ajusté pour les tests
from kpi.web.routes import (  # noqa: E402 - chemin ajusté pour les tests
    ApplicationWeb,
    _bornes_annees_mois,
    _periode_par_defaut,
)

#: Valeurs de référence minimales pour alimenter les listes déroulantes.
REFERENTIELS_TEST = {
    "statut_contact": ["prospect", "client"],
    "prestation": ["Mariage", "Séances"],
    "detail_prestation": ["Famille", "Portrait"],
    "action": ["Demande", "Paiement", "Réponse", "RDV"],
    "canal": ["mail", "téléphone", "instagram"],
    "provenance": ["Google", "Instagram"],
}


class TestEcranSaisie(unittest.TestCase):
    """Tests des pages de saisie, de modification et de suppression."""

    def setUp(self) -> None:
        """Prépare une base temporaire et le client de test."""
        self._dossier = tempfile.TemporaryDirectory()
        self._chemin_base = Path(self._dossier.name) / "test.sqlite3"
        _base = BaseDonnees(self._chemin_base)
        try:
            _referentiels = ReferentielRepository(_base)
            for _table, _valeurs in REFERENTIELS_TEST.items():
                for _valeur in _valeurs:
                    _referentiels.obtenir_ou_creer(_table, _valeur)
            _base.valider()
        finally:
            _base.fermer()
        self._application = ApplicationWeb(self._chemin_base)
        self._client = TestClient(self._application.application)

    def tearDown(self) -> None:
        """Supprime le dossier temporaire (le client est déjà refermé)."""
        self._dossier.cleanup()

    def _compter(self) -> int:
        """Compte les événements avec une connexion indépendante."""
        _base = BaseDonnees(self._chemin_base)
        try:
            return SuiviRepository(_base).compter()
        finally:
            _base.fermer()

    def test_page_saisie(self) -> None:
        """Par défaut, seul le lien « Ajouter » est visible (formulaire masqué)."""
        _reponse = self._client.get("/")
        self.assertEqual(_reponse.status_code, 200)
        self.assertIn("Ajouter un événement", _reponse.text)
        self.assertIn("afficher_formulaire=1", _reponse.text)
        self.assertNotIn("Qui et quand", _reponse.text)

    def test_page_saisie_avec_formulaire(self) -> None:
        """Le formulaire s'affiche avec ?afficher_formulaire=1."""
        _reponse = self._client.get("/?afficher_formulaire=1")
        self.assertEqual(_reponse.status_code, 200)
        self.assertIn("Qui et quand", _reponse.text)
        self.assertIn("La demande", _reponse.text)
        self.assertIn("La réponse de la photographe", _reponse.text)
        self.assertIn("mail", _reponse.text)
        self.assertIn("Un nom absent de la liste sera créé automatiquement", _reponse.text)

    def test_lien_ajouter_conserve_filtres_et_page(self) -> None:
        """Le lien « Ajouter » conserve les filtres, le tri et la page actifs."""
        _reponse = self._client.get("/?filtre_personne=alice&tri=personne&sens=asc&page=2")
        self.assertIn("afficher_formulaire=1", _reponse.text)
        self.assertIn("filtre_personne=alice", _reponse.text)
        self.assertIn("page=2", _reponse.text)

    def test_apres_enregistrement_formulaire_reste_visible(self) -> None:
        """La redirection après enregistrement conserve afficher_formulaire=1."""
        _reponse = self._client.post(
            "/evenements",
            data={"date": "2025-01-14", "personne": "Alice Martin"},
        )
        self.assertIn("afficher_formulaire=1", str(_reponse.url))
        self.assertIn("Qui et quand", _reponse.text)

    def test_bouton_fermer_masque_le_formulaire(self) -> None:
        """Quand le formulaire est visible, « Fermer » est à côté du titre.

        Le lien conserve les filtres actifs mais retire afficher_formulaire.
        """
        _reponse = self._client.get("/?afficher_formulaire=1&filtre_personne=alice&page=2")
        # « Fermer » est dans l'en-tête du formulaire, à côté du titre.
        self.assertIn('entete-formulaire', _reponse.text)
        _m = re.search(
            r'<div class="entete-formulaire">.*?Nouvel événement.*?Fermer.*?</div>',
            _reponse.text, re.DOTALL,
        )
        self.assertIsNotNone(_m, "Le lien Fermer doit être à côté du titre")
        self.assertIn("filtre_personne=alice", _reponse.text)
        # Le lien Fermer ne contient pas afficher_formulaire.
        _liens_fermer = re.findall(r'href="([^"]*page=2[^"]*)"', _reponse.text)
        self.assertTrue(any("afficher_formulaire" not in _l for _l in _liens_fermer))

    def test_formulaire_sans_lien_gerer_listes(self) -> None:
        """Le lien « Gérer les listes » n'est plus dans le formulaire."""
        _reponse = self._client.get("/?afficher_formulaire=1")
        self.assertNotIn("Gérer les listes", _reponse.text)
        # Le lien « Listes » reste dans la barre de navigation.
        self.assertIn('href="/listes"', _reponse.text)

    def test_enregistrement_et_redirection(self) -> None:
        """Un enregistrement valide crée l'événement puis confirme.

        Le message rappelle que le formulaire est prêt pour la même
        personne, et l'événement est bien durable en base (lu depuis une
        seconde connexion) avant l'affichage.
        """
        _reponse = self._client.post(
            "/evenements",
            data={
                "date": "2025-01-14",
                "personne": "Alice Martin",
                "statut_contact": "prospect",
                "action_public": "Demande",
                "canal": "mail",
                "provenance": "Google",
                "prestation": "Séances",
                "detail_prestation": "Famille",
                "action_photographe": "",
                "canal2": "",
                "commentaire": "Premier contact",
            },
        )
        self.assertEqual(_reponse.status_code, 200)
        # La redirection a bien eu lieu (303) avant l'affichage final.
        self.assertEqual(_reponse.history[-1].status_code, 303)
        self.assertIn("Événement enregistré", _reponse.text)
        self.assertIn("Alice Martin", _reponse.text)
        self.assertEqual(self._compter(), 1)

        # Un événement créé se lit depuis une connexion indépendante.
        _base = BaseDonnees(self._chemin_base)
        try:
            _evenements = SuiviRepository(_base).lister()
        finally:
            _base.fermer()
        self.assertEqual(len(_evenements), 1)
        self.assertEqual(_evenements[0].personne, "Alice Martin")
        self.assertEqual(_evenements[0].commentaire, "Premier contact")

    def test_personne_pre_replie_apres_enregistrement(self) -> None:
        """Après un enregistrement, la personne reste préremplie."""
        self._client.post(
            "/evenements",
            data={"date": "2025-02-01", "personne": "Bob Dupont", "commentaire": ""},
        )
        _reponse = self._client.get("/?afficher_formulaire=1")
        # La valeur est présente dans le champ du formulaire.
        self.assertIn('value="Bob Dupont"', _reponse.text)

    def test_date_invalide_conserve_le_formulaire(self) -> None:
        """Une date invalide est refusée sans perdre la saisie."""
        _reponse = self._client.post(
            "/evenements",
            data={
                "date": "pas-une-date",
                "personne": "Alice Martin",
                "commentaire": "Saisie gardée",
            },
        )
        self.assertEqual(_reponse.status_code, 400)
        self.assertIn("pas valide (jj/mm/aaaa)", _reponse.text)
        self.assertIn("Saisie gardée", _reponse.text)
        self.assertEqual(self._compter(), 0)

    def test_personne_vide_refusee(self) -> None:
        """Un nom composé d'espaces est refusé, rien n'est enregistré."""
        _reponse = self._client.post(
            "/evenements",
            data={"date": "2025-01-14", "personne": "   "},
        )
        self.assertEqual(_reponse.status_code, 400)
        self.assertIn("Le nom de la personne est obligatoire", _reponse.text)
        self.assertEqual(self._compter(), 0)

    def test_nouvelle_personne_creee(self) -> None:
        """Un nom inconnu est accepté : la personne est créée à la saisie."""
        self._client.post(
            "/evenements",
            data={"date": "2025-03-02", "personne": "Chloé Bernard"},
        )
        _base = BaseDonnees(self._chemin_base)
        try:
            _evenements = SuiviRepository(_base).lister()
        finally:
            _base.fermer()
        self.assertEqual(_evenements[0].personne, "Chloé Bernard")

    def test_html_echappe(self) -> None:
        """Un commentaire contenant du HTML est affiché tel quel, échappé."""
        self._client.post(
            "/evenements",
            data={"date": "2025-04-01", "personne": "Dave", "commentaire": "<b>gras</b>"},
        )
        _reponse = self._client.get("/")
        self.assertNotIn("<b>gras</b>", _reponse.text)
        self.assertIn("&lt;b&gt;gras&lt;/b&gt;", _reponse.text)

    def test_modification(self) -> None:
        """La correction modifie l'événement existant, sans en créer un autre."""
        self._client.post(
            "/evenements",
            data={"date": "2025-01-14", "personne": "Alice Martin", "action_public": "Demande"},
        )
        _base = BaseDonnees(self._chemin_base)
        try:
            _identifiant = SuiviRepository(_base).lister()[0].id
        finally:
            _base.fermer()

        # Le formulaire de modification est prérempli.
        _reponse = self._client.get(f"/evenements/{_identifiant}/modifier")
        self.assertEqual(_reponse.status_code, 200)
        self.assertIn("Modifier un événement", _reponse.text)
        self.assertIn('value="Alice Martin"', _reponse.text)

        # La correction remplace les valeurs, sans créer de doublon.
        _reponse = self._client.post(
            f"/evenements/{_identifiant}/modifier",
            data={"date": "2025-01-20", "personne": "Alice Martin", "action_public": "Paiement"},
        )
        self.assertEqual(_reponse.status_code, 200)
        self.assertEqual(self._compter(), 1)
        _base = BaseDonnees(self._chemin_base)
        try:
            _evenement = SuiviRepository(_base).lister()[0]
        finally:
            _base.fermer()
        self.assertEqual(_evenement.action_public, "Paiement")
        self.assertEqual(_evenement.date, date(2025, 1, 20))

    def test_identifiant_inconnu_refuse(self) -> None:
        """Un identifiant inexistant renvoie 404, sans écrire en base."""
        self.assertEqual(self._client.get("/evenements/999/modifier").status_code, 404)
        _reponse = self._client.post(
            "/evenements/999/modifier",
            data={"date": "2025-01-14", "personne": "Alice"},
        )
        self.assertEqual(_reponse.status_code, 404)
        self.assertEqual(self._client.get("/evenements/999/supprimer").status_code, 404)
        self.assertEqual(self._client.post("/evenements/999/supprimer").status_code, 404)

    def test_suppression_avec_confirmation(self) -> None:
        """La suppression exige une page de confirmation explicite."""
        self._client.post(
            "/evenements",
            data={"date": "2025-01-14", "personne": "Alice Martin"},
        )
        _base = BaseDonnees(self._chemin_base)
        try:
            _identifiant = SuiviRepository(_base).lister()[0].id
        finally:
            _base.fermer()

        # La page de confirmation rappelle la personne et la date.
        _reponse = self._client.get(f"/evenements/{_identifiant}/supprimer")
        self.assertEqual(_reponse.status_code, 200)
        self.assertIn("Alice Martin", _reponse.text)
        self.assertIn("irréversible", _reponse.text)
        self.assertEqual(self._compter(), 1)

        # La confirmation supprime effectivement l'événement.
        _reponse = self._client.post(f"/evenements/{_identifiant}/supprimer")
        self.assertEqual(_reponse.status_code, 200)
        self.assertEqual(self._compter(), 0)

    def test_ecriture_interdite_depuis_un_autre_site(self) -> None:
        """Une requête POST avec une origine externe est refusée (403)."""
        _reponse = self._client.post(
            "/evenements",
            data={"date": "2025-01-14", "personne": "Alice Martin"},
            headers={"origin": "http://exemple-mechant.fr", "host": "testserver"},
        )
        self.assertEqual(_reponse.status_code, 403)
        self.assertEqual(self._compter(), 0)

    def test_rafraichissement_ne_double_pas(self) -> None:
        """Recharger la page après enregistrement n'ajoute rien."""
        for _ in range(2):
            self._client.post(
                "/evenements",
                data={"date": "2025-01-14", "personne": "Alice Martin"},
            )
        # Deux soumissions explicites = deux événements, c'est voulu.
        self.assertEqual(self._compter(), 2)
        # Mais un simple GET de la page de confirmation n'écrit rien.
        self._client.get("/?personne=Alice%20Martin&enregistre=1")
        self.assertEqual(self._compter(), 2)

    def test_evenements_recents_affiches(self) -> None:
        """Les événements enregistrés apparaissent dans la liste."""
        self._client.post(
            "/evenements",
            data={"date": "2025-01-14", "personne": "Alice Martin", "action_public": "Demande"},
        )
        _reponse = self._client.get("/")
        self.assertIn("Derniers événements", _reponse.text)
        self.assertIn("Alice Martin", _reponse.text)
        self.assertIn("14/01/2025", _reponse.text)

    def test_commentaire_complet_dans_liste(self) -> None:
        """Un commentaire long est présent en entier dans le HTML de la liste."""
        _commentaire_long = (
            "Premier contact par Instagram, la personne souhaite un devis "
            "pour un mariage en juin 2025 avec une cinquantaine d invites, "
            "budget serre, a suivre rapidement."
        )
        self._client.post(
            "/evenements",
            data={"date": "2025-01-14", "personne": "Alice Martin", "commentaire": _commentaire_long},
        )
        _reponse = self._client.get("/")
        self.assertIn(_commentaire_long, _reponse.text)

    def test_commentaire_title(self) -> None:
        """La cellule commentaire a un attribut title avec le commentaire complet."""
        _commentaire = "Rendez-vous confirmé pour le 15 mars à 14h au studio."
        self._client.post(
            "/evenements",
            data={"date": "2025-01-14", "personne": "Bob Dupont", "commentaire": _commentaire},
        )
        _reponse = self._client.get("/")
        self.assertIn(f'title="{_commentaire}"', _reponse.text)

    def test_commentaire_sans_title_si_vide(self) -> None:
        """Pas d'attribut title quand le commentaire est vide."""
        self._client.post(
            "/evenements",
            data={"date": "2025-01-14", "personne": "Chloé Bernard", "commentaire": ""},
        )
        _reponse = self._client.get("/")
        self.assertNotIn('class="commentaire" title=', _reponse.text)

    def test_commentaire_css_sans_troncature(self) -> None:
        """Le CSS du tableau garantit le retour à la ligne sans troncature."""
        _reponse = self._client.get("/")
        self.assertIn("max-width: 22rem", _reponse.text)
        self.assertIn("overflow-wrap: break-word", _reponse.text)


class TestTriEtFiltres(unittest.TestCase):
    """Tests du tri et des filtres de la liste des événements."""

    def setUp(self) -> None:
        """Prépare une base avec trois événements à des dates distinctes."""
        self._dossier = tempfile.TemporaryDirectory()
        self._chemin_base = Path(self._dossier.name) / "test.sqlite3"
        _base = BaseDonnees(self._chemin_base)
        try:
            _referentiels = ReferentielRepository(_base)
            for _table, _valeurs in REFERENTIELS_TEST.items():
                for _valeur in _valeurs:
                    _referentiels.obtenir_ou_creer(_table, _valeur)
            _base.valider()
        finally:
            _base.fermer()
        self._application = ApplicationWeb(self._chemin_base)
        self._client = TestClient(self._application.application)
        self._client.post(
            "/evenements",
            data={"date": "2025-01-14", "personne": "Alice Martin", "action_public": "Demande"},
        )
        self._client.post(
            "/evenements",
            data={"date": "2025-03-02", "personne": "Bob Dupont", "action_public": "Paiement"},
        )
        self._client.post(
            "/evenements",
            data={"date": "2025-02-10", "personne": "Chloé Bernard", "action_public": "Réponse"},
        )

    def tearDown(self) -> None:
        """Supprime le dossier temporaire."""
        self._dossier.cleanup()

    def test_tri_par_defaut_date_decroissante(self) -> None:
        """Sans paramètre, l'interaction la plus récente apparaît en premier."""
        _reponse = self._client.get("/")
        self.assertEqual(_reponse.status_code, 200)
        self.assertLess(
            _reponse.text.index("02/03/2025"),
            _reponse.text.index("10/02/2025"),
        )
        self.assertLess(
            _reponse.text.index("10/02/2025"),
            _reponse.text.index("14/01/2025"),
        )

    def test_tri_croissant_demande(self) -> None:
        """Le tri explicite croissant inverse l'ordre par défaut."""
        _reponse = self._client.get("/?tri=date&sens=asc")
        self.assertLess(
            _reponse.text.index("14/01/2025"),
            _reponse.text.index("02/03/2025"),
        )

    def test_tri_par_personne(self) -> None:
        """Le tri par personne ordonne les noms alphabétiquement.

        La vérification porte sur les dates des lignes (Alice, Bob puis
        Chloé), les noms apparaissant aussi dans les suggestions.
        """
        _reponse = self._client.get("/?tri=personne&sens=asc")
        self.assertLess(
            _reponse.text.index("14/01/2025"),
            _reponse.text.index("02/03/2025"),
        )
        self.assertLess(
            _reponse.text.index("02/03/2025"),
            _reponse.text.index("10/02/2025"),
        )

    def test_tri_colonne_inconnue_ignore(self) -> None:
        """Une colonne inconnue retombe sur le tri par défaut, sans erreur."""
        _reponse = self._client.get("/?tri=bidon&sens=desc")
        self.assertEqual(_reponse.status_code, 200)
        self.assertLess(
            _reponse.text.index("02/03/2025"),
            _reponse.text.index("14/01/2025"),
        )

    def test_departage_ordre_saisie_decroissant(self) -> None:
        """À date égale, la saisie la plus récente apparaît en premier.

        Deux événements sont saisis le même jour (02/03/2025, date déjà
        portée par l'événement de Bob) : au tri par défaut (date
        décroissante), le commentaire de la saisie la plus récente
        précède celui de la saisie antérieure.
        """
        self._client.post(
            "/evenements",
            data={"date": "2025-03-02", "personne": "Alice Martin",
                  "commentaire": "saisie ancienne"},
        )
        self._client.post(
            "/evenements",
            data={"date": "2025-03-02", "personne": "Bob Dupont",
                  "commentaire": "saisie récente"},
        )
        _reponse = self._client.get("/")
        self.assertEqual(_reponse.status_code, 200)
        self.assertLess(
            _reponse.text.index("saisie récente"),
            _reponse.text.index("saisie ancienne"),
        )

    def test_ordre_saisie_non_affiche(self) -> None:
        """Aucune colonne ni aucun lien de tri sur l'ordre de saisie."""
        _reponse = self._client.get("/")
        self.assertEqual(_reponse.status_code, 200)
        self.assertNotIn("ordre_saisie", _reponse.text)
        self.assertNotIn("tri=ordre_saisie", _reponse.text)
        self.assertNotIn("N°", _reponse.text)

    def test_filtre_personne_insensible_a_la_casse(self) -> None:
        """Le filtre personne ne garde que les événements correspondants.

        Les noms apparaissent aussi dans la liste de suggestion du
        formulaire : la vérification porte sur les dates des lignes.
        """
        _reponse = self._client.get("/?filtre_personne=alice")
        self.assertIn("14/01/2025", _reponse.text)
        self.assertNotIn("02/03/2025", _reponse.text)
        self.assertNotIn("10/02/2025", _reponse.text)

    def test_filtre_sans_resultat(self) -> None:
        """Un filtre sans correspondance affiche un message explicite."""
        _reponse = self._client.get("/?filtre_personne=inconnu")
        self.assertIn("Aucun événement ne correspond aux filtres actuels", _reponse.text)

    def test_filtre_conserve_le_tri(self) -> None:
        """Filtrer et trier se combinent : la plus récente d'abord."""
        self._client.post(
            "/evenements",
            data={"date": "2025-04-05", "personne": "Alice Robert"},
        )
        _reponse = self._client.get("/?filtre_personne=alice")
        self.assertLess(
            _reponse.text.index("05/04/2025"),
            _reponse.text.index("14/01/2025"),
        )
        self.assertNotIn("02/03/2025", _reponse.text)

    def test_liens_de_tri_dans_l_entete(self) -> None:
        """Chaque colonne propose un lien de tri, l'active indique le sens."""
        _reponse = self._client.get("/")
        self.assertIn('href="/?tri=personne&amp;sens=asc"', _reponse.text)
        # La colonne active (date, décroissante par défaut) propose l'inverse.
        self.assertIn('href="/?tri=date&amp;sens=asc"', _reponse.text)
        self.assertIn("▼", _reponse.text)


class TestPagination(unittest.TestCase):
    """Tests de la pagination de la liste des événements (10 par page)."""

    def setUp(self) -> None:
        """Prépare une base avec 25 événements sur des dates distinctes."""
        self._dossier = tempfile.TemporaryDirectory()
        self._chemin_base = Path(self._dossier.name) / "test.sqlite3"
        _base = BaseDonnees(self._chemin_base)
        try:
            _referentiels = ReferentielRepository(_base)
            for _table, _valeurs in REFERENTIELS_TEST.items():
                for _valeur in _valeurs:
                    _referentiels.obtenir_ou_creer(_table, _valeur)
            _base.valider()
        finally:
            _base.fermer()
        self._application = ApplicationWeb(self._chemin_base)
        self._client = TestClient(self._application.application)
        # 25 événements du 01/01/2025 au 25/01/2025.
        for _jour in range(1, 26):
            self._client.post(
                "/evenements",
                data={"date": f"2025-01-{_jour:02d}", "personne": f"Pers{_jour:02d}"},
            )

    def tearDown(self) -> None:
        """Supprime le dossier temporaire."""
        self._dossier.cleanup()

    def test_page_1_affiche_10_evenements_et_lien_suivant(self) -> None:
        """La page 1 affiche 10 événements et un lien vers la page 2."""
        _reponse = self._client.get("/")
        self.assertIn("Page 1 / 3", _reponse.text)
        self.assertIn("25 événements", _reponse.text)
        self.assertIn("Suivant", _reponse.text)
        self.assertNotIn("Précédent", _reponse.text)
        # Le plus récent (25/01/2025) est en page 1.
        self.assertIn("25/01/2025", _reponse.text)
        # Le plus ancien (01/01/2025) est en page 3, pas en page 1.
        self.assertNotIn("01/01/2025", _reponse.text)

    def test_page_3_affiche_les_5_restants(self) -> None:
        """La dernière page affiche les 5 derniers événements."""
        _reponse = self._client.get("/?page=3")
        self.assertIn("Page 3 / 3", _reponse.text)
        self.assertIn("Précédent", _reponse.text)
        self.assertNotIn("Suivant", _reponse.text)
        self.assertIn("01/01/2025", _reponse.text)
        self.assertNotIn("25/01/2025", _reponse.text)

    def test_page_invalide_retombe_sur_1(self) -> None:
        """Un numéro de page invalide ou hors limites retombe sur une page valide."""
        _reponse = self._client.get("/?page=abc")
        self.assertIn("Page 1 / 3", _reponse.text)
        _reponse = self._client.get("/?page=99")
        self.assertIn("Page 3 / 3", _reponse.text)

    def test_pagination_conserve_les_filtres(self) -> None:
        """Les filtres réduisent le nombre d'événements affichés.

        La vérification porte sur les dates des lignes du tableau (les
        noms apparaissent aussi dans le datalist du formulaire).
        """
        _reponse = self._client.get("/?filtre_personne=pers2")
        self.assertIn("20/01/2025", _reponse.text)
        self.assertNotIn("01/01/2025", _reponse.text)

    def test_moins_de_10_evenements_pas_de_pagination(self) -> None:
        """Avec 10 événements ou moins, tous sont affichés sans barre de pagination."""
        _reponse = self._client.get("/?filtre_personne=pers1")
        # pers1 matche pers10 à pers19 (10 événements) -> pas de pagination.
        self.assertNotIn("Page 1 /", _reponse.text)


class TestGestionListes(unittest.TestCase):
    """Tests de la page de gestion des valeurs des listes déroulantes."""

    def setUp(self) -> None:
        """Prépare une base et un événement utilisant la valeur « mail »."""
        self._dossier = tempfile.TemporaryDirectory()
        self._chemin_base = Path(self._dossier.name) / "test.sqlite3"
        _base = BaseDonnees(self._chemin_base)
        try:
            _referentiels = ReferentielRepository(_base)
            for _table, _valeurs in REFERENTIELS_TEST.items():
                for _valeur in _valeurs:
                    _referentiels.obtenir_ou_creer(_table, _valeur)
            _base.valider()
        finally:
            _base.fermer()
        self._application = ApplicationWeb(self._chemin_base)
        self._client = TestClient(self._application.application)
        self._client.post(
            "/evenements",
            data={"date": "2025-01-14", "personne": "Alice Martin", "canal": "mail"},
        )

    def tearDown(self) -> None:
        """Supprime le dossier temporaire."""
        self._dossier.cleanup()

    def test_page_listes(self) -> None:
        """La page affiche chaque liste, ses valeurs et leur utilisation."""
        _reponse = self._client.get("/listes")
        self.assertEqual(_reponse.status_code, 200)
        self.assertIn("Valeurs des listes déroulantes", _reponse.text)
        self.assertIn("Canaux", _reponse.text)
        self.assertIn("mail", _reponse.text)
        self.assertIn("1 événement", _reponse.text)

    def test_ajout_de_valeur(self) -> None:
        """Une valeur ajoutée apparaît dans la liste et le formulaire."""
        _reponse = self._client.post(
            "/listes/ajouter", data={"table": "canal", "valeur": "tiktok"}
        )
        self.assertEqual(_reponse.status_code, 200)
        self.assertIn("ajouté à la liste", _reponse.text)
        _reponse = self._client.get("/listes")
        self.assertIn("tiktok", _reponse.text)
        _reponse = self._client.get("/?afficher_formulaire=1")
        self.assertIn("tiktok", _reponse.text)

    def test_ajout_de_valeur_vide_refuse(self) -> None:
        """Une valeur vide est refusée avec un message explicite."""
        _reponse = self._client.post(
            "/listes/ajouter", data={"table": "canal", "valeur": "   "}
        )
        self.assertIn("ne peut pas être vide", _reponse.text)

    def test_ajout_de_valeur_existante_signale(self) -> None:
        """Ré-ajouter une valeur existante ne crée pas de doublon."""
        _reponse = self._client.post(
            "/listes/ajouter", data={"table": "canal", "valeur": "mail"}
        )
        self.assertIn("était déjà", _reponse.text)

    def test_renommage_suivi_par_les_evenements(self) -> None:
        """Renommer une valeur met à jour l'affichage des événements."""
        _reponse = self._client.post(
            "/listes/renommer",
            data={"table": "canal", "ancienne": "mail", "nouvelle": "courriel"},
        )
        self.assertIn("renommé en « courriel »", _reponse.text)
        # La liste et l'événement existant affichent le nouveau nom.
        self.assertIn("courriel", self._client.get("/listes").text)
        _reponse = self._client.get("/")
        self.assertIn("courriel", _reponse.text)
        self.assertNotIn(">mail<", _reponse.text)

    def test_renommage_vers_nom_deja_pris_refuse(self) -> None:
        """Renommer vers une valeur existante est refusé sans changement."""
        _reponse = self._client.post(
            "/listes/renommer",
            data={"table": "canal", "ancienne": "mail", "nouvelle": "instagram"},
        )
        self.assertIn("Impossible de renommer", _reponse.text)
        # L'ancienne valeur est toujours là.
        self.assertIn("mail", self._client.get("/listes").text)

    def test_retrait_de_valeur_utilisee(self) -> None:
        """Retirer une valeur utilisée prévient sans toucher aux événements."""
        _reponse = self._client.post(
            "/listes/retirer", data={"table": "canal", "ancienne": "mail"}
        )
        self.assertIn("retiré de la liste", _reponse.text)
        self.assertIn("1 événement", _reponse.text)
        # La valeur disparaît de la page des listes…
        _reponse = self._client.get("/listes")
        self.assertNotIn(">mail<", _reponse.text)
        # …mais l'événement la conserve.
        _reponse = self._client.get("/")
        self.assertIn("Alice Martin", _reponse.text)
        self.assertIn("mail", _reponse.text)

    def test_rajout_reactive_une_valeur_retiree(self) -> None:
        """Ré-ajouter une valeur retirée la remet dans la liste."""
        self._client.post("/listes/retirer", data={"table": "canal", "ancienne": "mail"})
        _reponse = self._client.post(
            "/listes/ajouter", data={"table": "canal", "valeur": "mail"}
        )
        self.assertIn("ajouté à la liste", _reponse.text)
        self.assertIn("mail", self._client.get("/listes").text)

    def test_liste_inconnue_refusee(self) -> None:
        """Une table hors référentiels est refusée avec un message clair."""
        _reponse = self._client.post(
            "/listes/ajouter", data={"table": "pirate", "valeur": "x"}
        )
        self.assertIn("Liste inconnue", _reponse.text)

    def test_ecriture_listes_interdite_depuis_un_autre_site(self) -> None:
        """Une requête POST avec une origine externe est refusée (403)."""
        _reponse = self._client.post(
            "/listes/ajouter",
            data={"table": "canal", "valeur": "tiktok"},
            headers={"origin": "http://exemple-mechant.fr", "host": "testserver"},
        )
        self.assertEqual(_reponse.status_code, 403)


class TestPageKpiGhosting(unittest.TestCase):
    """Tests de la page KPI pour l'indicateur Taux de ghosting.

    Le tableau des indicateurs à 2 dimensions est généré en JavaScript :
    la page doit donc définir ``isRatio`` avant son utilisation dans
    ``formatValue`` (régression : le tableau restait vide, seul le
    graphique était alimenté).
    """

    def setUp(self) -> None:
        """Prépare une base temporaire avec des demandes et réponses."""
        self._dossier = tempfile.TemporaryDirectory()
        self._chemin_base = Path(self._dossier.name) / "test.sqlite3"
        _base = BaseDonnees(self._chemin_base)
        try:
            _referentiels = ReferentielRepository(_base)
            for _table, _valeurs in REFERENTIELS_TEST.items():
                for _valeur in _valeurs:
                    _referentiels.obtenir_ou_creer(_table, _valeur)
            _suivi = SuiviRepository(_base)
            # Décembre 2025 : 1 demande, 1 réponse -> taux 0 %
            _suivi.ajouter(EvenementSuivi(
                date=date(2025, 12, 3), personne="Chloe",
                statut_contact="prospect",
                action_public="Demande", canal="mail",
            ))
            _suivi.ajouter(EvenementSuivi(
                date=date(2025, 12, 20), personne="Chloe",
                statut_contact="prospect",
                action_public="Réponse", canal="mail",
            ))
            # Janvier 2026 : 2 demandes, 1 réponse -> taux 50 %
            _suivi.ajouter(EvenementSuivi(
                date=date(2026, 1, 5), personne="Alice",
                statut_contact="prospect",
                action_public="Demande", canal="mail",
            ))
            _suivi.ajouter(EvenementSuivi(
                date=date(2026, 1, 10), personne="Bob",
                statut_contact="prospect",
                action_public="Demande", canal="instagram",
            ))
            _suivi.ajouter(EvenementSuivi(
                date=date(2026, 1, 12), personne="Alice",
                statut_contact="prospect",
                action_public="Réponse", canal="mail",
            ))
            # Février 2026 : 1 demande, 1 réponse -> taux 0 %
            _suivi.ajouter(EvenementSuivi(
                date=date(2026, 2, 2), personne="David",
                statut_contact="prospect",
                action_public="Demande", canal="téléphone",
            ))
            _suivi.ajouter(EvenementSuivi(
                date=date(2026, 2, 9), personne="David",
                statut_contact="prospect",
                action_public="Réponse", canal="téléphone",
            ))
            _base.valider()
        finally:
            _base.fermer()
        self._application = ApplicationWeb(self._chemin_base)
        self._client = TestClient(self._application.application)

    def tearDown(self) -> None:
        """Supprime le dossier temporaire."""
        self._dossier.cleanup()

    def test_tableau_ghosting_alimente_par_js(self) -> None:
        """Le bloc JS du tableau dépliable définit isRatio et les données.

        Avant la correction, ``formatValue`` levait une ReferenceError
        (isRatio non défini) : le tableau restait vide.
        """
        _reponse = self._client.get(
            "/kpi?indicateur=TauxGhosting&annee_debut=2026&mois_debut=1"
            "&annee_fin=2026&mois_fin=12"
        )
        self.assertEqual(_reponse.status_code, 200)
        # Le tableau dépliable est bien le mode d'affichage (2 dimensions).
        self.assertIn('id="corps-tableau"', _reponse.text)
        # isRatio est déclaré avant d'être utilisé par formatValue.
        self.assertIn("const isRatio = 1;", _reponse.text)
        # Les données du tableau JS contiennent le mois de janvier 2026.
        self.assertRegex(_reponse.text, r'dimensions:\s*\[2026, 1\]')
        self.assertIn("valeur: 0.5", _reponse.text)

    def test_tableau_autre_indicateur_2d_definit_isratio_a_zero(self) -> None:
        """Pour un indicateur à 2 dimensions non ratio, isRatio vaut 0."""
        _reponse = self._client.get(
            "/kpi?indicateur=NbConversions&annee_debut=2026&mois_debut=1"
            "&annee_fin=2026&mois_fin=12"
        )
        self.assertEqual(_reponse.status_code, 200)
        self.assertIn('id="corps-tableau"', _reponse.text)
        self.assertIn("const isRatio = 0;", _reponse.text)

    def test_detail_demandes_reponses_serialise(self) -> None:
        """Le détail demandes/réponses par mois est transmis au JS du tableau.

        Valeurs témoins : 2025/12 = 1 demande 1 réponse (taux 0 %) ;
        2026/1 = 2 demandes 1 réponse (taux 50 %) ; 2026/2 = 1 demande
        1 réponse (taux 0 %). Agrégat 2026 attendu : (3-2)/3 = 33,3 %,
        et non la somme des taux 50 % + 0 % = 50 %.
        """
        _reponse = self._client.get(
            "/kpi?indicateur=TauxGhosting&annee_debut=2025&mois_debut=1"
            "&annee_fin=2026&mois_fin=12"
        )
        self.assertEqual(_reponse.status_code, 200)
        self.assertIn('"2025/12"', _reponse.text)
        self.assertRegex(_reponse.text, r"demandes:\s*1,\s*reponses:\s*1")
        self.assertIn('"2026/1"', _reponse.text)
        self.assertRegex(_reponse.text, r"demandes:\s*2,\s*reponses:\s*1")

    def test_tableau_recalcule_le_taux_agrege(self) -> None:
        """Le JS recalcule le taux agrégé depuis demandes/réponses.

        Ne doit plus sommer les taux : la formule (D-R)/D sur les compteurs
        agrégés par préfixe doit être présente dans le bloc du tableau.
        """
        _reponse = self._client.get("/kpi?indicateur=TauxGhosting")
        self.assertEqual(_reponse.status_code, 200)
        self.assertIn("detailAgrege", _reponse.text)
        _formule = (
            "Math.max(0, (_detailAgg.demandes - _detailAgg.reponses)"
            " / _detailAgg.demandes)"
        )
        self.assertIn(_formule, _reponse.text)

    def test_tableau_total_zero_affiche_zero_pas_nan(self) -> None:
        """Un total nul s'affiche 0 % : le `||` sur la valeur est supprimé.

        Avant la correction, `formatValue(node.total || node)` recevait
        l'objet nœud quand le total était 0 et affichait « NaN% » (cas de
        l'année 2025 du jeu de test, taux 0 % sur son seul mois).
        """
        _reponse = self._client.get("/kpi?indicateur=TauxGhosting")
        self.assertEqual(_reponse.status_code, 200)
        self.assertNotIn("node.total || node", _reponse.text)
        self.assertNotIn("total || 0", _reponse.text)


class TestPageKpiConversion(unittest.TestCase):
    """Tests de la page KPI pour l'indicateur Taux de conversion.

    Le taux agrégé par statut doit être recalculé depuis les compteurs
    (confirmations / demandes ouvertes), jamais sommé depuis les taux
    par canal : avec ce jeu, « prospect » vaut 1/2 = 50 % et non 100 %.
    """

    def setUp(self) -> None:
        """Prépare une base temporaire avec demandes et confirmations."""
        self._dossier = tempfile.TemporaryDirectory()
        self._chemin_base = Path(self._dossier.name) / "test.sqlite3"
        _base = BaseDonnees(self._chemin_base)
        try:
            _referentiels = ReferentielRepository(_base)
            for _table, _valeurs in REFERENTIELS_TEST.items():
                for _valeur in _valeurs:
                    _referentiels.obtenir_ou_creer(_table, _valeur)
            _suivi = SuiviRepository(_base)
            # Alice : demande + confirmation (prospect, mail) -> 1/1 = 100 %
            _suivi.ajouter(EvenementSuivi(
                date=date(2026, 1, 5), personne="Alice",
                statut_contact="prospect",
                action_public="Demande", canal="mail",
            ))
            _suivi.ajouter(EvenementSuivi(
                date=date(2026, 1, 20), personne="Alice",
                action_photographe="Confirmation",
            ))
            # Bob : demande sans confirmation (prospect, instagram) -> 0/1
            _suivi.ajouter(EvenementSuivi(
                date=date(2026, 1, 10), personne="Bob",
                statut_contact="prospect",
                action_public="Demande", canal="instagram",
            ))
            # Chloé : demande sans confirmation (client, mail) -> 0/1 = 0 %
            _suivi.ajouter(EvenementSuivi(
                date=date(2026, 2, 2), personne="Chloe",
                statut_contact="client",
                action_public="Demande", canal="mail",
            ))
            _base.valider()
        finally:
            _base.fermer()
        self._application = ApplicationWeb(self._chemin_base)
        self._client = TestClient(self._application.application)

    def tearDown(self) -> None:
        """Supprime le dossier temporaire."""
        self._dossier.cleanup()

    def test_detail_confirmations_serialise(self) -> None:
        """Le détail demandes/confirmations par (statut, canal) est transmis.

        Y compris la combinaison à 0 % (prospect/instagram : 0 confirmation
        sur 1 demande) : elle doit peser dans le dénominateur du statut.
        """
        _reponse = self._client.get("/kpi?indicateur=TauxConversion")
        self.assertEqual(_reponse.status_code, 200)
        self.assertIn("const isConversion = 1;", _reponse.text)
        self.assertIn('"prospect/instagram"', _reponse.text)
        _regex = (
            r'"prospect/instagram":\s*\{\s*demandes:\s*1,'
            r"\s*confirmations:\s*0"
        )
        self.assertRegex(_reponse.text, _regex)
        self.assertRegex(
            _reponse.text,
            r'"prospect/mail":\s*\{\s*demandes:\s*1,\s*confirmations:\s*1',
        )

    def test_tableau_recalcule_le_taux_agrege_par_statut(self) -> None:
        """Le JS recalcule le taux d'un nœud parent (C/D × 100 agrégés).

        La formule sur les compteurs agrégés par préfixe doit être
        présente : un taux ne se somme jamais (prospect = 50 %, pas 100 %).
        """
        _reponse = self._client.get("/kpi?indicateur=TauxConversion")
        self.assertEqual(_reponse.status_code, 200)
        self.assertIn("detailAgrege", _reponse.text)
        self.assertIn(
            "_detailAgg.confirmations / _detailAgg.demandes * 100",
            _reponse.text,
        )


class TestCharteGraphique(unittest.TestCase):
    """Tests du thème conforme à la charte graphique (nov. 2026)."""

    def setUp(self) -> None:
        """Prépare une base temporaire et le client de test."""
        self._dossier = tempfile.TemporaryDirectory()
        self._chemin_base = Path(self._dossier.name) / "test.sqlite3"
        _base = BaseDonnees(self._chemin_base)
        try:
            _base.valider()
        finally:
            _base.fermer()
        self._application = ApplicationWeb(self._chemin_base)
        self._client = TestClient(self._application.application)

    def tearDown(self) -> None:
        """Supprime le dossier temporaire."""
        self._dossier.cleanup()

    def test_palette_charte_dans_variables_css(self) -> None:
        """Les variables CSS utilisent les couleurs de la charte officielle."""
        _reponse = self._client.get("/")
        self.assertEqual(_reponse.status_code, 200)
        _codes = ("#F4F2ED", "#353F38", "#757B74",
                  "#D0D3C5", "#FBFBF9", "#475836")
        for _code in _codes:
            self.assertIn(_code, _reponse.text)

    def test_ancienne_palette_absente(self) -> None:
        """L'ancien accent terracotta (#b4593b) n'apparaît plus."""
        _reponse = self._client.get("/")
        self.assertNotIn("#b4593b", _reponse.text)
        self.assertNotIn("rgba(180, 89, 59", _reponse.text)

    def test_favicon_pictogramme(self) -> None:
        """Le favicon est le pictogramme de la marque, servi en local."""
        _reponse = self._client.get("/")
        self.assertIn('rel="icon"', _reponse.text)
        self.assertIn("/static/favicon.png", _reponse.text)
        _fav = self._client.get("/static/favicon.png")
        self.assertEqual(_fav.status_code, 200)
        self.assertEqual(_fav.headers["content-type"], "image/png")

    def test_pied_de_page_logo_primaire(self) -> None:
        """Toutes les pages affichent le logo primaire en pied de page."""
        for _page in ("/", "/kpi", "/listes"):
            _reponse = self._client.get(_page)
            self.assertEqual(_reponse.status_code, 200)
            self.assertIn('class="pied-de-page"', _reponse.text)
            self.assertIn("/static/logo-primaire.png", _reponse.text)
        _logo = self._client.get("/static/logo-primaire.png")
        self.assertEqual(_logo.status_code, 200)

    def test_polices_substitution_avec_replis(self) -> None:
        """Titres en substitut Laviossa (Fraunces), texte en substitut Roundo
        (Red Hat Display), avec replis système."""
        _reponse = self._client.get("/")
        self.assertIn("Fraunces", _reponse.text)
        self.assertIn("Red Hat Display", _reponse.text)
        self.assertIn("Georgia", _reponse.text)
        self.assertIn("system-ui", _reponse.text)

    def test_motif_papier_millimetre(self) -> None:
        """Le fond comporte le quadrillage subtil de la charte."""
        _reponse = self._client.get("/")
        self.assertIn("background-image", _reponse.text)
        self.assertIn("rgba(135, 150, 117, .07)", _reponse.text)


class TestPeriodeParDefaut(unittest.TestCase):
    """Tests de la fonction _periode_par_defaut (12 mois glissants)."""

    def test_milieu_annee(self) -> None:
        """15 novembre 2026 → décembre 2025 à novembre 2026."""
        self.assertEqual(_periode_par_defaut(date(2026, 11, 15)), (2025, 12, 2026, 11))

    def test_janvier_passage_annee(self) -> None:
        """10 janvier 2026 → février 2025 à janvier 2026."""
        self.assertEqual(_periode_par_defaut(date(2026, 1, 10)), (2025, 2, 2026, 1))

    def test_decembre(self) -> None:
        """31 décembre 2026 → janvier 2026 à décembre 2026 (12 mois même année)."""
        self.assertEqual(_periode_par_defaut(date(2026, 12, 31)), (2026, 1, 2026, 12))

    def test_premier_du_mois(self) -> None:
        """1er février 2026 → mars 2025 à février 2026."""
        self.assertEqual(_periode_par_defaut(date(2026, 2, 1)), (2025, 3, 2026, 2))

    def test_annee_bissextile(self) -> None:
        """Février 2028 (bissextile) → mars 2027 à février 2028."""
        self.assertEqual(_periode_par_defaut(date(2028, 2, 29)), (2027, 3, 2028, 2))


class TestBornesAnneesMois(unittest.TestCase):
    """Bornes min/max pour « Toutes les années » / « Tous les mois ».

    Valeurs témoins : événements en juin 2024, décembre 2025 et janvier 2026
    → bornes ((2024, 6), (2026, 1)). Avec les 4 paramètres de période présents
    mais vides dans l'URL, la page KPI doit couvrir toute cette plage (et non
    retomber sur les 12 mois glissants).
    """

    def setUp(self) -> None:
        """Prépare une base temporaire avec des événements sur 3 périodes."""
        self._dossier = tempfile.TemporaryDirectory()
        self._chemin_base = Path(self._dossier.name) / "test.sqlite3"
        _base = BaseDonnees(self._chemin_base)
        try:
            _referentiels = ReferentielRepository(_base)
            for _table, _valeurs in REFERENTIELS_TEST.items():
                for _valeur in _valeurs:
                    _referentiels.obtenir_ou_creer(_table, _valeur)
            _suivi = SuiviRepository(_base)
            # Juin 2024 : 1 demande
            _suivi.ajouter(EvenementSuivi(
                date=date(2024, 6, 10), personne="Alice",
                statut_contact="prospect",
                action_public="Demande", canal="mail",
            ))
            # Décembre 2025 : 1 demande, 1 réponse
            _suivi.ajouter(EvenementSuivi(
                date=date(2025, 12, 3), personne="Bob",
                statut_contact="prospect",
                action_public="Demande", canal="mail",
            ))
            _suivi.ajouter(EvenementSuivi(
                date=date(2025, 12, 20), personne="Bob",
                statut_contact="prospect",
                action_public="Réponse", canal="mail",
            ))
            # Janvier 2026 : 1 demande
            _suivi.ajouter(EvenementSuivi(
                date=date(2026, 1, 5), personne="Chloe",
                statut_contact="prospect",
                action_public="Demande", canal="instagram",
            ))
            _base.valider()
        finally:
            _base.fermer()
        self._application = ApplicationWeb(self._chemin_base)
        self._client = TestClient(self._application.application)

    def tearDown(self) -> None:
        """Supprime le dossier temporaire."""
        self._dossier.cleanup()

    def test_bornes_annees_mois_liste_vide(self) -> None:
        """Une liste vide ne produit pas de bornes (None, pas d'erreur)."""
        self.assertIsNone(_bornes_annees_mois([]))

    def test_bornes_annees_mois_min_max(self) -> None:
        """Les couples min et max sont calculés sur (année, mois)."""
        _evenements = [
            EvenementSuivi(date=date(2026, 1, 5), personne="A"),
            EvenementSuivi(date=date(2024, 6, 2), personne="B"),
            EvenementSuivi(date=date(2025, 12, 3), personne="C"),
        ]
        self.assertEqual(
            _bornes_annees_mois(_evenements), ((2024, 6), (2026, 1))
        )

    def test_bornes_periode_resolues_parametres_vides(self) -> None:
        """4 composantes vides → bornes = min/max des événements."""
        _base = BaseDonnees(self._chemin_base)
        try:
            _evenements = SuiviRepository(_base).lister()
        finally:
            _base.fermer()
        _debut, _fin = self._application._bornes_periode_resolues(
            _evenements, "", "", "", ""
        )
        self.assertEqual(_debut, (2024, 6))
        self.assertEqual(_fin, (2026, 1))

    def test_page_kpi_parametres_vides_couvrent_toute_la_plage(self) -> None:
        """4 sélecteurs vides (« Appliquer ») couvrent tout l'historique.

        Le mois le plus ancien (2024/6) et le plus récent (2026/1) doivent
        apparaître : la période par défaut des 12 mois glissants ne doit PAS
        être appliquée quand les paramètres sont présents mais vides.
        """
        _reponse = self._client.get(
            "/kpi?indicateur=TauxGhosting&annee_debut=&mois_debut="
            "&annee_fin=&mois_fin="
        )
        self.assertEqual(_reponse.status_code, 200)
        self.assertIn('"2024/6"', _reponse.text)
        self.assertIn('"2025/12"', _reponse.text)
        self.assertIn('"2026/1"', _reponse.text)

    def test_page_kpi_sans_parametre_applique_les_12_mois(self) -> None:
        """Sans aucun paramètre de période, les 12 mois glissants s'appliquent.

        Les sélecteurs d'année affichent la période par défaut comme
        sélectionnée (non-régression du comportement par défaut).
        """
        _reponse = self._client.get("/kpi?indicateur=TauxGhosting")
        self.assertEqual(_reponse.status_code, 200)
        _a, _m, _af, _mf = _periode_par_defaut()
        self.assertIn(
            f'<option value="{_a}" selected>{_a}</option>', _reponse.text
        )
        self.assertIn(
            f'<option value="{_af}" selected>{_af}</option>', _reponse.text
        )

    def test_page_kpi_un_seul_parametre_pas_de_defaut(self) -> None:
        """Un seul paramètre : pas de défaut, fin = max des données."""
        _reponse = self._client.get(
            "/kpi?indicateur=TauxGhosting&annee_debut=2025"
        )
        self.assertEqual(_reponse.status_code, 200)
        # 2024/6 exclu (avant 2025), 2026/1 inclus (fin = max des données).
        self.assertNotIn('"2024/6"', _reponse.text)
        self.assertIn('"2026/1"', _reponse.text)

    def test_page_ghosting_parametres_vides(self) -> None:
        """La page ghosting applique les mêmes bornes min/max."""
        _reponse = self._client.get(
            "/kpi/TauxGhosting?annee_debut=&mois_debut=&annee_fin=&mois_fin="
        )
        self.assertEqual(_reponse.status_code, 200)
        self.assertIn("2024", _reponse.text)

    def test_base_vide_parametres_vides_aucune_erreur(self) -> None:
        """Base vide + 4 paramètres vides : aucune donnée, sans erreur."""
        _dossier = tempfile.TemporaryDirectory()
        try:
            _chemin = Path(_dossier.name) / "vide.sqlite3"
            _app = ApplicationWeb(_chemin)
            _client = TestClient(_app.application)
            _reponse = _client.get(
                "/kpi?indicateur=TauxGhosting&annee_debut=&mois_debut="
                "&annee_fin=&mois_fin="
            )
            self.assertEqual(_reponse.status_code, 200)
            self.assertIn("Aucune donnée disponible", _reponse.text)
        finally:
            _dossier.cleanup()


class TestLienChangelog(unittest.TestCase):
    """Tests du lien « changements » vers le CHANGELOG publié sur GitHub."""

    def setUp(self) -> None:
        """Prépare une base temporaire et le client de test."""
        self._dossier = tempfile.TemporaryDirectory()
        self._chemin_base = Path(self._dossier.name) / "test.sqlite3"
        _base = BaseDonnees(self._chemin_base)
        try:
            _referentiels = ReferentielRepository(_base)
            for _table, _valeurs in REFERENTIELS_TEST.items():
                for _valeur in _valeurs:
                    _referentiels.obtenir_ou_creer(_table, _valeur)
            _base.valider()
        finally:
            _base.fermer()
        self._application = ApplicationWeb(self._chemin_base)
        self._client = TestClient(self._application.application)

    def tearDown(self) -> None:
        """Supprime le dossier temporaire."""
        self._dossier.cleanup()

    def test_lien_changelog_nouvel_onglet(self) -> None:
        """L'en-tête contient un lien target=_blank vers github.com."""
        _reponse = self._client.get("/")
        self.assertEqual(_reponse.status_code, 200)
        self.assertIn('target="_blank"', _reponse.text)
        self.assertIn("github.com/jeremyplessis/kpi/blob/", _reponse.text)
        self.assertIn("/CHANGELOG.md", _reponse.text)

    def test_lien_changelog_attributs(self) -> None:
        """Le lien porte rel=noopener et le mot « changements »."""
        _reponse = self._client.get("/")
        self.assertIn('rel="noopener"', _reponse.text)
        self.assertIn("changements", _reponse.text)

    def test_url_changelog_branche_courante(self) -> None:
        """L'URL globale contient la branche courante (ou main en repli)."""
        _url = self._application.modeles.env.globals["url_changelog"]
        self.assertTrue(
            _url.endswith("/CHANGELOG.md"),
            f"URL inattendue : {_url}",
        )
        self.assertIn("github.com/jeremyplessis/kpi/blob/", _url)

    def test_branche_courante_repli_main(self) -> None:
        """git indisponible → la branche retournée est « main »."""
        from unittest.mock import patch

        with patch(
            "kpi.web.routes._run_subprocess", side_effect=FileNotFoundError
        ):
            self.assertEqual(self._application._branche_courante(), "main")

    def test_route_changelog_interne_absente(self) -> None:
        """Pas de page interne /changelog : le lien est externe."""
        _reponse = self._client.get("/changelog")
        self.assertEqual(_reponse.status_code, 404)


if __name__ == "__main__":
    unittest.main()
