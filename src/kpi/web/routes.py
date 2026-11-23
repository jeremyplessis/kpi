"""Écran web local de saisie du suivi d'activité.

L'application n'écoute que sur ``127.0.0.1`` (usage personnel, sans
authentification) et les écritures sont refusées si elles proviennent d'un
autre site (contrôle de l'en-tête ``Origin``).

Chaque requête ouvre sa propre connexion SQLite puis la referme : le
serveur peut ainsi traiter plusieurs requêtes successives sans conflit,
et chaque écriture est validée (ou annulée) dans la foulée, avant la
redirection.
"""

from datetime import date
from pathlib import Path
from urllib.parse import quote, urlencode

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from kpi import __version__
from kpi.bdd.connexion import BaseDonnees
from kpi.bdd.modeles import (
    PersonneRepository,
    ReferentielRepository,
    SuiviRepository,
)
from kpi.kpi.indicateurs import (
    LigneGhosting,
    REGISTRE_INDICATEURS,
    TauxGhosting,
)
from kpi.suivi import EvenementSuivi

#: Tables de référence proposées dans les listes déroulantes du formulaire.
TABLES_FORMULAIRE = (
    "statut_contact",
    "prestation",
    "detail_prestation",
    "action",
    "canal",
    "provenance",
)

#: Champs attendus dans le formulaire de saisie.
CHAMPS_FORMULAIRE = (
    "date",
    "personne",
    "statut_contact",
    "action_public",
    "canal",
    "provenance",
    "prestation",
    "detail_prestation",
    "action_photographe",
    "canal2",
    "commentaire",
)

#: Colonnes triables de la liste des événements (clé -> attribut lu).
COLONNES_TRI = (
    "date",
    "personne",
    "statut_contact",
    "action_public",
    "canal",
    "action_photographe",
    "commentaire",
)

#: Filtres de la liste des événements (paramètre d'URL -> attribut lu).
FILTRES_LISTE = (
    ("filtre_personne", "personne"),
    ("filtre_statut", "statut_contact"),
    ("filtre_action", "action_public"),
    ("filtre_canal", "canal"),
    ("filtre_photographe", "action_photographe"),
    ("filtre_commentaire", "commentaire"),
)

#: Nombre d'événements affichés par page dans la liste.
EVENEMENTS_PAR_PAGE = 10

#: Libellés conviviaux des listes sur la page de paramétrage.
LIBELLES_LISTES = {
    "statut_contact": "Statut du contact",
    "prestation": "Prestations",
    "detail_prestation": "Détails de prestation",
    "action": "Actions (contact et photographe)",
    "canal": "Canaux",
    "provenance": "Provenances",
}


def formater_date_fr(_valeur: date | None) -> str:
    """Formate une date en français court (jj/mm/aaaa), vide si absente."""
    if _valeur is None:
        return ""
    return f"{_valeur.day:02d}/{_valeur.month:02d}/{_valeur.year}"


class ApplicationWeb:
    """Application web locale de saisie et de consultation du suivi.

    :param _chemin_base: chemin du fichier SQLite, partagé avec l'outil
        d'import (même fichier, même dossier de lancement).
    """

    def __init__(self, _chemin_base: str | Path = "kpi.sqlite3") -> None:
        """Prépare le serveur, les gabarits et les routes."""
        self.chemin_base = Path(_chemin_base)
        _dossier_gabarits = Path(__file__).parent / "gabarits"
        self.modeles = Jinja2Templates(directory=str(_dossier_gabarits))
        self.modeles.env.filters["date_fr"] = formater_date_fr
        self.modeles.env.globals["version"] = __version__
        self.application = FastAPI(title="Suivi d'activité")
        _dossier_statique = Path(__file__).parent / "static"
        self.application.mount(
            "/static", StaticFiles(directory=str(_dossier_statique)), name="static"
        )
        self._configurer_routes()

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    def _configurer_routes(self) -> None:
        """Déclare les pages de l'application."""
        _app = self.application
        _app.get("/")(self.page_saisie)
        _app.post("/evenements")(self.enregistrer_evenement)
        _app.get("/evenements/{_identifiant}/modifier")(self.page_modifier)
        _app.post("/evenements/{_identifiant}/modifier")(self.modifier_evenement)
        _app.get("/evenements/{_identifiant}/supprimer")(self.page_supprimer)
        _app.post("/evenements/{_identifiant}/supprimer")(self.supprimer_evenement)
        _app.get("/listes")(self.page_listes)
        _app.post("/listes/ajouter")(self.ajouter_valeur_liste)
        _app.post("/listes/renommer")(self.renommer_valeur_liste)
        _app.post("/listes/retirer")(self.retirer_valeur_liste)
        # Routes pour la consultation des KPI
        _app.get("/kpi")(self.page_kpi)
        _app.get("/kpi/{_indicateur}")(self.page_kpi_indicateur)

    def _ouvrir_base(self) -> BaseDonnees:
        """Ouvre une connexion vers la base (le schéma est créé au besoin)."""
        return BaseDonnees(self.chemin_base)

    # ------------------------------------------------------------------
    # Page de saisie
    # ------------------------------------------------------------------

    def page_saisie(self, _requete: Request):
        """Affiche le formulaire de saisie et les derniers événements.

        Après un enregistrement, la personne reste préremplie pour enchaîner
        la saisie du même dossier, et un message le rappelle clairement.
        """
        # Les paramètres d'URL sont lus depuis la requête : la convention du
        # projet (variables locales préfixées par « _ ») ne se marie pas avec
        # les noms de paramètres FastAPI.
        _personne = _requete.query_params.get("personne", "")
        _enregistre = _requete.query_params.get("enregistre", "") == "1"
        _base = self._ouvrir_base()
        try:
            _contexte = self._contexte_page(_requete)
            _contexte["valeurs"] = {
                "date": date.today().isoformat(),
                "personne": _personne,
            }
            _contexte["message_enregistrement"] = _enregistre
        finally:
            _base.fermer()
        return self.modeles.TemplateResponse(_requete, "saisie.html", _contexte)

    async def enregistrer_evenement(self, _requete: Request):
        """Enregistre un nouvel événement saisi dans le formulaire.

        En cas d'erreur (date invalide, personne vide), le formulaire est
        réaffiché avec toutes les valeurs saisies et un message à côté du
        champ concerné : rien n'est perdu.
        """
        self._verifier_origine(_requete)
        _valeurs = self._lire_formulaire(await _requete.form())
        _erreurs = self._verifier_saisie(_valeurs)
        if _erreurs:
            return self._reafficher_formulaire(_requete, _valeurs, _erreurs)

        _evenement = self._construire_evenement(_valeurs)
        _base = self._ouvrir_base()
        try:
            SuiviRepository(_base).ajouter(_evenement)
            # L'événement est durablement enregistré avant la redirection :
            # un simple rafraîchissement de la page ne peut pas le dupliquer.
            _base.valider()
        except Exception:
            _base.annuler()
            raise
        finally:
            _base.fermer()
        return self._rediriger_vers_saisie(_evenement.personne)

    # ------------------------------------------------------------------
    # Modification
    # ------------------------------------------------------------------

    def page_modifier(self, _requete: Request, _identifiant: int):
        """Affiche le formulaire prérempli pour corriger un événement."""
        _base = self._ouvrir_base()
        try:
            _evenement = SuiviRepository(_base).obtenir(_identifiant)
            if _evenement is None:
                raise HTTPException(status_code=404, detail="Événement inconnu")
            _contexte = self._contexte_page(_requete)
            _contexte["valeurs"] = self._valeurs_depuis_evenement(_evenement)
            _contexte["identifiant"] = _identifiant
            # La modification exige toujours le formulaire visible.
            _contexte["afficher_formulaire"] = True
        finally:
            _base.fermer()
        return self.modeles.TemplateResponse(_requete, "saisie.html", _contexte)

    async def modifier_evenement(
        self, _requete: Request, _identifiant: int
    ):
        """Enregistre la correction d'un événement existant.

        L'identifiant ne change pas : la correction ne crée pas de nouvel
        événement. Un identifiant inconnu est refusé (404).
        """
        self._verifier_origine(_requete)
        _valeurs = self._lire_formulaire(await _requete.form())
        _erreurs = self._verifier_saisie(_valeurs)
        if _erreurs:
            return self._reafficher_formulaire(
                _requete, _valeurs, _erreurs, _identifiant=_identifiant
            )

        _base = self._ouvrir_base()
        try:
            if SuiviRepository(_base).obtenir(_identifiant) is None:
                raise HTTPException(status_code=404, detail="Événement inconnu")
            SuiviRepository(_base).mettre_a_jour(
                _identifiant, self._construire_evenement(_valeurs)
            )
            _base.valider()
        except HTTPException:
            raise
        except Exception:
            _base.annuler()
            raise
        finally:
            _base.fermer()
        return self._rediriger_vers_saisie(_valeurs["personne"].strip())

    # ------------------------------------------------------------------
    # Suppression (avec confirmation explicite)
    # ------------------------------------------------------------------

    def page_supprimer(self, _requete: Request, _identifiant: int):
        """Affiche une page de confirmation avant toute suppression.

        La page rappelle la date et la personne concernées : la suppression
        ne se fait jamais en un clic depuis la liste.
        """
        _base = self._ouvrir_base()
        try:
            _evenement = SuiviRepository(_base).obtenir(_identifiant)
            if _evenement is None:
                raise HTTPException(status_code=404, detail="Événement inconnu")
        finally:
            _base.fermer()
        return self.modeles.TemplateResponse(
            _requete,
            "confirmation_suppression.html",
            {"requete": _requete, "evenement": _evenement, "identifiant": _identifiant},
        )

    async def supprimer_evenement(self, _requete: Request, _identifiant: int):
        """Supprime définitivement un événement, après confirmation."""
        self._verifier_origine(_requete)
        _base = self._ouvrir_base()
        try:
            SuiviRepository(_base).supprimer(_identifiant)
            _base.valider()
        except ValueError as _erreur:
            raise HTTPException(status_code=404, detail=str(_erreur)) from _erreur
        except Exception:
            _base.annuler()
            raise
        finally:
            _base.fermer()
        return RedirectResponse("/", status_code=303)

    # ------------------------------------------------------------------
    # Paramétrage des listes déroulantes
    # ------------------------------------------------------------------

    def page_listes(self, _requete: Request):
        """Affiche les valeurs de chaque liste, avec leur gestion.

        Chaque valeur indique combien d'événements l'utilisent : retirer
        une valeur utilisée est possible (les événements conservent leur
        contenu), l'utilisatrice est simplement informée.
        """
        _message = _requete.query_params.get("message", "")
        _base = self._ouvrir_base()
        try:
            _referentiels = ReferentielRepository(_base)
            _listes = []
            for _table in TABLES_FORMULAIRE:
                _valeurs = [
                    {
                        "nom": _valeur,
                        "utilisation": _referentiels.compter_utilisation(
                            _table, _valeur
                        ),
                    }
                    for _valeur in _referentiels.lister(_table)
                ]
                _listes.append(
                    {
                        "cle": _table,
                        "libelle": LIBELLES_LISTES[_table],
                        "valeurs": _valeurs,
                    }
                )
        finally:
            _base.fermer()
        return self.modeles.TemplateResponse(
            _requete,
            "listes.html",
            {"requete": _requete, "listes": _listes, "message": _message},
        )

    async def ajouter_valeur_liste(self, _requete: Request):
        """Ajoute une valeur à une liste déroulante."""
        self._verifier_origine(_requete)
        _formulaire = await _requete.form()
        _table, _valeur, _message = self._lire_demande_liste(_formulaire)
        if _message:
            return self._rediriger_vers_listes(_message)
        if not _valeur.strip():
            return self._rediriger_vers_listes(
                "La valeur à ajouter ne peut pas être vide."
            )
        _base = self._ouvrir_base()
        try:
            _referentiels = ReferentielRepository(_base)
            _cree = _referentiels.ajouter(_table, _valeur.strip())
            _base.valider()
        except Exception:
            _base.annuler()
            raise
        finally:
            _base.fermer()
        return self._rediriger_vers_listes(
            f"« {_valeur.strip()} » ajouté à la liste {_table}."
            if _cree
            else f"« {_valeur.strip()} » était déjà dans la liste {_table}."
        )

    async def renommer_valeur_liste(self, _requete: Request):
        """Renomme une valeur : les événements existants suivent le changement."""
        self._verifier_origine(_requete)
        _formulaire = await _requete.form()
        _table, _ancienne, _message = self._lire_demande_liste(
            _formulaire, champ_valeur="ancienne"
        )
        if _message:
            return self._rediriger_vers_listes(_message)
        _nouvelle = str(_formulaire.get("nouvelle") or "").strip()
        if not _ancienne.strip() or not _nouvelle:
            return self._rediriger_vers_listes(
                "Le renommage exige l'ancien et le nouveau nom."
            )
        _base = self._ouvrir_base()
        try:
            _referentiels = ReferentielRepository(_base)
            _renomme = _referentiels.renommer(
                _table, _ancienne.strip(), _nouvelle
            )
            _base.valider()
        except Exception:
            _base.annuler()
            raise
        finally:
            _base.fermer()
        if _renomme:
            return self._rediriger_vers_listes(
                f"« {_ancienne.strip()} » renommé en « {_nouvelle} »."
            )
        return self._rediriger_vers_listes(
            f"Impossible de renommer « {_ancienne.strip()} » : "
            "valeur introuvable ou nouveau nom déjà pris."
        )

    async def retirer_valeur_liste(self, _requete: Request):
        """Retire une valeur des listes, sans modifier les événements."""
        self._verifier_origine(_requete)
        _formulaire = await _requete.form()
        _table, _valeur, _message = self._lire_demande_liste(
            _formulaire, champ_valeur="ancienne"
        )
        if _message:
            return self._rediriger_vers_listes(_message)
        if not _valeur.strip():
            return self._rediriger_vers_listes(
                "La valeur à retirer ne peut pas être vide."
            )
        _base = self._ouvrir_base()
        try:
            _referentiels = ReferentielRepository(_base)
            _utilisations = _referentiels.compter_utilisation(
                _table, _valeur.strip()
            )
            _retire = _referentiels.retirer(_table, _valeur.strip())
            _base.valider()
        except Exception:
            _base.annuler()
            raise
        finally:
            _base.fermer()
        if not _retire:
            return self._rediriger_vers_listes(
                f"« {_valeur.strip()} » n'est pas dans la liste {_table}."
            )
        _message = f"« {_valeur.strip()} » retiré de la liste {_table}."
        if _utilisations:
            _message += (
                f" {_utilisations} événement(s) l'utilisent encore "
                "et conservent cette valeur."
            )
        return self._rediriger_vers_listes(_message)

    # ------------------------------------------------------------------
    # Pages KPI
    # ------------------------------------------------------------------

    def page_kpi(self, _requete: Request):
        """Affiche la page de consultation des KPI avec filtres."""
        _base = self._ouvrir_base()
        try:
            _evenements = SuiviRepository(_base).lister()
            _annees = self._obtenir_annees(_evenements)
            
            # Lire les paramètres de filtrage
            _indicateur_nom = _requete.query_params.get("indicateur", "")
            _annee_debut = _requete.query_params.get("annee_debut", "")
            _mois_debut = _requete.query_params.get("mois_debut", "")
            _annee_fin = _requete.query_params.get("annee_fin", "")
            _mois_fin = _requete.query_params.get("mois_fin", "")
            
            # Filtrer les événements selon la période
            _evenements_filtres = self._filtrer_par_periode(
                _evenements, _annee_debut, _mois_debut, _annee_fin, _mois_fin
            )
            
            # Trouver l'indicateur sélectionné
            _indicateur_classe = None
            _lignes_indicateur = []
            _indicateur_libelle = ""
            _indicateur_description = ""
            _indicateur_dimensions = []
            
            if _indicateur_nom:
                for _indic_classe in REGISTRE_INDICATEURS:
                    if _indic_classe.__name__ == _indicateur_nom:
                        _indicateur_classe = _indic_classe
                        _indicateur = _indic_classe()
                        # Les indicateurs avec calculer_periode ont besoin
                        # de tous les événements + les bornes de la période.
                        if hasattr(_indicateur, "calculer_periode"):
                            _a_d = int(_annee_debut) if _annee_debut else None
                            _m_d = int(_mois_debut) if _mois_debut else None
                            _a_f = int(_annee_fin) if _annee_fin else None
                            _m_f = int(_mois_fin) if _mois_fin else None
                            _debut = (_a_d, _m_d) if _a_d else None
                            _fin = (_a_f, _m_f) if _a_f else None
                            _lignes_indicateur = _indicateur.calculer_periode(
                                _evenements, _debut, _fin
                            )
                        else:
                            _lignes_indicateur = _indicateur.calculer(
                                _evenements_filtres
                            )
                        _indicateur_libelle = _indic_classe.libelle
                        _indicateur_description = _indic_classe.description
                        _indicateur_dimensions = list(_indic_classe.dimensions)
                        break
            
            # Tableau de bord : synthèses de tous les indicateurs quand
            # aucun n'est sélectionné.
            _tableau_de_bord = []
            if not _indicateur_nom:
                _tableau_de_bord = self._construire_tableau_de_bord(
                    _evenements,
                    _annee_debut, _mois_debut, _annee_fin, _mois_fin,
                )
            
            _contexte = {
                "requete": _requete,
                "indicateurs_disponibles": [
                    {"nom": _indic.__name__, "libelle": _indic.libelle}
                    for _indic in REGISTRE_INDICATEURS
                ],
                "annees_disponibles": sorted(_annees),
                "indicateur_selectionne": _indicateur_nom,
                "annee_debut": _annee_debut,
                "mois_debut": _mois_debut,
                "annee_fin": _annee_fin,
                "mois_fin": _mois_fin,
                "lignes_indicateur": _lignes_indicateur,
                "indicateur_libelle": _indicateur_libelle,
                "indicateur_description": _indicateur_description,
                "indicateur_dimensions": _indicateur_dimensions,
                "tableau_de_bord": _tableau_de_bord,
            }
        finally:
            _base.fermer()
        
        return self.modeles.TemplateResponse(_requete, "kpi.html", _contexte)

    def page_kpi_indicateur(self, _requete: Request, _indicateur: str):
        """Affiche une page dédiée pour un indicateur spécifique.
        
        Actuellement, seul le TauxGhosting a une page dédiée avec détail.
        """
        if _indicateur == "TauxGhosting":
            return self._page_ghosting_detail(_requete)
        
        # Pour les autres indicateurs, rediriger vers la page principale
        # avec l'indicateur présélectionné
        _params = dict(_requete.query_params)
        _params["indicateur"] = _indicateur
        return RedirectResponse(
            "/kpi?" + urlencode(_params), status_code=303
        )

    def _page_ghosting_detail(self, _requete: Request):
        """Affiche le détail du taux de ghosting avec demandes/réponses."""
        _base = self._ouvrir_base()
        try:
            _evenements = SuiviRepository(_base).lister()
            _annees = self._obtenir_annees(_evenements)
            
            # Lire les paramètres de filtrage
            _annee_debut = _requete.query_params.get("annee_debut", "")
            _mois_debut = _requete.query_params.get("mois_debut", "")
            _annee_fin = _requete.query_params.get("annee_fin", "")
            _mois_fin = _requete.query_params.get("mois_fin", "")
            
            # Filtrer les événements selon la période
            _evenements_filtres = self._filtrer_par_periode(
                _evenements, _annee_debut, _mois_debut, _annee_fin, _mois_fin
            )
            
            # Calculer le détail du ghosting
            _indicateur = TauxGhosting()
            _detail_ghosting = _indicateur.calculer_detail(_evenements_filtres)
            
            _contexte = {
                "requete": _requete,
                "annees_disponibles": sorted(_annees),
                "annee_debut": _annee_debut,
                "mois_debut": _mois_debut,
                "annee_fin": _annee_fin,
                "mois_fin": _mois_fin,
                "detail_ghosting": _detail_ghosting,
            }
        finally:
            _base.fermer()
        
        return self.modeles.TemplateResponse(
            _requete, "kpi_ghosting.html", _contexte
        )

    def _obtenir_annees(self, _evenements: list[EvenementSuivi]) -> set[int]:
        """Retourne l'ensemble des années présentes dans les événements."""
        return {_ev.annee for _ev in _evenements}

    def _filtrer_par_periode(
        self,
        _evenements: list[EvenementSuivi],
        _annee_debut: str,
        _mois_debut: str,
        _annee_fin: str,
        _mois_fin: str,
    ) -> list[EvenementSuivi]:
        """Filtre les événements selon une période.
        
        :param _annee_debut: Année de début (vide = pas de filtre)
        :param _mois_debut: Mois de début (vide = pas de filtre)
        :param _annee_fin: Année de fin (vide = pas de filtre)
        :param _mois_fin: Mois de fin (vide = pas de filtre)
        :returns: Liste filtrée des événements
        """
        _resultat = _evenements
        
        # Convertir les paramètres en entiers
        _a_debut = int(_annee_debut) if _annee_debut else None
        _m_debut = int(_mois_debut) if _mois_debut else None
        _a_fin = int(_annee_fin) if _annee_fin else None
        _m_fin = int(_mois_fin) if _mois_fin else None
        
        # Si aucune date de début n'est spécifiée, on prend la plus ancienne
        if _a_debut is None and _m_debut is None:
            _a_debut = min((_ev.annee for _ev in _resultat), default=None)
            if _a_debut is not None:
                _m_debut = 1
        
        # Si aucune date de fin n'est spécifiée, on prend la plus récente
        if _a_fin is None and _m_fin is None:
            _a_fin = max((_ev.annee for _ev in _resultat), default=None)
            if _a_fin is not None:
                _m_fin = 12
        
        # Filtrer
        if _a_debut is not None:
            _resultat = [
                _ev for _ev in _resultat
                if (_ev.annee > _a_debut) or (
                    _ev.annee == _a_debut and _ev.mois >= (_m_debut or 1)
                )
            ]
        
        if _a_fin is not None:
            _resultat = [
                _ev for _ev in _resultat
                if (_ev.annee < _a_fin) or (
                    _ev.annee == _a_fin and _ev.mois <= (_m_fin or 12)
                )
            ]
        
        return _resultat

    def _construire_tableau_de_bord(
        self,
        _tous_evenements: list[EvenementSuivi],
        _annee_debut: str,
        _mois_debut: str,
        _annee_fin: str,
        _mois_fin: str,
    ) -> list[dict]:
        """Construit les cartes de synthèse du tableau de bord.

        Pour chaque indicateur du registre, calcule le total sur la
        période filtrée et la série mensuelle pour le sparkline.

        :param _tous_evenements: tous les événements (pas filtrés), pour
            permettre aux indicateurs de conversion de voir les demandes
            antérieures.
        :returns: liste de dicts avec nom, libelle, total, pourcentage,
            serie (liste de [label, valeur]) et lien vers le détail.
        """
        _cartes = []
        _params_filtres = {
            _k: _v
            for _k, _v in {
                "annee_debut": _annee_debut,
                "mois_debut": _mois_debut,
                "annee_fin": _annee_fin,
                "mois_fin": _mois_fin,
            }.items()
            if _v
        }
        # Bornes de période pour les indicateurs avec calculer_periode
        _a_d = int(_annee_debut) if _annee_debut else None
        _m_d = int(_mois_debut) if _mois_debut else None
        _a_f = int(_annee_fin) if _annee_fin else None
        _m_f = int(_mois_fin) if _mois_fin else None
        _debut = (_a_d, _m_d) if _a_d else None
        _fin = (_a_f, _m_f) if _a_f else None
        # Événements filtrés pour les indicateurs classiques
        _evenements_filtres = self._filtrer_par_periode(
            _tous_evenements, _annee_debut, _mois_debut, _annee_fin, _mois_fin
        )
        for _classe in REGISTRE_INDICATEURS:
            _indicateur = _classe()
            if hasattr(_indicateur, "calculer_periode"):
                _lignes = _indicateur.calculer_periode(
                    _tous_evenements, _debut, _fin
                )
            else:
                _lignes = _indicateur.calculer(_evenements_filtres)
            _est_pourcentage = _classe.__name__ in ("TauxGhosting", "TauxConversion")
            # Total : somme des lignes « Tous » (indicateurs conversions),
            # sinon moyenne pour les %, sinon somme de toutes les lignes.
            _lignes_tous = [
                _l for _l in _lignes if _l.dimensions[0] == "Tous"
            ]
            if _lignes_tous:
                if _est_pourcentage:
                    # Taux : moyenne pondérée = somme conf / somme demandeurs,
                    # mais on n'a que les taux par canal ; on fait la moyenne simple
                    # des taux canal (approximation acceptable pour la carte).
                    _total = sum(_l.valeur for _l in _lignes_tous) / len(_lignes_tous)
                else:
                    _total = sum(_l.valeur for _l in _lignes_tous)
            elif _est_pourcentage and _lignes:
                _total = sum(_ligne.valeur for _ligne in _lignes) / len(_lignes)
            else:
                _total = sum(_ligne.valeur for _ligne in _lignes)
            
            # Série mensuelle pour le sparkline : regrouper par (année, mois)
            # ou (année, canal) selon les dimensions de l'indicateur.
            _serie: list[tuple[str, float]] = []
            _par_cle: dict[tuple, float] = {}
            for _ligne in _lignes:
                if _ligne.dimensions[0] == "Tous":
                    continue
                _cle = tuple(_ligne.dimensions[:2])
                _par_cle[_cle] = _par_cle.get(_cle, 0.0) + _ligne.valeur
            for _cle in sorted(_par_cle):
                if len(_cle) >= 2 and isinstance(_cle[1], int):
                    _label = f"{_cle[0]}-{_cle[1]:02d}"
                else:
                    _label = " ".join(str(_v) for _v in _cle)
                _serie.append((_label, _par_cle[_cle]))
            
            # Lien vers le détail avec filtres conservés
            _params = dict(_params_filtres)
            _params["indicateur"] = _classe.__name__
            _lien = "/kpi?" + urlencode(_params)
            
            _cartes.append({
                "nom": _classe.__name__,
                "libelle": _classe.libelle,
                "total": _total,
                "pourcentage": _est_pourcentage,
                # TauxGhosting est un ratio 0-1 (×100 pour l'affichage) ;
                # TauxConversion est déjà en pourcentage 0-100.
                "ratio": _classe.__name__ == "TauxGhosting",
                "serie": _serie,
                "lien": _lien,
            })
        return _cartes

    def _lire_demande_liste(
        self, _formulaire, champ_valeur: str = "valeur"
    ) -> tuple[str, str, str]:
        """Lit la table et la valeur d'une demande de gestion de liste.

        :returns: (table, valeur, message d'erreur éventuel). La table
            doit être l'une des listes du formulaire ; sinon la demande
            est refusée avec un message clair.
        """
        _table = str(_formulaire.get("table") or "")
        if _table not in TABLES_FORMULAIRE:
            return "", "", f"Liste inconnue : {_table or '(vide)'}."
        return _table, str(_formulaire.get(champ_valeur) or ""), ""

    def _rediriger_vers_listes(self, _message: str) -> RedirectResponse:
        """Redirige vers la page des listes, avec un message affiché."""
        return RedirectResponse(
            f"/listes?message={quote(_message)}", status_code=303
        )

    # ------------------------------------------------------------------
    # Aides communes
    # ------------------------------------------------------------------

    def _contexte_page(self, _requete: Request) -> dict:
        """Construit le contexte commun (référentiels, personnes, événements).

        La liste des événements est filtrée puis triée selon les
        paramètres d'URL (``filtre_*``, ``tri``, ``sens``), avec par
        défaut la date d'interaction la plus récente en premier.
        La liste est paginée (30 par page, paramètre ``page``).
        """
        _referentiels = ReferentielRepository(_base := self._ouvrir_base())
        try:
            _tri, _sens, _filtres = self._lire_tri_filtres(_requete)
            _evenements = SuiviRepository(_base).lister()
            _evenements = self._filtrer_evenements(_evenements, _filtres)
            _evenements = self._trier_evenements(_evenements, _tri, _sens)
            _total = len(_evenements)
            _total_pages = max(1, (_total + EVENEMENTS_PAR_PAGE - 1) // EVENEMENTS_PAR_PAGE)
            _page = self._lire_page(_requete, _total_pages)
            _debut = (_page - 1) * EVENEMENTS_PAR_PAGE
            _evenements = _evenements[_debut : _debut + EVENEMENTS_PAR_PAGE]
            _contexte = {
                "requete": _requete,
                "referentiels": {
                    _table: _referentiels.lister(_table)
                    for _table in TABLES_FORMULAIRE
                },
                "personnes": PersonneRepository(_base).lister(),
                # Les événements de la page courante, filtrés et triés.
                "evenements": _evenements,
                "tris": self._urls_tri(_requete, _filtres, _tri, _sens),
                "tri_actif": _tri,
                "sens_actif": _sens,
                "filtres": _filtres,
                "page": _page,
                "total_pages": _total_pages,
                "total_evenements": _total,
                "url_page_precedente": self._url_page(_requete, _page - 1),
                "url_page_suivante": self._url_page(_requete, _page + 1),
                "afficher_formulaire": self._afficher_formulaire(_requete),
                "url_afficher_formulaire": self._url_afficher_formulaire(_requete),
                "url_masquer_formulaire": self._url_masquer_formulaire(_requete),
            }
        finally:
            _base.fermer()
        return _contexte

    def _lire_page(self, _requete: Request, _total_pages: int) -> int:
        """Lit le numéro de page demandé, borné entre 1 et le total."""
        try:
            _page = int(_requete.query_params.get("page", "1") or "1")
        except ValueError:
            _page = 1
        return max(1, min(_page, _total_pages))

    def _afficher_formulaire(self, _requete: Request) -> bool:
        """Le formulaire est visible si le paramètre d'URL est présent."""
        return _requete.query_params.get("afficher_formulaire", "") == "1"

    def _url_afficher_formulaire(self, _requete: Request) -> str:
        """URL du lien « Ajouter » : conserve filtres, tri et page actifs."""
        _params = dict(_requete.query_params)
        _params["afficher_formulaire"] = "1"
        return "/?" + urlencode(_params)

    def _url_masquer_formulaire(self, _requete: Request) -> str:
        """URL du bouton « Fermer » : conserve filtres, tri et page actifs."""
        _params = {
            _k: _v
            for _k, _v in _requete.query_params.items()
            if _k != "afficher_formulaire"
        }
        if not _params:
            return "/"
        return "/?" + urlencode(_params)

    def _url_page(self, _requete: Request, _page: int) -> str:
        """Construit l'URL d'une page de la liste, filtres et tri conservés."""
        _params = dict(_requete.query_params)
        _params["page"] = str(_page)
        return "/?" + urlencode(_params)

    def _lire_tri_filtres(self, _requete: Request) -> tuple[str, str, dict]:
        """Lit le tri et les filtres demandés dans l'URL.

        Sans paramètre, le tri par défaut s'applique : date de
        l'interaction, de la plus récente à la plus ancienne. Une colonne
        inconnue ou un sens inconnu est ignoré au profit de ce défaut.
        """
        _parametres = _requete.query_params
        _tri = _parametres.get("tri", "")
        if _tri not in COLONNES_TRI:
            _tri = "date"
        _sens = _parametres.get("sens", "")
        if _tri == "date" and not _sens:
            _sens = "desc"
        elif _sens not in ("asc", "desc"):
            _sens = "asc"
        _filtres = {
            _champ: _parametres.get(_champ, "").strip()
            for _champ, _ in FILTRES_LISTE
        }
        return _tri, _sens, _filtres

    def _filtrer_evenements(
        self, _evenements: list, _filtres: dict
    ) -> list:
        """Ne garde que les événements qui remplissent tous les filtres.

        La recherche est insensible à la casse et porte sur un extrait du
        texte de la colonne.
        """
        _resultats = _evenements
        for _parametre, _attribut in FILTRES_LISTE:
            _recherche = _filtres.get(_parametre, "").lower()
            if _recherche:
                _resultats = [
                    _evenement
                    for _evenement in _resultats
                    if _recherche in str(
                        getattr(_evenement, _attribut) or ""
                    ).lower()
                ]
        return _resultats

    def _trier_evenements(
        self, _evenements: list, _tri: str, _sens: str
    ) -> list:
        """Trie les événements selon une colonne et un sens.

        Les événements sans valeur pour cette colonne restent en fin de
        liste quel que soit le sens.
        """
        def _valeur(_evenement):
            return getattr(_evenement, _tri) or ""

        _remplis = [
            _evenement
            for _evenement in _evenements
            if getattr(_evenement, _tri)
        ]
        _vides = [
            _evenement
            for _evenement in _evenements
            if not getattr(_evenement, _tri)
        ]
        return sorted(_remplis, key=_valeur, reverse=_sens == "desc") + _vides

    def _urls_tri(
        self, _requete: Request, _filtres: dict, _tri: str, _sens: str
    ) -> dict:
        """Construit, pour chaque colonne, le lien de tri à afficher.

        Cliquer sur la colonne déjà active inverse le sens ; les filtres
        et la personne préremplie sont conservés dans le lien.
        """
        _parametres = {
            _champ: _valeur
            for _champ, _valeur in _requete.query_params.items()
            if _champ.startswith("filtre_") or _champ == "personne"
        }
        _liens: dict[str, str] = {}
        for _colonne in COLONNES_TRI:
            _cible = dict(_parametres)
            _cible["tri"] = _colonne
            if _colonne == _tri:
                # La colonne déjà active propose l'ordre inverse.
                _cible["sens"] = "asc" if _sens == "desc" else "desc"
            else:
                _cible["sens"] = "asc"
            _liens[_colonne] = "/?" + urlencode(_cible)
        return _liens

    def _lire_formulaire(self, _formulaire) -> dict[str, str]:
        """Extrait les champs du formulaire (chaîne vide si absents)."""
        return {
            _champ: str(_formulaire.get(_champ) or "")
            for _champ in CHAMPS_FORMULAIRE
        }

    def _verifier_saisie(self, _valeurs: dict) -> dict[str, str]:
        """Vérifie les champs obligatoires et la validité de la date.

        :returns: dictionnaire champ -> message d'erreur (vide si tout va bien).
        """
        _erreurs: dict[str, str] = {}
        if not _valeurs["personne"].strip():
            _erreurs["personne"] = "Le nom de la personne est obligatoire."
        try:
            date.fromisoformat(_valeurs["date"])
        except ValueError:
            _erreurs["date"] = "La date saisie n'est pas valide (jj/mm/aaaa)."
        return _erreurs

    def _construire_evenement(self, _valeurs: dict) -> EvenementSuivi:
        """Construit l'événement à enregistrer depuis le formulaire.

        Les champs vides deviennent None : la date et la personne sont les
        seuls champs obligatoires.
        """
        return EvenementSuivi(
            date=date.fromisoformat(_valeurs["date"]),
            personne=_valeurs["personne"].strip(),
            statut_contact=_optionnel(_valeurs["statut_contact"]),
            action_public=_optionnel(_valeurs["action_public"]),
            canal=_optionnel(_valeurs["canal"]),
            provenance=_optionnel(_valeurs["provenance"]),
            prestation=_optionnel(_valeurs["prestation"]),
            detail_prestation=_optionnel(_valeurs["detail_prestation"]),
            action_photographe=_optionnel(_valeurs["action_photographe"]),
            canal2=_optionnel(_valeurs["canal2"]),
            commentaire=_optionnel(_valeurs["commentaire"]),
        )

    def _rediriger_vers_saisie(self, _personne: str) -> RedirectResponse:
        """Redirige vers la saisie, la personne restant préremplie.

        Le formulaire reste visible après un enregistrement pour
        enchaîner la saisie du même dossier.
        """
        return RedirectResponse(
            f"/?personne={quote(_personne)}&enregistre=1&afficher_formulaire=1",
            status_code=303,
        )

    def _reafficher_formulaire(
        self,
        _requete: Request,
        _valeurs: dict,
        _erreurs: dict[str, str],
        _identifiant: int | None = None,
    ):
        """Réaffiche le formulaire avec les valeurs saisies et les erreurs."""
        _base = self._ouvrir_base()
        try:
            _contexte = self._contexte_page(_requete)
            _contexte["valeurs"] = _valeurs
            _contexte["erreurs"] = _erreurs
            if _identifiant is not None:
                _contexte["identifiant"] = _identifiant
            # En cas d'erreur, le formulaire reste visible.
            _contexte["afficher_formulaire"] = True
        finally:
            _base.fermer()
        return self.modeles.TemplateResponse(
            _requete, "saisie.html", _contexte, status_code=400
        )

    def _valeurs_depuis_evenement(self, _evenement: EvenementSuivi) -> dict[str, str]:
        """Prépare les valeurs du formulaire à partir d'un événement."""
        return {
            "date": _evenement.date.isoformat(),
            "personne": _evenement.personne,
            "statut_contact": _evenement.statut_contact or "",
            "action_public": _evenement.action_public or "",
            "canal": _evenement.canal or "",
            "provenance": _evenement.provenance or "",
            "prestation": _evenement.prestation or "",
            "detail_prestation": _evenement.detail_prestation or "",
            "action_photographe": _evenement.action_photographe or "",
            "canal2": _evenement.canal2 or "",
            "commentaire": _evenement.commentaire or "",
        }

    def _verifier_origine(self, _requete: Request) -> None:
        """Refuse les écritures venant d'un autre site (protection locale).

        Sans cette vérification, une page web malveillante consultée dans le
        même navigateur pourrait soumettre le formulaire silencieusement.
        """
        _origine = _requete.headers.get("origin")
        if _origine is None:
            return
        _hote = _requete.headers.get("host", "")
        if _origine.rsplit("//", 1)[-1] != _hote:
            raise HTTPException(
                status_code=403,
                detail="Écriture refusée : la requête vient d'un autre site.",
            )


def _optionnel(_valeur: str) -> str | None:
    """Convertit une chaîne de formulaire : vide (ou espaces) -> None."""
    _texte = _valeur.strip()
    return _texte or None
