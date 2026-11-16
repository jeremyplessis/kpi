# OpenSpec — Projet KPI

Ce dossier contient la planification du projet au format [OpenSpec](https://github.com/openspec-dev/openspec).

## Structure

```
openspec/
├── project.md              # Contexte du projet (stack, architecture, état, conventions)
├── config.yaml             # Configuration OpenSpec
├── specs/                  # Specs validées du projet (capabilities)
└── changes/                # Changes proposés ou en cours
    ├── ameliorer-consultation-kpi/   # Étape 4a : tableau de bord KPI
    ├── export-pdf-kpi/               # Étape 4b : export PDF
    ├── connecteur-ga4/               # Étape 5 : connecteur Google Analytics 4
    └── indicateurs-ga/               # Étape 6 : indicateurs visiteurs/conversions GA
```

Chaque change contient :

| Fichier | Rôle |
|---|---|
| `proposal.md` | Pourquoi et quoi (vue d'ensemble) |
| `design.md` | Comment (décisions techniques) |
| `specs/<capability>.md` | Exigences précises (format WHEN/THEN) |
| `tasks.md` | Tâches d'implémentation (checklist) |

## Workflow

1. Lire `project.md` pour le contexte
2. Choisir un change dans `changes/`
3. Lire `proposal.md` → `design.md` → `specs/` → `tasks.md`
4. Implémenter les tâches une par une
5. Quand tout est fait, archiver le change dans `changes/archive/`

## Ordre recommandé

1. `ameliorer-consultation-kpi` (étape 4a)
2. `export-pdf-kpi` (étape 4b)
3. `connecteur-ga4` (étape 5)
4. `indicateurs-ga` (étape 6, nécessite décision sur les règles de conversion)
