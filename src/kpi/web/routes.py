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
from fastapi.templating import Jinja2Templates

from kpi.bdd.connexion import BaseDonnees
from kpi.bdd.modeles import (
    PersonneRepository,
    ReferentielRepository,
    SuiviRepository,
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
        self.application = FastAPI(title="Suivi d'activité")
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
        """
        _referentiels = ReferentielRepository(_base := self._ouvrir_base())
        try:
            _tri, _sens, _filtres = self._lire_tri_filtres(_requete)
            _evenements = SuiviRepository(_base).lister()
            _evenements = self._filtrer_evenements(_evenements, _filtres)
            _evenements = self._trier_evenements(_evenements, _tri, _sens)[:100]
            _contexte = {
                "requete": _requete,
                "referentiels": {
                    _table: _referentiels.lister(_table)
                    for _table in TABLES_FORMULAIRE
                },
                "personnes": PersonneRepository(_base).lister(),
                # Les événements filtrés, triés (date décroissante par
                # défaut), limités aux 100 premiers.
                "evenements": _evenements,
                "tris": self._urls_tri(_requete, _filtres, _tri, _sens),
                "tri_actif": _tri,
                "sens_actif": _sens,
                "filtres": _filtres,
            }
        finally:
            _base.fermer()
        return _contexte

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
        """Redirige vers la saisie, la personne restant préremplie."""
        return RedirectResponse(
            f"/?personne={quote(_personne)}&enregistre=1", status_code=303
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
