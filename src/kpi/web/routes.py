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
from urllib.parse import quote

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
    # Aides communes
    # ------------------------------------------------------------------

    def _contexte_page(self, _requete: Request) -> dict:
        """Construit le contexte commun (référentiels, personnes, événements)."""
        _referentiels = ReferentielRepository(_base := self._ouvrir_base())
        try:
            _contexte = {
                "requete": _requete,
                "referentiels": {
                    _table: _referentiels.lister(_table)
                    for _table in TABLES_FORMULAIRE
                },
                "personnes": PersonneRepository(_base).lister(),
                # Les événements les plus récents en premier, limités à 100.
                "evenements": list(reversed(SuiviRepository(_base).lister()))[:100],
            }
        finally:
            _base.fermer()
        return _contexte

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
