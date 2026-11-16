# Tasks: Export PDF KPI

## 1. Dépendance et configuration

- [ ] 1.1 Ajouter `weasyprint>=62` dans `pyproject.toml` dependencies — verify: `.venv/bin/pip install -e .` installe weasyprint sans erreur
- [ ] 1.2 Vérifier que WeasyPrint fonctionne dans l'environnement (test minimal HTML→PDF) — verify: un script de test génère un PDF valide

## 2. Template PDF

- [ ] 2.1 Créer `src/kpi/web/gabarits/rapport_kpi.html` avec mise en page A4 (`@page`), en-tête (titre, version, date, période) — verify: le template se rend sans erreur Jinja2
- [ ] 2.2 Ajouter les blocs pour chaque indicateur : titre, description, tableau complet des données — verify: les 4 indicateurs apparaissent dans le HTML rendu
- [ ] 2.3 Styliser pour l'impression : tableaux compacts, pas de navigation, couleurs sobres — verify: aperçu visuel correct en PDF

## 3. Route d'export

- [ ] 3.1 Créer la route `GET /kpi/export-pdf` dans `routes.py` — verify: la route répond 200 avec `application/pdf`
- [ ] 3.2 Réutiliser `_filtrer_par_periode` et le calcul des indicateurs (mêmes méthodes que `page_kpi`) — verify: les données du PDF correspondent à l'écran
- [ ] 3.3 Générer le PDF via WeasyPrint et retourner un `Response` avec `Content-Disposition: attachment` — verify: le navigateur télécharge le fichier
- [ ] 3.4 Nommer le fichier selon la période : `kpi_2026-01_2026-06.pdf` — verify: le header Content-Disposition contient le bon nom

## 4. Boutons d'export

- [ ] 4.1 Ajouter un bouton "Exporter en PDF" dans `kpi.html` (conservant les query params actuels) — verify: le lien pointe vers `/kpi/export-pdf?...` avec les bons filtres
- [ ] 4.2 Ajouter le même bouton dans `kpi_ghosting.html` — verify: export depuis la page ghosting fonctionne

## 5. Tests

- [ ] 5.1 Test : `GET /kpi/export-pdf` retourne 200 avec `Content-Type: application/pdf` — verify: `test_export_pdf_statut`
- [ ] 5.2 Test : le contenu PDF commence par `%PDF-` et fait plus de 1 Ko — verify: `test_export_pdf_valide`
- [ ] 5.3 Test : export avec filtres de période retourne un PDF avec le bon nom de fichier — verify: `test_export_pdf_nom_fichier`
- [ ] 5.4 Test : export avec indicateur spécifique ne contient que cet indicateur — verify: `test_export_pdf_indicateur_specifique`
- [ ] 5.5 Test : les totaux du PDF correspondent aux totaux de l'écran — verify: `test_export_pdf_coherence`

## 6. Documentation

- [ ] 6.1 Documenter l'export PDF dans `documentation/04_ecran_consultation.md` — verify: le guide explique le bouton et le contenu du PDF
- [ ] 6.2 Mettre à jour le CHANGELOG.md — verify: entrée pour l'export PDF

## 7. Intégration

- [ ] 7.1 Tous les tests passent (68 existants + nouveaux) — verify: `.venv/bin/python -m unittest discover -s tests`
- [ ] 7.2 Style PEP 8 respecté — verify: `.venv/bin/pycodestyle src/ tests/`
