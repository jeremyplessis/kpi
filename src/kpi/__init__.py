"""Outil de saisie d'activité et de restitution des KPI.

Application autonome destinée aux entrepreneurs individuels : suivi des
contacts et prospects, calcul des indicateurs clés de l'activité et
restitution sous forme d'écrans exportables en PDF.
"""

try:
    from importlib.metadata import version
    __version__ = version("kpi")
except (ImportError, ModuleNotFoundError):
    # Fallback pour les environnements sans importlib.metadata (Python < 3.8)
    # ou quand le package n'est pas installé
    __version__ = "0.0.0+dev"
