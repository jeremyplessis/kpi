"""Tests de l'écran web de saisie du suivi.

Les tests utilisent une base temporaire et des données synthétiques
anonymes. Le client de test suit les redirections comme un navigateur :
un enregistrement réussi aboutit donc à la page de saisie avec message de
confirmation, jamais à un double enregistrement lors du rafraîchissement.
"""

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
from kpi.web.routes import ApplicationWeb  # noqa: E402 - chemin ajusté pour les tests

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
        """La page affiche le formulaire en trois groupes et les référentiels."""
        _reponse = self._client.get("/")
        self.assertEqual(_reponse.status_code, 200)
        self.assertIn("Qui et quand", _reponse.text)
        self.assertIn("La demande", _reponse.text)
        self.assertIn("La réponse de la photographe", _reponse.text)
        self.assertIn("mail", _reponse.text)
        self.assertIn("Un nom absent de la liste sera créé automatiquement", _reponse.text)

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
        _reponse = self._client.get("/")
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
        _reponse = self._client.get("/")
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


if __name__ == "__main__":
    unittest.main()
