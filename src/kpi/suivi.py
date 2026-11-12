"""Modèle métier du suivi d'activité.

Un événement de suivi représente une étape du parcours d'une personne :
demande, réponse, rendez-vous, devis, paiement… Le suivi complet d'une
personne se lit donc comme une chronologie d'événements.
"""

from dataclasses import dataclass
from datetime import date


@dataclass
class EvenementSuivi:
    """Un événement du parcours d'une personne.

    Les champs de référence (canal, prestation…) portent le nom lisible de la
    valeur, tel qu'affiché à l'utilisatrice ; la correspondance avec les
    identifiants en base est assurée par la couche d'accès aux données.
    """

    date: date
    personne: str
    statut_contact: str | None = None
    action_public: str | None = None
    canal: str | None = None
    provenance: str | None = None
    prestation: str | None = None
    detail_prestation: str | None = None
    action_photographe: str | None = None
    canal2: str | None = None
    commentaire: str | None = None
    #: Identifiant en base, renseigné à la lecture (vide pour un nouvel événement).
    id: int | None = None

    @property
    def annee(self) -> int:
        """Année de l'événement (déduite de la date, jamais saisie)."""
        return self.date.year

    @property
    def mois(self) -> int:
        """Numéro du mois de l'événement (déduit de la date)."""
        return self.date.month
