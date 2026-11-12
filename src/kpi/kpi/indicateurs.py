"""Indicateurs de l'activité : règles de calcul explicites.

Les règles ci-dessous sont la traduction en code des tableaux croisés
dynamiques du classeur d'origine, telles qu'analysées dans
``documentation/00_analyse_kpi_xlsx.md``. Elles ont été validées avec
l'utilisatrice le 28 octobre 2026 :

- une « demande » est une action du public ``Demande`` ou ``Réservation``
  (une réservation en ligne est une demande directe) ;
- une « réponse » est toute action du public autre qu'une demande, un tiret
  ou une relance : Réponse, Confirmation, Paiement, RDV, Refus, Échanges…

Les indicateurs « Nombre de visiteurs Google Analytics » et
« Nombre de conversions » sont volontairement reportés : leur mode de calcul
n'est pas encore défini (voir la proposition d'architecture).

Sémantique importante : le taux de ghosting est un **ratio de flux mensuels**
(nb de personnes ayant demandé ce mois-ci / nb de personnes ayant répondu
ce mois-ci), pas le suivi d'une cohorte de demandes : une réponse peut
donner suite à une demande du mois précédent, et le taux est borné à 0.
"""

from collections import defaultdict
from typing import ClassVar, NamedTuple, Sequence

from kpi.suivi import EvenementSuivi

#: Actions du public comptées comme une demande (une réservation en ligne
#: est une demande directe, règle confirmée par l'analyse du classeur).
ACTIONS_DEMANDE = frozenset({"Demande", "Réservation"})

#: Actions du public ignorées pour la recherche d'une réponse : les demandes,
#: le tiret (aucune action) et la relance. Une « Relance » dans la colonne
#: Action public est une action du photographe (elle relance un contact
#: silencieux), pas une réponse du contact : ce choix est documenté et
#: restera à confirmer avec l'utilisatrice.
ACTIONS_SANS_REPONSE = frozenset({"-", "Demande", "Réservation", "Relance"})


class LigneIndicateur(NamedTuple):
    """Une ligne de résultat : regroupement (dimensions) et valeur calculée."""

    dimensions: tuple
    valeur: float


class LigneGhosting(NamedTuple):
    """Détail mensuel du taux de ghosting.

    Le taux est borné à 0 : un mois où les réponses dépassent les demandes
    (reports de mois précédents) ne produit pas un taux négatif, conformément
    au classeur d'origine.
    """

    annee: int
    mois: int
    demandes: int
    reponses: int
    taux: float


class Indicateur:
    """Classe de base de tous les indicateurs KPI.

    Un indicateur reçoit la liste des événements du suivi et retourne des
    lignes de résultat regroupées selon ses dimensions.
    """

    libelle: ClassVar[str] = ""
    description: ClassVar[str] = ""
    dimensions: ClassVar[tuple[str, ...]] = ()

    def calculer(self, _evenements: Sequence[EvenementSuivi]) -> list[LigneIndicateur]:
        """Calcule l'indicateur sur les événements fournis.

        :raises NotImplementedError: dans la classe de base.
        """
        raise NotImplementedError


class NbProspects(Indicateur):
    """Nombre de prospects contactés, par année, mois et canal."""

    libelle: ClassVar[str] = "Nombre de prospects"
    description: ClassVar[str] = (
        "Événements du suivi portant le statut « prospect », "
        "regroupés par année, mois et canal."
    )
    dimensions: ClassVar[tuple[str, ...]] = ("année", "mois", "canal")

    def calculer(self, _evenements: Sequence[EvenementSuivi]) -> list[LigneIndicateur]:
        """Compte les événements de prospects par (année, mois, canal)."""
        _comptes: dict[tuple, int] = defaultdict(int)
        for _evenement in _evenements:
            if _evenement.statut_contact == "prospect":
                _cle = (_evenement.annee, _evenement.mois, _evenement.canal or "(vide)")
                _comptes[_cle] += 1
        return [
            LigneIndicateur(dimensions=_cle, valeur=float(_total))
            for _cle, _total in sorted(_comptes.items())
        ]


class NbDemandes(Indicateur):
    """Nombre de demandes reçues, par année, mois et canal.

    Une même personne ne compte qu'une fois par mois, conformément au
    classeur d'origine (dédoublonnage par (mois, personne)).
    """

    libelle: ClassVar[str] = "Nombre de demandes"
    description: ClassVar[str] = (
        "Demandes (action « Demande » ou « Réservation »), une personne "
        "ne comptant qu'une fois par mois, regroupées par année, mois et canal."
    )
    dimensions: ClassVar[tuple[str, ...]] = ("année", "mois", "canal")

    def calculer(self, _evenements: Sequence[EvenementSuivi]) -> list[LigneIndicateur]:
        """Compte les demandes dédoublonnées par (année, mois, personne)."""
        _vues: set[tuple] = set()
        _comptes: dict[tuple, int] = defaultdict(int)
        for _evenement in _evenements:
            if _evenement.action_public not in ACTIONS_DEMANDE:
                continue
            _cle_personne = (
                _evenement.annee,
                _evenement.mois,
                _evenement.personne,
            )
            if _cle_personne in _vues:
                continue
            _vues.add(_cle_personne)
            _cle = (_evenement.annee, _evenement.mois, _evenement.canal or "(vide)")
            _comptes[_cle] += 1
        return [
            LigneIndicateur(dimensions=_cle, valeur=float(_total))
            for _cle, _total in sorted(_comptes.items())
        ]


class TauxGhosting(Indicateur):
    """Taux de ghosting mensuel : demandes restées sans réponse.

    Un contact a « répondu » sur un mois donné si au moins une action du
    public de ce mois est une réponse (toute action autre qu'une demande,
    un tiret ou une relance).
    """

    libelle: ClassVar[str] = "Taux de ghosting"
    description: ClassVar[str] = (
        "Part des demandes du mois restées sans réponse du contact, "
        "calculée par mois et bornée à 0."
    )
    dimensions: ClassVar[tuple[str, ...]] = ("année", "mois")

    def calculer(self, _evenements: Sequence[EvenementSuivi]) -> list[LigneIndicateur]:
        """Calcule le taux mensuel à partir du détail mensuel."""
        return [
            LigneIndicateur(dimensions=(_ligne.annee, _ligne.mois), valeur=_ligne.taux)
            for _ligne in self.calculer_detail(_evenements)
        ]

    def calculer_detail(self, _evenements: Sequence[EvenementSuivi]) -> list[LigneGhosting]:
        """Retourne, pour chaque mois avec demande, le détail du calcul.

        Le détail (demandes, réponses, taux) est conservé pour l'affichage,
        comme dans le tableau croisé d'origine. Conformément à la règle
        validée, une réponse est comptée même si la personne n'a pas
        demandé ce même mois (sa demande peut dater du mois précédent) :
        le taux est ensuite borné à 0.
        """
        _demandes: dict[tuple, set[str]] = defaultdict(set)
        _reponses: dict[tuple, set[str]] = defaultdict(set)
        for _evenement in _evenements:
            _cle = (_evenement.annee, _evenement.mois)
            _action = _evenement.action_public
            if _action in ACTIONS_DEMANDE:
                _demandes[_cle].add(_evenement.personne)
            if _action is not None and _action not in ACTIONS_SANS_REPONSE:
                _reponses[_cle].add(_evenement.personne)
        _lignes = []
        for _cle in sorted(_demandes):
            _nb_demandes = len(_demandes[_cle])
            _nb_reponses = len(_reponses.get(_cle, set()))
            _taux_brut = (_nb_demandes - _nb_reponses) / _nb_demandes
            _lignes.append(
                LigneGhosting(
                    annee=_cle[0],
                    mois=_cle[1],
                    demandes=_nb_demandes,
                    reponses=_nb_reponses,
                    taux=max(0.0, _taux_brut),
                )
            )
        return _lignes


class RdvParCanal(Indicateur):
    """Nombre de rendez-vous obtenus, par année et canal de réponse."""

    libelle: ClassVar[str] = "RDV par canal"
    description: ClassVar[str] = (
        "Événements portant l'action photographe « RDV », "
        "regroupés par année et canal utilisé."
    )
    dimensions: ClassVar[tuple[str, ...]] = ("année", "canal")

    def calculer(self, _evenements: Sequence[EvenementSuivi]) -> list[LigneIndicateur]:
        """Compte les rendez-vous par (année, canal de réponse)."""
        _comptes: dict[tuple, int] = defaultdict(int)
        for _evenement in _evenements:
            if _evenement.action_photographe == "RDV":
                _cle = (_evenement.annee, _evenement.canal2 or "(vide)")
                _comptes[_cle] += 1
        _lignes_resultat = [
            LigneIndicateur(dimensions=_cle, valeur=float(_total))
            for _cle, _total in sorted(_comptes.items())
        ]
        return _lignes_resultat


#: Registre des indicateurs disponibles : l'ajout d'un KPI se fait ici.
REGISTRE_INDICATEURS: list[type[Indicateur]] = [
    NbProspects,
    NbDemandes,
    TauxGhosting,
    RdvParCanal,
]
