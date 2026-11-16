# Proposal: Indicateurs Google Analytics (visiteurs et conversions)

## Why

Les deux indicateurs "Nombre de visiteurs GA" et "Nombre de conversions" étaient volontairement reportés car leur mode de calcul n'était pas défini. Maintenant que les tables GA seront alimentées automatiquement (étape 5), il faut définir et implémenter ces indicateurs pour compléter le tableau de bord.

## What Changes

- Définition des règles de calcul avec l'utilisatrice (à valider avant implémentation) :
  - **Visiteurs GA** : somme des visiteurs mensuels de `ga_visiteurs` sur la période
  - **Conversions** : à définir — pistes : événements GA4 marqués comme conversion, ou événements du suivi avec action "Paiement"/"RDV" croisés avec les visiteurs
- Nouveaux indicateurs dans `src/kpi/kpi/indicateurs.py` (héritant de `Indicateur`)
- Intégration dans le registre `REGISTRE_INDICATEURS`
- Affichage dans l'écran `/kpi` (tableau de bord + page détaillée)
- Possiblement un indicateur croisé : taux de conversion = conversions / visiteurs GA

## Capabilities

### New Capabilities
- `indicateurs-ga/visiteurs-ga`: Indicateur "Nombre de visiteurs GA" depuis les tables GA
- `indicateurs-ga/conversions`: Indicateur "Nombre de conversions" (règle à définir avec l'utilisatrice)
- `indicateurs-ga/taux-conversion`: Taux de conversion = conversions / visiteurs GA (si pertinent)

### Modified Capabilities
- `consultation-kpi/tableau-bord`: Le tableau de bord affiche aussi les nouveaux indicateurs GA
- `kpi/registre-indicateurs`: Deux à trois nouvelles classes dans le registre

## Impact

- `src/kpi/kpi/indicateurs.py` : nouvelles classes d'indicateurs + enregistrement dans le registre
- `src/kpi/web/routes.py` : les indicateurs GA lisent depuis `GoogleAnalyticsRepository` en plus de `SuiviRepository`
- `src/kpi/web/gabarits/kpi.html` : affichage des nouveaux indicateurs (graphiques adaptés)
- `tests/test_calculs_kpi.py` : tests des nouveaux indicateurs
- `tests/test_kpi_web.py` : tests d'affichage des indicateurs GA
- `documentation/06_indicateurs_ga.md` : définition des règles + guide

## Questions à valider avec l'utilisatrice avant implémentation

1. "Visiteurs GA" = somme des `totalUsers` mensuels ? Faut-il distinguer visiteurs uniques vs sessions ?
2. "Conversions" = quoi exactement ? Événements GA4 marqués "conversion" ? Paiements dans le suivi ? RDV pris ?
3. Faut-il un taux de conversion (conversions / visiteurs) ?
4. Faut-il croiser les canaux GA avec les canaux du suivi (ex: visiteurs "Organic Search" vs demandes via "formulaire de contact") ?
