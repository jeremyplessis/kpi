"""Tests du lanceur macOS KPI.command (mise à jour automatique).

Chaque test exécute le vrai script ``KPI.command`` via subprocess dans un
clone git temporaire ayant un remote local (dépôt bare), avec de faux
binaires ``.venv/bin/pip`` et ``.venv/bin/kpi`` qui journalisent leurs
appels. Le vrai dépôt du projet et le vrai venv ne sont jamais touchés.
"""

import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

#: Racine du projet (là où se trouve le vrai KPI.command).
RACINE_PROJET = Path(__file__).resolve().parents[1]

#: Contenu du faux pip : journalise ses arguments dans $KPI_TEST_LOG.
FAUX_PIP = '#!/bin/bash\necho "pip $*" >> "$KPI_TEST_LOG"\n'

#: Contenu du faux kpi : journalise son lancement dans $KPI_TEST_LOG.
FAUX_KPI = '#!/bin/bash\necho "kpi $*" >> "$KPI_TEST_LOG"\n'


class TestLanceurCommand(unittest.TestCase):
    """Exécute KPI.command dans un clone git temporaire isolé."""

    def setUp(self) -> None:
        """Construit un remote bare, un clone propre et les faux binaires."""
        self._dossier = tempfile.TemporaryDirectory()
        _racine = Path(self._dossier.name)
        self._tmp = _racine
        self._remote = _racine / "remote.git"
        self._clone = _racine / "clone"
        self._chemin_log = _racine / "appels.log"
        self._git(["init", "--bare", str(self._remote)])
        self._git(["clone", str(self._remote), str(self._clone)])
        self._branche = self._git(
            ["symbolic-ref", "--short", "HEAD"], cwd=self._clone
        ).stdout.strip()
        # Contenu initial du clone : pyproject.toml, .gitignore, KPI.command
        (self._clone / "pyproject.toml").write_text(
            "[project]\nname = 'kpi'\n"
        )
        (self._clone / ".gitignore").write_text(".venv/\n")
        shutil.copy(RACINE_PROJET / "KPI.command", self._clone / "KPI.command")
        self._git(["add", "."], cwd=self._clone)
        self._git(["commit", "-m", "initial"], cwd=self._clone)
        self._git(["push", "-u", "origin", self._branche], cwd=self._clone)
        self._installer_faux_binaires()

    def tearDown(self) -> None:
        """Supprime le dossier temporaire."""
        self._dossier.cleanup()

    def _git(
        self, args: list[str], cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        """Exécute une commande git avec une identité de test fixe."""
        return subprocess.run(
            [
                "git",
                "-c",
                "user.email=test@example.com",
                "-c",
                "user.name=Test",
                *args,
            ],
            cwd=cwd or self._tmp,
            capture_output=True,
            text=True,
            check=True,
        )

    def _installer_faux_binaires(self) -> None:
        """Crée .venv/bin/pip et .venv/bin/kpi factices et journalisants."""
        _bin = self._clone / ".venv" / "bin"
        _bin.mkdir(parents=True)
        for _nom, _contenu in (("pip", FAUX_PIP), ("kpi", FAUX_KPI)):
            _fichier = _bin / _nom
            _fichier.write_text(_contenu)
            _fichier.chmod(0o755)

    def _avancer_remote(self) -> str:
        """Pousse un nouveau commit sur le remote depuis un second clone.

        :returns: le message du commit poussé.
        """
        _autre = self._clone.parent / "autre"
        self._git(["clone", str(self._remote), str(_autre)])
        (_autre / "README.md").write_text("nouveau contenu\n")
        self._git(["add", "."], cwd=_autre)
        self._git(["commit", "-m", "commit distant"], cwd=_autre)
        self._git(["push", "origin", self._branche], cwd=_autre)
        return "commit distant"

    def _lancer(
        self, env_supp: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        """Exécute KPI.command dans le clone, comme un double-clic Finder."""
        _env = dict(os.environ)
        _env.pop("KPI_SANS_MISE_A_JOUR", None)
        _env.pop("_KPI_MAJ_REEXEC", None)
        _env["KPI_TEST_LOG"] = str(self._chemin_log)
        if env_supp:
            _env.update(env_supp)
        return subprocess.run(
            ["bash", "KPI.command"],
            cwd=self._clone,
            env=_env,
            input="\n",  # simule la touche Entrée du read final
            capture_output=True,
            text=True,
            timeout=120,
        )

    def _log(self) -> list[str]:
        """Retourne les lignes du journal des faux binaires."""
        if not self._chemin_log.exists():
            return []
        return self._chemin_log.read_text().splitlines()

    def _nb_kpi(self) -> int:
        """Compte les lancements du faux kpi dans le journal."""
        return sum(1 for _l in self._log() if _l.startswith("kpi"))

    def _head(self) -> str:
        """Retourne le message du commit HEAD du clone."""
        return self._git(
            ["log", "-1", "--format=%s"], cwd=self._clone
        ).stdout.strip()

    def _hash_pyproject(self) -> str:
        """SHA-256 hexadécimal de pyproject.toml (identique au stamp)."""
        _contenu = (self._clone / "pyproject.toml").read_bytes()
        return hashlib.sha256(_contenu).hexdigest()

    def test_pull_quand_en_retard(self) -> None:
        """Un commit en retard sur origin déclenche pull + ré-exécution."""
        _message = self._avancer_remote()
        _resultat = self._lancer()
        self.assertEqual(_resultat.returncode, 0, _resultat.stderr)
        self.assertIn("Mise à jour du code depuis origin...", _resultat.stdout)
        self.assertEqual(self._head(), _message)
        # Une seule exécution de kpi malgré la ré-exécution du script
        self.assertEqual(self._nb_kpi(), 1)

    def test_repli_origin_sans_upstream(self) -> None:
        """Sans upstream, la branche amont est origin/<branche courante>."""
        self._git(["branch", "--unset-upstream"], cwd=self._clone)
        _message = self._avancer_remote()
        _resultat = self._lancer()
        self.assertEqual(_resultat.returncode, 0, _resultat.stderr)
        self.assertEqual(self._head(), _message)

    def test_rien_quand_a_jour(self) -> None:
        """Code et dépendances à jour : aucun pull, aucun pip, kpi lancé."""
        self._lancer()  # premier lancement : écrit le stamp
        self._chemin_log.unlink()
        _resultat = self._lancer()
        self.assertEqual(_resultat.returncode, 0, _resultat.stderr)
        self.assertNotIn("Mise à jour du code", _resultat.stdout)
        self.assertNotIn("Mise à jour des dépendances", _resultat.stdout)
        self.assertFalse(any(_l.startswith("pip") for _l in self._log()))
        self.assertEqual(self._nb_kpi(), 1)

    def test_pip_quand_pyproject_change(self) -> None:
        """pyproject.toml modifié : pip install -e . relancé, stamp à jour."""
        self._lancer()
        _stamp = self._clone / ".venv" / "kpi-pyproject.sha256"
        self.assertEqual(_stamp.read_text().strip(), self._hash_pyproject())
        (self._clone / "pyproject.toml").write_text(
            "[project]\nname = 'kpi'\nversion = '1'\n"
        )
        self._chemin_log.unlink()
        _resultat = self._lancer()
        self.assertEqual(_resultat.returncode, 0, _resultat.stderr)
        self.assertIn("Mise à jour des dépendances...", _resultat.stdout)
        self.assertTrue(any("install -e ." in _l for _l in self._log()))
        self.assertEqual(_stamp.read_text().strip(), self._hash_pyproject())
        # Lancement suivant : plus de réinstallation
        self._chemin_log.unlink()
        self._lancer()
        self.assertFalse(any(_l.startswith("pip") for _l in self._log()))

    def test_env_desactive_mise_a_jour(self) -> None:
        """KPI_SANS_MISE_A_JOUR=1 : ni pull ni pip, mais kpi est lancé."""
        self._lancer()  # écrit le stamp
        self._avancer_remote()
        (self._clone / "pyproject.toml").write_text(
            "[project]\nname = 'kpi'\nversion = '2'\n"
        )
        _avant = self._head()
        self._chemin_log.unlink()
        _resultat = self._lancer({"KPI_SANS_MISE_A_JOUR": "1"})
        self.assertEqual(_resultat.returncode, 0, _resultat.stderr)
        self.assertEqual(self._head(), _avant)
        self.assertNotIn("Mise à jour", _resultat.stdout)
        self.assertFalse(any(_l.startswith("pip") for _l in self._log()))
        self.assertEqual(self._nb_kpi(), 1)

    def test_remote_injoignable(self) -> None:
        """Fetch en échec (hors ligne) : avertissement, lancement normal."""
        self._git(
            ["remote", "set-url", "origin", "/chemin/inexistant"],
            cwd=self._clone,
        )
        _resultat = self._lancer()
        self.assertEqual(_resultat.returncode, 0, _resultat.stderr)
        self.assertIn("origin injoignable", _resultat.stdout)
        self.assertEqual(self._nb_kpi(), 1)

    def test_pull_impossible_arbre_sale(self) -> None:
        """Pull --ff-only refusé (arbre sale) : avertissement, kpi lancé."""
        self._avancer_remote()  # modifie README.md côté distant
        # modification locale non commitée du même fichier
        (self._clone / "README.md").write_text("modif locale\n")
        _avant = self._head()
        _resultat = self._lancer()
        self.assertEqual(_resultat.returncode, 0, _resultat.stderr)
        self.assertIn("git pull impossible", _resultat.stdout)
        self.assertEqual(self._head(), _avant)  # pas de pull effectué
        self.assertEqual(self._nb_kpi(), 1)

    def test_hors_depot_git(self) -> None:
        """Hors d'un dépôt git, le bloc git est ignoré et kpi est lancé."""
        _dossier = tempfile.TemporaryDirectory()
        self.addCleanup(_dossier.cleanup)
        _racine = Path(_dossier.name)
        shutil.copy(RACINE_PROJET / "KPI.command", _racine / "KPI.command")
        (_racine / "pyproject.toml").write_text("[project]\nname = 'kpi'\n")
        _bin = _racine / ".venv" / "bin"
        _bin.mkdir(parents=True)
        for _nom, _contenu in (("pip", FAUX_PIP), ("kpi", FAUX_KPI)):
            _fichier = _bin / _nom
            _fichier.write_text(_contenu)
            _fichier.chmod(0o755)
        _env = dict(os.environ)
        _env["KPI_TEST_LOG"] = str(self._chemin_log)
        _resultat = subprocess.run(
            ["bash", "KPI.command"],
            cwd=_racine,
            env=_env,
            input="\n",  # simule la touche Entrée du read final
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(_resultat.returncode, 0, _resultat.stderr)
        self.assertEqual(self._nb_kpi(), 1)


if __name__ == "__main__":
    unittest.main()
