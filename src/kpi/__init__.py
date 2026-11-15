"""Outil de saisie d'activité et de restitution des KPI.

Application autonome destinée aux entrepreneurs individuels : suivi des
contacts et prospects, calcul des indicateurs clés de l'activité et
restitution sous forme d'écrans exportables en PDF.
"""

try:
    from setuptools_scm import get_version
    __version__ = get_version(
        root="../..", 
        relative_to=__file__,
        version_scheme="post-release",
        local_scheme="dirty-tag"
    )
except Exception:
    __version__ = "0.0.0+dev"
