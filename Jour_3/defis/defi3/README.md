# Defi 3 - Ce que dit bourse.db

Requetes SQL du sujet, executees sur le vrai `bourse.db` (25 actions,
scrape du 29/07/2026 ~09:26 UTC).

## A savoir avant de lire les chiffres

Au moment du crawl, la page du palmares affichait l'onglet "Hausses" :
les 25 lignes ont donc toutes une variation positive. Le "top 5 baisses"
plus bas n'est pas un vrai groupe d'actions en recul, juste les 5 plus
petites hausses du lot (le palmares a un onglet "Baisses" a part, pas
scrape ici).

## Top 5 hausses

| Libelle | Variation | Cours |
|---|---|---|
| ALTEN | +19.46% | 79.80 |
| SOPRA STERIA | +14.29% | 196.80 |
| KERING | +12.57% | 282.00 |
| BUREAU VERITAS | +7.65% | 29.41 |
| NEXANS | +5.96% | 131.50 |

## Top 5 "baisses" (en realite les plus petites hausses)

| Libelle | Variation | Cours |
|---|---|---|
| MAUREL & PROM | +0.76% | 7.985 |
| EDENRED | +0.78% | 28.40 |
| ABIVAX | +0.92% | 109.80 |
| VIVENDI | +1.16% | 2.008 |
| CLARIANE | +1.26% | 4.016 |

## Volume anormal (> 2x la moyenne)

Moyenne des volumes sur les 25 actions : 258 177. Seuil (x2) : 516 354.

| Libelle | Volume | Cours |
|---|---|---|
| STELLANTIS | 2 406 011 | 5.18 |
| BUREAU VERITAS | 925 556 | 29.41 |
| TOTALENERGIES | 611 081 | 74.82 |

Export complet dans `analyse_bourse.csv`. Le sujet propose `sqlite3` en
ligne de commande avec `.mode csv` / `.output`, pas installe sur cette
machine -- reproduit en Python avec les modules `sqlite3` et `csv`, memes
requetes.

## Et dans la vraie actualite ?

**Sopra Steria** (+14.29% mesure ici, +14.9% rapporte en seance) :
resultats semestriels au-dessus des attentes (CA du S1 a 2.96 Md€, +4.1%
publie) et relevement de la prevision de croissance 2026, dans un
secteur recemment plombe par les avertissements d'acteurs americains.
[Sopra Steria bondit en Bourse apres avoir relevé sa prévision de
croissance pour 2026](https://www.abcbourse.com/marches/sopra-steria-bondit-en-bourse-apres-avoir-releve-sa-prevision-de-croissance-pour_700560)

**Alten** (+19.46% mesure ici) : plus surprenant, le CA du S1 est en
repli (-1.1% publie, -5.6% a perimetre constant, penalise par
l'automobile), mais la marge operationnelle et le cash-flow ressortent
meilleurs qu'attendu -- le marche a salue un "moins pire que redoute".
[Alten : malgre ses difficultes dans l'automobile, Alten degage une
rentabilite et un cash meilleurs qu'attendu et grimpe en Bourse -- BFM
Bourse](https://www.tradingsat.com/alten-FR0000071946/actualites/alten-malgre-ses-difficultes-dans-l-automobile-alten-degage-une-rentabilite-et-un-cash-meilleurs-qu-attendu-et-grimpe-en-bourse-1147206.html)

Les deux plus grosses hausses du jour viennent donc de publications de
resultats semestriels dans la tech/services, avec un marche qui reagit
plus a l'ecart avec les attentes qu'au niveau absolu du resultat.
