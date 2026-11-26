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


class LigneConversionDetail(NamedTuple):
    """Détail d'un taux de conversion : demandes ouvertes et confirmations.

    ``dimensions`` vaut ``("Tous", canal)`` ou ``(statut, canal)``. Ce détail
    sert à recalculer un taux agrégé (ex. par statut) depuis les compteurs :
    jamais en sommant des taux, ce qui n'aurait pas de sens pour un ratio.
    """

    dimensions: tuple
    demandes: int
    confirmations: int


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


def _borne_annee_mois(
    _evenement: EvenementSuivi,
) -> tuple[int, int]:
    """Retourne le couple (année, mois) d'un événement."""
    return (_evenement.annee, _evenement.mois)


def _dans_periode(
    _ev: EvenementSuivi,
    _debut: tuple[int, int] | None,
    _fin: tuple[int, int] | None,
) -> bool:
    """Vrai si l'événement est dans [début, fin] (bornes en (année, mois))."""
    _cle = _borne_annee_mois(_ev)
    if _debut is not None and _cle < _debut:
        return False
    if _fin is not None and _cle > _fin:
        return False
    return True


def _avant_periode(
    _ev: EvenementSuivi,
    _debut: tuple[int, int] | None,
) -> bool:
    """Vrai si l'événement est strictement avant le début de période."""
    if _debut is None:
        return False
    return _borne_annee_mois(_ev) < _debut


def _calculer_demandeurs_ouverts(
    _tous_evenements: Sequence[EvenementSuivi],
    _debut: tuple[int, int] | None,
    _fin: tuple[int, int] | None,
) -> tuple[set[str], dict[str, str], dict[str, str]]:
    """Retourne (demandeurs_ouverts, statut_par_personne, canal_par_personne).

    - ``demandeurs_ouverts`` : personnes ayant au moins une demande dans la
      période, OU une demande avant la période sans aucune Confirmation
      à une date ≤ fin de période (la demande n'a jamais été convertie).
    - ``statut_par_personne`` : statut de la première demande de chaque
      personne (chronologiquement). Un statut vide (None) vaut « prospect ».
    - ``canal_par_personne`` : canal de la première demande de chaque personne.
    """
    _premiere_demande: dict[str, tuple[tuple[int, int], str, str]] = {}
    _demande_dans_periode: set[str] = set()
    _demande_avant: set[str] = set()
    # Confirmations à toute date ≤ fin de période (ferment la demande).
    _confirmation_avant_fin: set[str] = set()
    for _ev in _tous_evenements:
        if _ev.action_public in ACTIONS_DEMANDE:
            _cle = _borne_annee_mois(_ev)
            if _ev.personne not in _premiere_demande:
                _premiere_demande[_ev.personne] = (
                    _cle,
                    _ev.statut_contact or "prospect",
                    _ev.canal or "(vide)",
                )
            if _dans_periode(_ev, _debut, _fin):
                _demande_dans_periode.add(_ev.personne)
            elif _avant_periode(_ev, _debut):
                _demande_avant.add(_ev.personne)
        if _ev.action_photographe == "Confirmation":
            _cle = _borne_annee_mois(_ev)
            if _fin is None or _cle <= _fin:
                _confirmation_avant_fin.add(_ev.personne)
    _demandeurs = _demande_dans_periode | (
        _demande_avant - _confirmation_avant_fin
    )
    _statut = {_p: _s for _p, (_, _s, _) in _premiere_demande.items()}
    _canal = {_p: _c for _p, (_, _, _c) in _premiere_demande.items()}
    return _demandeurs, _statut, _canal


def _compter_confirmations_dans_periode(
    _tous_evenements: Sequence[EvenementSuivi],
    _debut: tuple[int, int] | None,
    _fin: tuple[int, int] | None,
) -> dict[str, int]:
    """Compte les Confirmations dans la période, par personne."""
    _par_personne: dict[str, int] = defaultdict(int)
    for _ev in _tous_evenements:
        if (
            _ev.action_photographe == "Confirmation"
            and _dans_periode(_ev, _debut, _fin)
        ):
            _par_personne[_ev.personne] += 1
    return dict(_par_personne)


class NbConversions(Indicateur):
    """Nombre de conversions (Confirmations) dans la période, par statut et canal."""

    libelle: ClassVar[str] = "Nombre de conversions"
    description: ClassVar[str] = (
        "Événements « Confirmation » du photographe dans la période, "
        "regroupés par statut puis canal de la première demande."
    )
    dimensions: ClassVar[tuple[str, ...]] = ("statut", "canal")

    def calculer(self, _evenements: Sequence[EvenementSuivi]) -> list[LigneIndicateur]:
        """Compatibilité : période = toutes les données."""
        return self.calculer_periode(_evenements, None, None)

    def calculer_periode(
        self,
        _tous_evenements: Sequence[EvenementSuivi],
        _debut: tuple[int, int] | None,
        _fin: tuple[int, int] | None,
    ) -> list[LigneIndicateur]:
        """Compte les Confirmations dans [début, fin] par (statut, canal)."""
        _confirmations = _compter_confirmations_dans_periode(
            _tous_evenements, _debut, _fin
        )
        _, _statut, _canal = _calculer_demandeurs_ouverts(
            _tous_evenements, _debut, _fin
        )
        # Agrégation par (statut, canal), par statut, et par canal (cumul)
        _par_statut_canal: dict[tuple[str, str], int] = defaultdict(int)
        _par_statut: dict[str, int] = defaultdict(int)
        _par_canal: dict[str, int] = defaultdict(int)
        for _personne, _nb in _confirmations.items():
            _s = _statut.get(_personne, "prospect")
            _c = _canal.get(_personne, "(vide)")
            _par_statut_canal[(_s, _c)] += _nb
            _par_statut[_s] += _nb
            _par_canal[_c] += _nb
        _total = sum(_confirmations.values())
        _lignes: list[LigneIndicateur] = []
        # Canaux cumulés sous « Tous »
        for _c in sorted(_par_canal):
            _lignes.append(
                LigneIndicateur(
                    dimensions=("Tous", _c),
                    valeur=float(_par_canal[_c]),
                )
            )
        for _s in sorted(_par_statut):
            _canaux = sorted(
                _c for (_ss, _c) in _par_statut_canal if _ss == _s
            )
            for _c in _canaux:
                _lignes.append(
                    LigneIndicateur(
                        dimensions=(_s, _c),
                        valeur=float(_par_statut_canal[(_s, _c)]),
                    )
                )
        return _lignes


class TauxConversion(Indicateur):
    """Taux de conversion : Confirmations / demandes ouvertes × 100, par statut et canal."""

    libelle: ClassVar[str] = "Taux de conversion"
    description: ClassVar[str] = (
        "Pourcentage de demandes ouvertes converties (Confirmation) "
        "dans la période, décomposé par statut puis canal."
    )
    dimensions: ClassVar[tuple[str, ...]] = ("statut", "canal")

    def calculer(self, _evenements: Sequence[EvenementSuivi]) -> list[LigneIndicateur]:
        """Compatibilité : période = toutes les données."""
        return self.calculer_periode(_evenements, None, None)

    def _compteurs_periode(
        self,
        _tous_evenements: Sequence[EvenementSuivi],
        _debut: tuple[int, int] | None,
        _fin: tuple[int, int] | None,
    ) -> tuple[dict[tuple[str, str], int], dict[tuple[str, str], int]]:
        """Retourne (demandes, confirmations) indexées par (statut, canal).

        Chaque personne contribue à la fois à la ligne ``("Tous", canal)``
        et à la ligne ``(statut, canal)`` : les agrégats « Tous » et par
        statut se lisent directement dans ces compteurs, et un taux agrégé
        se recalcule depuis eux (jamais en sommant des taux).
        """
        _demandeurs, _statut, _canal = _calculer_demandeurs_ouverts(
            _tous_evenements, _debut, _fin
        )
        _confirmations = _compter_confirmations_dans_periode(
            _tous_evenements, _debut, _fin
        )
        _dem: dict[tuple[str, str], int] = defaultdict(int)
        _conf: dict[tuple[str, str], int] = defaultdict(int)
        for _p in _demandeurs:
            _s = _statut.get(_p, "prospect")
            _c = _canal.get(_p, "(vide)")
            _dem[("Tous", _c)] += 1
            _dem[(_s, _c)] += 1
        for _p, _nb in _confirmations.items():
            _s = _statut.get(_p, "prospect")
            _c = _canal.get(_p, "(vide)")
            _conf[("Tous", _c)] += _nb
            _conf[(_s, _c)] += _nb
        return dict(_dem), dict(_conf)

    def calculer_detail_periode(
        self,
        _tous_evenements: Sequence[EvenementSuivi],
        _debut: tuple[int, int] | None,
        _fin: tuple[int, int] | None,
    ) -> list[LigneConversionDetail]:
        """Détail (demandes, confirmations) par (« Tous »/statut, canal).

        Toutes les combinaisons sont retournées, y compris à 0 % : un canal
        sans conversion mais avec des demandes doit quand même peser dans
        le dénominateur du taux agrégé par statut.
        """
        _dem, _conf = self._compteurs_periode(_tous_evenements, _debut, _fin)
        _cles = sorted(set(_dem) | set(_conf))
        return [
            LigneConversionDetail(
                dimensions=_cle,
                demandes=_dem.get(_cle, 0),
                confirmations=_conf.get(_cle, 0),
            )
            for _cle in _cles
        ]

    def taux_global_periode(
        self,
        _tous_evenements: Sequence[EvenementSuivi],
        _debut: tuple[int, int] | None,
        _fin: tuple[int, int] | None,
    ) -> float:
        """Taux global (%) sur la période : confirmations / demandes ouvertes.

        Recalculé depuis les compteurs, jamais depuis les taux par canal.
        """
        _dem, _conf = self._compteurs_periode(_tous_evenements, _debut, _fin)
        _nb_demandeurs = sum(
            _nb for _cle, _nb in _dem.items() if _cle[0] == "Tous"
        )
        _nb_confirmations = sum(
            _nb for _cle, _nb in _conf.items() if _cle[0] == "Tous"
        )
        if _nb_demandeurs > 0:
            return _nb_confirmations / _nb_demandeurs * 100.0
        return 0.0

    def calculer_periode(
        self,
        _tous_evenements: Sequence[EvenementSuivi],
        _debut: tuple[int, int] | None,
        _fin: tuple[int, int] | None,
    ) -> list[LigneIndicateur]:
        """Calcule les composantes du taux par (statut, canal), en %."""
        _dem_statut_canal, _conf_statut_canal = self._compteurs_periode(
            _tous_evenements, _debut, _fin
        )
        _dem_canal: dict[str, int] = defaultdict(int)
        _conf_canal: dict[str, int] = defaultdict(int)
        _dem_statut: dict[str, int] = defaultdict(int)
        for (_s, _c), _nb in _dem_statut_canal.items():
            if _s == "Tous":
                _dem_canal[_c] += _nb
            else:
                _dem_statut[_s] += _nb
        for (_s, _c), _nb in _conf_statut_canal.items():
            if _s == "Tous":
                _conf_canal[_c] += _nb
        _lignes: list[LigneIndicateur] = []
        # Canaux cumulés sous « Tous » (tous statuts confondus)
        for _c in sorted(_dem_canal):
            _nd = _dem_canal[_c]
            _nc = _conf_canal.get(_c, 0)
            _t = (_nc / _nd * 100.0) if _nd > 0 else 0.0
            if _t > 0:  # ne pas afficher les canaux à 0 %
                _lignes.append(
                    LigneIndicateur(dimensions=("Tous", _c), valeur=_t)
                )
        for _s in sorted(_dem_statut):
            _canaux = sorted(
                _c for (_ss, _c) in _dem_statut_canal if _ss == _s
            )
            for _c in _canaux:
                _nd = _dem_statut_canal[(_s, _c)]
                _nc = _conf_statut_canal.get((_s, _c), 0)
                _t = (_nc / _nd * 100.0) if _nd > 0 else 0.0
                if _t > 0:  # ne pas afficher les canaux à 0 %
                    _lignes.append(
                        LigneIndicateur(dimensions=(_s, _c), valeur=_t)
                    )
        return _lignes


#: Registre des indicateurs disponibles : l'ajout d'un KPI se fait ici.
REGISTRE_INDICATEURS: list[type[Indicateur]] = [
    NbProspects,
    NbDemandes,
    TauxGhosting,
    RdvParCanal,
    NbConversions,
    TauxConversion,
]
