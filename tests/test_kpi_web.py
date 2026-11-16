"""Tests de l'écran de consultation des KPI."""

import os
import tempfile
import unittest
from datetime import date

from fastapi.testclient import TestClient

from kpi.bdd.connexion import BaseDonnees
from kpi.bdd.modeles import (
    ReferentielRepository,
    SuiviRepository,
)
from kpi.web.routes import ApplicationWeb


class TestEcranKPI(unittest.TestCase):
    """Tests de la page de consultation des KPI."""

    @classmethod
    def setUpClass(cls):
        """Initialise la base de test avec des données."""
        # Utiliser un fichier temporaire au lieu de :memory: pour que
        # les données persistent entre les requêtes
        cls.temp_dir = tempfile.mkdtemp()
        cls.chemin_base = os.path.join(cls.temp_dir, "test_kpi.sqlite3")
        
        _base = BaseDonnees(cls.chemin_base)
        try:
            # Créer les référentiels nécessaires
            _referentiels = ReferentielRepository(_base)
            for _table, _valeurs in {
                "canal": ["formulaire de contact", "instagram", "mail"],
                "statut_contact": ["prospect", "client"],
                "action": ["Demande", "Réservation", "Réponse", "RDV", "Paiement"],
                "prestation": ["Mariage", "Séance"],
                "detail_prestation": ["Famille", "Portrait"],
                "provenance": ["Google", "Instagram"],
            }.items():
                for _valeur in _valeurs:
                    _referentiels.ajouter(_table, _valeur)
            
            # Ajouter des événements de test
            _suivi = SuiviRepository(_base)
            _suivi.ajouter(_evenement(
                date(2026, 1, 15), "Alice Dupont", "prospect", "Demande",
                "formulaire de contact", "Google", "Mariage", "Famille",
                None, None, None
            ))
            _suivi.ajouter(_evenement(
                date(2026, 1, 16), "Bob Martin", "prospect", "Demande",
                "instagram", "Instagram", "Séance", "Portrait",
                None, None, None
            ))
            _suivi.ajouter(_evenement(
                date(2026, 1, 17), "Alice Dupont", "prospect", "Réponse",
                "mail", "Google", "Mariage", "Famille",
                "RDV", "mail", None
            ))
            _suivi.ajouter(_evenement(
                date(2026, 2, 1), "Charlie Brown", "prospect", "Demande",
                "formulaire de contact", "Google", "Mariage", None,
                None, None, None
            ))
            _base.valider()
        finally:
            _base.fermer()
        
        cls.client = TestClient(ApplicationWeb(cls.chemin_base).application)

    @classmethod
    def tearDownClass(cls):
        """Nettoie les fichiers temporaires."""
        import shutil
        if os.path.exists(cls.chemin_base):
            os.remove(cls.chemin_base)
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    @staticmethod
    def _contexte_base() -> BaseDonnees:
        """Ouvre une connexion à la base de test."""
        return BaseDonnees(TestEcranKPI.chemin_base)

    def test_page_kpi_affiche_les_indicateurs(self):
        """La page KPI affiche la liste des indicateurs disponibles."""
        _reponse = self.client.get("/kpi")
        self.assertEqual(_reponse.status_code, 200)
        _texte = _reponse.text
        self.assertIn("Nombre de prospects", _texte)
        self.assertIn("Nombre de demandes", _texte)
        self.assertIn("Taux de ghosting", _texte)
        self.assertIn("RDV par canal", _texte)

    def test_page_kpi_affiche_les_annees_disponibles(self):
        """La page KPI propose les années disponibles dans les filtres."""
        _reponse = self.client.get("/kpi")
        self.assertEqual(_reponse.status_code, 200)
        _texte = _reponse.text
        self.assertIn("2026", _texte)

    def test_kpi_nb_demandes_affiche_les_donnees(self):
        """L'indicateur NbDemandes affiche correctement les données."""
        _reponse = self.client.get("/kpi?indicateur=NbDemandes")
        self.assertEqual(_reponse.status_code, 200)
        _texte = _reponse.text
        # Alice a fait une demande le 15/01, Bob le 16/01, Charlie le 01/02
        # Alice ne compte qu'une fois par mois (dédoublonnage)
        self.assertIn("Nombre de demandes", _texte)
        self.assertIn("2026", _texte)

    def test_kpi_nb_prospects_affiche_les_donnees(self):
        """L'indicateur NbProspects affiche correctement les données."""
        _reponse = self.client.get("/kpi?indicateur=NbProspects")
        self.assertEqual(_reponse.status_code, 200)
        _texte = _reponse.text
        self.assertIn("Nombre de prospects", _texte)

    def test_kpi_taux_ghosting_affiche_les_donnees(self):
        """L'indicateur TauxGhosting affiche correctement les données."""
        _reponse = self.client.get("/kpi?indicateur=TauxGhosting")
        self.assertEqual(_reponse.status_code, 200)
        _texte = _reponse.text
        self.assertIn("Taux de ghosting", _texte)
        # En janvier 2026 : 2 demandes (Alice, Bob), 1 réponse (Alice)
        # Taux = (2-1)/2 = 50%
        self.assertIn("50", _texte) or self.assertIn("0.5", _texte)

    def test_kpi_rdv_par_canal_affiche_les_donnees(self):
        """L'indicateur RdvParCanal affiche correctement les données."""
        _reponse = self.client.get("/kpi?indicateur=RdvParCanal")
        self.assertEqual(_reponse.status_code, 200)
        _texte = _reponse.text
        self.assertIn("RDV par canal", _texte)

    def test_page_ghosting_detail_affiche_les_donnees(self):
        """La page dédiée au ghosting affiche le détail."""
        _reponse = self.client.get("/kpi/TauxGhosting")
        self.assertEqual(_reponse.status_code, 200)
        _texte = _reponse.text
        self.assertIn("Taux de ghosting — Détail mensuel", _texte)
        self.assertIn("Demandes", _texte)
        self.assertIn("Réponses", _texte)

    def test_filtre_par_annee(self):
        """Le filtrage par année fonctionne correctement."""
        _reponse = self.client.get(
            "/kpi?indicateur=NbDemandes&annee_debut=2026&annee_fin=2026"
        )
        self.assertEqual(_reponse.status_code, 200)
        _texte = _reponse.text
        self.assertIn("2026", _texte)

    def test_filtre_par_mois(self):
        """Le filtrage par mois fonctionne correctement."""
        _reponse = self.client.get(
            "/kpi?indicateur=NbDemandes&annee_debut=2026&mois_debut=1"
            "&annee_fin=2026&mois_fin=1"
        )
        self.assertEqual(_reponse.status_code, 200)

    def test_filtre_ghosting_par_annee(self):
        """Le filtrage du ghosting par année fonctionne."""
        _reponse = self.client.get(
            "/kpi/TauxGhosting?annee_debut=2026&annee_fin=2026"
        )
        self.assertEqual(_reponse.status_code, 200)
        _texte = _reponse.text
        self.assertIn("2026", _texte)

    def test_redirection_vers_kpi_avec_indicateur(self):
        """Les autres indicateurs redirigent vers /kpi avec l'indicateur."""
        _reponse = self.client.get("/kpi/NbDemandes", follow_redirects=False)
        self.assertEqual(_reponse.status_code, 303)
        self.assertTrue(
            _reponse.headers.get("location", "").endswith("/kpi?indicateur=NbDemandes")
        )

    def test_tableau_bord_affiche_cartes(self):
        """La page /kpi sans indicateur affiche les 4 cartes du tableau de bord."""
        _reponse = self.client.get("/kpi")
        self.assertEqual(_reponse.status_code, 200)
        _texte = _reponse.text
        self.assertIn("Nombre de prospects", _texte)
        self.assertIn("Nombre de demandes", _texte)
        self.assertIn("Taux de ghosting", _texte)
        self.assertIn("RDV par canal", _texte)
        # Les sparklines sont présents pour les indicateurs multi-mois
        self.assertIn("spark-NbProspects", _texte)
        self.assertIn("spark-NbDemandes", _texte)
        self.assertIn("spark-TauxGhosting", _texte)

    def test_tableau_bord_totaux(self):
        """Les totaux des cartes correspondent aux données de test.

        Jeu : Alice (demande 15/01, réponse 17/01, RDV), Bob (demande
        16/01), Charlie (demande 01/02). Totaux : prospects 3, demandes 3,
        ghosting 75%, RDV 1. Les sparklines embarquent les séries mensuelles.
        """
        _reponse = self.client.get("/kpi")
        self.assertEqual(_reponse.status_code, 200)
        _texte = _reponse.text
        # Taux de ghosting moyen affiché en pourcentage
        self.assertIn("75.0 %", _texte)
        # Séries mensuelles dans les sparklines : NbProspects = [3.0, 1.0]
        self.assertIn("[3.0, 1.0]", _texte)
        # NbDemandes = [2.0, 1.0]
        self.assertIn("[2.0, 1.0]", _texte)

    def test_tableau_bord_filtre_periode(self):
        """Les filtres de période s'appliquent au tableau de bord."""
        _reponse = self.client.get(
            "/kpi?annee_debut=2026&mois_debut=1&annee_fin=2026&mois_fin=1"
        )
        self.assertEqual(_reponse.status_code, 200)
        _texte = _reponse.text
        # Janvier seul : ghosting 50% (2 demandes, 1 réponse)
        self.assertIn("50.0 %", _texte)

    def test_carte_cliquable(self):
        """Chaque carte contient un lien vers l'indicateur avec filtres conservés."""
        _reponse = self.client.get(
            "/kpi?annee_debut=2026&mois_debut=1&annee_fin=2026&mois_fin=2"
        )
        self.assertEqual(_reponse.status_code, 200)
        _texte = _reponse.text
        self.assertIn("indicateur=TauxGhosting", _texte)
        self.assertIn("annee_debut=2026", _texte)

    def test_coherence_total_detail(self):
        """Le total de la carte égale la somme du tableau détaillé."""
        _reponse = self.client.get("/kpi")
        self.assertEqual(_reponse.status_code, 200)
        _reponse_detail = self.client.get("/kpi?indicateur=NbDemandes")
        self.assertEqual(_reponse_detail.status_code, 200)
        # La série NbDemandes dans le tableau de bord = [2.0, 1.0] (total 3)
        # et le détail affiche aussi 3 demandes au total
        self.assertIn("[2.0, 1.0]", _reponse.text)
        self.assertIn(">3<", _reponse_detail.text)


def _evenement(
    _date: date,
    _personne: str,
    _statut: str | None,
    _action_public: str | None,
    _canal: str | None,
    _provenance: str | None,
    _prestation: str | None,
    _detail: str | None,
    _action_photographe: str | None,
    _canal2: str | None,
    _commentaire: str | None,
):
    """Fabrique un événement de test."""
    from kpi.suivi import EvenementSuivi
    return EvenementSuivi(
        date=_date,
        personne=_personne,
        statut_contact=_statut,
        action_public=_action_public,
        canal=_canal,
        provenance=_provenance,
        prestation=_prestation,
        detail_prestation=_detail,
        action_photographe=_action_photographe,
        canal2=_canal2,
        commentaire=_commentaire,
    )


if __name__ == "__main__":
    unittest.main()
