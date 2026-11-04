"""Ouverture et initialisation de la base SQLite de l'application.

La base est un simple fichier unique (par défaut ``kpi.sqlite3``) situé à côté
de l'application : la sauvegarde de l'outil se réduit donc à la copie de ce
fichier. Voir ``documentation/01_proposition_architecture.md`` pour le modèle
de données complet.
"""

import sqlite3
from pathlib import Path

#: Schéma de la base : tables de référence, table principale et relevés GA.
SCHEMA = """
CREATE TABLE IF NOT EXISTS canal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE,
    actif INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS provenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE,
    actif INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS statut_contact (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE,
    actif INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS prestation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE,
    actif INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS detail_prestation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE,
    actif INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS action (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE,
    actif INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS personne (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    actif INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS suivi_activite (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    personne_id INTEGER NOT NULL REFERENCES personne(id),
    statut_contact_id INTEGER REFERENCES statut_contact(id),
    action_public_id INTEGER REFERENCES action(id),
    canal_id INTEGER REFERENCES canal(id),
    provenance_id INTEGER REFERENCES provenance(id),
    prestation_id INTEGER REFERENCES prestation(id),
    detail_prestation_id INTEGER REFERENCES detail_prestation(id),
    action_photographe_id INTEGER REFERENCES action(id),
    canal2_id INTEGER REFERENCES canal(id),
    commentaire TEXT
);
CREATE INDEX IF NOT EXISTS idx_suivi_date ON suivi_activite(date);
CREATE INDEX IF NOT EXISTS idx_suivi_personne ON suivi_activite(personne_id);

CREATE TABLE IF NOT EXISTS ga_visiteurs (
    annee INTEGER NOT NULL,
    mois INTEGER NOT NULL,
    visiteurs INTEGER NOT NULL,
    origine TEXT NOT NULL DEFAULT 'manuel',
    date_maj TEXT NOT NULL,
    PRIMARY KEY (annee, mois)
);

CREATE TABLE IF NOT EXISTS ga_canaux (
    annee INTEGER NOT NULL,
    mois INTEGER NOT NULL,
    canal TEXT NOT NULL,
    visiteurs INTEGER NOT NULL,
    origine TEXT NOT NULL DEFAULT 'manuel',
    date_maj TEXT NOT NULL,
    PRIMARY KEY (annee, mois, canal)
);

CREATE TABLE IF NOT EXISTS ga_requetes (
    annee INTEGER NOT NULL,
    mois INTEGER NOT NULL,
    requete TEXT NOT NULL,
    occurrences INTEGER NOT NULL,
    origine TEXT NOT NULL DEFAULT 'manuel',
    date_maj TEXT NOT NULL,
    PRIMARY KEY (annee, mois, requete)
);
"""


class BaseDonnees:
    """Gestion de la connexion à la base SQLite de l'application.

    :param _chemin: chemin du fichier de base (créé s'il n'existe pas).
    """

    def __init__(self, _chemin: str | Path = "kpi.sqlite3") -> None:
        """Ouvre la base, active les clés étrangères et crée le schéma."""
        self.chemin = Path(_chemin)
        self.connexion = sqlite3.connect(self.chemin)
        self.connexion.row_factory = sqlite3.Row
        self.connexion.execute("PRAGMA foreign_keys = ON")
        self._creer_schema()

    def _creer_schema(self) -> None:
        """Crée les tables et index s'ils n'existent pas encore."""
        self.connexion.executescript(SCHEMA)
        self.connexion.commit()

    def valider(self) -> None:
        """Valide durablement les modifications en cours (COMMIT).

        À appeler explicitement après une écriture : la validation ne se
        fait plus implicitement à la fermeture, afin qu'un incident ne
        laisse jamais persister une écriture partielle.
        """
        self.connexion.commit()

    def annuler(self) -> None:
        """Annule les modifications en cours (ROLLBACK)."""
        self.connexion.rollback()

    def fermer(self) -> None:
        """Ferme la connexion sans valider.

        Les modifications non validées par :meth:`valider` sont perdues :
        c'est le comportement voulu pour ne jamais persister un état
        incohérent par accident.
        """
        self.connexion.close()
