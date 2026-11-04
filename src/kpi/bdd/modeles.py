"""Dépôts d'accès aux données de la base SQLite.

Chaque classe de ce module encapsule les requêtes SQL d'un périmètre
(référentiels, personnes, suivi, Google Analytics) : le reste de
l'application ne construit jamais de SQL lui-même.
"""

from datetime import date

from kpi.bdd.connexion import BaseDonnees
from kpi.suivi import EvenementSuivi

#: Tables de référence autorisées (garde-fou contre l'injection SQL).
TABLES_REFERENTIELLES = (
    "canal",
    "provenance",
    "statut_contact",
    "prestation",
    "detail_prestation",
    "action",
)


class ReferentielRepository:
    """Accès en lecture et écriture aux tables de référence.

    Les tables de référence alimentent les listes déroulantes de la saisie
    (issues de l'onglet ``Listes`` du classeur d'origine).
    """

    def __init__(self, _base: BaseDonnees) -> None:
        """Mémorise la connexion à la base."""
        self._base = _base

    def lister(self, _table: str) -> list[str]:
        """Retourne les valeurs actives d'un référentiel, triées par nom.

        :param _table: nom de la table de référence.
        :raises ValueError: si la table n'est pas un référentiel connu.
        """
        if _table not in TABLES_REFERENTIELLES:
            raise ValueError(f"Table de référence inconnue : {_table}")
        _curseur = self._base.connexion.execute(
            f"SELECT nom FROM {_table} WHERE actif = 1 ORDER BY nom"  # noqa: S608 - table listée blanche
        )
        return [_ligne["nom"] for _ligne in _curseur.fetchall()]

    def identifier(self, _table: str, _valeur: str) -> int | None:
        """Retourne l'identifiant d'une valeur d'un référentiel, ou None."""
        if _table not in TABLES_REFERENTIELLES:
            raise ValueError(f"Table de référence inconnue : {_table}")
        _curseur = self._base.connexion.execute(
            f"SELECT id FROM {_table} WHERE nom = ?",  # noqa: S608 - table listée blanche
            (_valeur,),
        )
        _ligne = _curseur.fetchone()
        return _ligne["id"] if _ligne else None

    def obtenir_ou_creer(self, _table: str, _valeur: str) -> int:
        """Retourne l'identifiant d'une valeur, en la créant si nécessaire.

        Utilisé par l'import du classeur : une valeur rencontrée dans le suivi
        mais absente de la liste (par exemple une action saisie librement)
        est ajoutée au référentiel plutôt que perdue.
        """
        _id = self.identifier(_table, _valeur)
        if _id is not None:
            return _id
        _curseur = self._base.connexion.execute(
            f"INSERT INTO {_table} (nom) VALUES (?)",  # noqa: S608 - table listée blanche
            (_valeur,),
        )
        return int(_curseur.lastrowid)

    def ajouter(self, _table: str, _valeur: str) -> bool:
        """Ajoute une valeur à un référentiel.

        :returns: True si la valeur a été créée, False si elle existait déjà.
        """
        if self.identifier(_table, _valeur) is not None:
            return False
        self.obtenir_ou_creer(_table, _valeur)
        return True


class PersonneRepository:
    """Accès aux personnes suivies (prospects et clientes)."""

    def __init__(self, _base: BaseDonnees) -> None:
        """Mémorise la connexion à la base."""
        self._base = _base

    def obtenir_ou_creer(self, _nom: str) -> int:
        """Retourne l'identifiant d'une personne, en la créant si nécessaire."""
        _curseur = self._base.connexion.execute(
            "SELECT id FROM personne WHERE nom = ?", (_nom,)
        )
        _ligne = _curseur.fetchone()
        if _ligne:
            return _ligne["id"]
        _curseur = self._base.connexion.execute(
            "INSERT INTO personne (nom) VALUES (?)", (_nom,)
        )
        return int(_curseur.lastrowid)

    def lister(self) -> list[str]:
        """Retourne les noms des personnes actives, triés par nom."""
        _curseur = self._base.connexion.execute(
            "SELECT nom FROM personne WHERE actif = 1 ORDER BY nom"
        )
        return [_ligne["nom"] for _ligne in _curseur.fetchall()]


class SuiviRepository:
    """Accès à la table principale ``suivi_activite``."""

    def __init__(self, _base: BaseDonnees) -> None:
        """Prépare les dépôts auxiliaires nécessaires à l'enregistrement."""
        self._base = _base
        self._referentiels = ReferentielRepository(_base)
        self._personnes = PersonneRepository(_base)

    def ajouter(self, _evenement: EvenementSuivi) -> int:
        """Enregistre un événement de suivi et retourne son identifiant.

        Les valeurs de référence inconnues sont créées automatiquement : la
        saisie de l'utilisatrice ne doit jamais être bloquée par une liste
        incomplète.
        """
        _personne_id = self._personnes.obtenir_ou_creer(_evenement.personne)
        _curseur = self._base.connexion.execute(
            """
            INSERT INTO suivi_activite (
                date, personne_id, statut_contact_id, action_public_id,
                canal_id, provenance_id, prestation_id, detail_prestation_id,
                action_photographe_id, canal2_id, commentaire
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _evenement.date.isoformat(),
                _personne_id,
                self._id_referentiel("statut_contact", _evenement.statut_contact),
                self._id_referentiel("action", _evenement.action_public),
                self._id_referentiel("canal", _evenement.canal),
                self._id_referentiel("provenance", _evenement.provenance),
                self._id_referentiel("prestation", _evenement.prestation),
                self._id_referentiel("detail_prestation", _evenement.detail_prestation),
                self._id_referentiel("action", _evenement.action_photographe),
                self._id_referentiel("canal", _evenement.canal2),
                _evenement.commentaire,
            ),
        )
        return int(_curseur.lastrowid)

    def _id_referentiel(self, _table: str, _valeur: str | None) -> int | None:
        """Retourne l'identifiant d'une valeur de référence, None si vide."""
        if _valeur is None or str(_valeur).strip() == "":
            return None
        return self._referentiels.obtenir_ou_creer(_table, str(_valeur).strip())

    #: Requête de lecture commune (création, liste, modification, suppression).
    REQUETE_LECTURE = """
            SELECT s.id, s.date, p.nom AS personne, sc.nom AS statut_contact,
                   ap.nom AS action_public, c1.nom AS canal,
                   pr.nom AS provenance, pe.nom AS prestation,
                   dp.nom AS detail_prestation, aph.nom AS action_photographe,
                   c2.nom AS canal2, s.commentaire
            FROM suivi_activite s
            JOIN personne p ON p.id = s.personne_id
            LEFT JOIN statut_contact sc ON sc.id = s.statut_contact_id
            LEFT JOIN action ap ON ap.id = s.action_public_id
            LEFT JOIN canal c1 ON c1.id = s.canal_id
            LEFT JOIN provenance pr ON pr.id = s.provenance_id
            LEFT JOIN prestation pe ON pe.id = s.prestation_id
            LEFT JOIN detail_prestation dp ON dp.id = s.detail_prestation_id
            LEFT JOIN action aph ON aph.id = s.action_photographe_id
            LEFT JOIN canal c2 ON c2.id = s.canal2_id
            """

    def lister(self) -> list[EvenementSuivi]:
        """Retourne tous les événements du suivi, triés par date."""
        _curseur = self._base.connexion.execute(self.REQUETE_LECTURE)
        return [self._vers_evenement(_ligne) for _ligne in _curseur.fetchall()]

    def _vers_evenement(self, _ligne) -> EvenementSuivi:
        """Construit un événement depuis une ligne de lecture SQL."""
        return EvenementSuivi(
            id=_ligne["id"],
            date=date.fromisoformat(_ligne["date"]),
            personne=_ligne["personne"],
            statut_contact=_ligne["statut_contact"],
            action_public=_ligne["action_public"],
            canal=_ligne["canal"],
            provenance=_ligne["provenance"],
            prestation=_ligne["prestation"],
            detail_prestation=_ligne["detail_prestation"],
            action_photographe=_ligne["action_photographe"],
            canal2=_ligne["canal2"],
            commentaire=_ligne["commentaire"],
        )

    def obtenir(self, _identifiant: int) -> EvenementSuivi | None:
        """Retourne l'événement portant cet identifiant, ou None s'il n'existe pas."""
        _curseur = self._base.connexion.execute(
            self.REQUETE_LECTURE + " WHERE s.id = ?",
            (_identifiant,),
        )
        _ligne = _curseur.fetchone()
        return self._vers_evenement(_ligne) if _ligne else None

    def mettre_a_jour(self, _identifiant: int, _evenement: EvenementSuivi) -> None:
        """Remplace le contenu d'un événement existant.

        :raises ValueError: si aucun événement ne porte cet identifiant.
        """
        if self.obtenir(_identifiant) is None:
            raise ValueError(f"Événement inconnu : {_identifiant}")
        _personne_id = self._personnes.obtenir_ou_creer(_evenement.personne)
        self._base.connexion.execute(
            """
            UPDATE suivi_activite SET
                date = ?, personne_id = ?, statut_contact_id = ?,
                action_public_id = ?, canal_id = ?, provenance_id = ?,
                prestation_id = ?, detail_prestation_id = ?,
                action_photographe_id = ?, canal2_id = ?, commentaire = ?
            WHERE id = ?
            """,
            (
                _evenement.date.isoformat(),
                _personne_id,
                self._id_referentiel("statut_contact", _evenement.statut_contact),
                self._id_referentiel("action", _evenement.action_public),
                self._id_referentiel("canal", _evenement.canal),
                self._id_referentiel("provenance", _evenement.provenance),
                self._id_referentiel("prestation", _evenement.prestation),
                self._id_referentiel("detail_prestation", _evenement.detail_prestation),
                self._id_referentiel("action", _evenement.action_photographe),
                self._id_referentiel("canal", _evenement.canal2),
                _evenement.commentaire,
                _identifiant,
            ),
        )

    def supprimer(self, _identifiant: int) -> None:
        """Supprime définitivement un événement.

        :raises ValueError: si aucun événement ne porte cet identifiant.
        """
        _curseur = self._base.connexion.execute(
            "DELETE FROM suivi_activite WHERE id = ?", (_identifiant,)
        )
        if _curseur.rowcount == 0:
            raise ValueError(f"Événement inconnu : {_identifiant}")

    def compter(self) -> int:
        """Retourne le nombre total d'événements enregistrés."""
        _curseur = self._base.connexion.execute("SELECT COUNT(*) AS total FROM suivi_activite")
        return int(_curseur.fetchone()["total"])


class GoogleAnalyticsRepository:
    """Accès aux relevés Google Analytics (visiteurs, canaux, requêtes)."""

    def __init__(self, _base: BaseDonnees) -> None:
        """Mémorise la connexion à la base."""
        self._base = _base

    def enregistrer_visiteurs(
        self, _annee: int, _mois: int, _visiteurs: int, _origine: str = "manuel"
    ) -> None:
        """Enregistre ou met à jour le nombre de visiteurs d'un mois.

        Le rechargement d'un mois déjà relevé remplace l'ancienne valeur :
        l'import est idempotent.
        """
        self._base.connexion.execute(
            """
            INSERT INTO ga_visiteurs (annee, mois, visiteurs, origine, date_maj)
            VALUES (?, ?, ?, ?, datetime('now'))
            ON CONFLICT(annee, mois) DO UPDATE SET
                visiteurs = excluded.visiteurs,
                origine = excluded.origine,
                date_maj = excluded.date_maj
            """,
            (_annee, _mois, _visiteurs, _origine),
        )

    def enregistrer_canal(
        self, _annee: int, _mois: int, _canal: str, _visiteurs: int, _origine: str = "manuel"
    ) -> None:
        """Enregistre ou met à jour les visiteurs d'un mois pour un canal."""
        self._base.connexion.execute(
            """
            INSERT INTO ga_canaux (annee, mois, canal, visiteurs, origine, date_maj)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(annee, mois, canal) DO UPDATE SET
                visiteurs = excluded.visiteurs,
                origine = excluded.origine,
                date_maj = excluded.date_maj
            """,
            (_annee, _mois, _canal, _visiteurs, _origine),
        )

    def enregistrer_requete(
        self, _annee: int, _mois: int, _requete: str, _occurrences: int, _origine: str = "manuel"
    ) -> None:
        """Enregistre ou met à jour les occurrences d'une requête sur un mois."""
        self._base.connexion.execute(
            """
            INSERT INTO ga_requetes (annee, mois, requete, occurrences, origine, date_maj)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(annee, mois, requete) DO UPDATE SET
                occurrences = excluded.occurrences,
                origine = excluded.origine,
                date_maj = excluded.date_maj
            """,
            (_annee, _mois, _requete, _occurrences, _origine),
        )

    def lister_visiteurs(self) -> list[tuple[int, int, int]]:
        """Retourne les relevés mensuels (année, mois, visiteurs), triés."""
        _curseur = self._base.connexion.execute(
            "SELECT annee, mois, visiteurs FROM ga_visiteurs ORDER BY annee, mois"
        )
        return [(_l["annee"], _l["mois"], _l["visiteurs"]) for _l in _curseur.fetchall()]
