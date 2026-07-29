# TP Jour 3 - Boursorama (TD 3.2)

Spider `cac` : recupere le palmares des actions sur
[boursorama.com/bourse/actions/palmares/france/](https://www.boursorama.com/bourse/actions/palmares/france/)
et stocke le resultat dans `bourse.db` (table `actions`, `isin` en
`UNIQUE`).

```bash
pip install scrapy
cd boursorama
scrapy crawl cac -L INFO
```

25 actions recuperees au dernier crawl, 0 erreur. En relancant le crawl
une deuxieme fois : toujours 25 lignes en base, la contrainte
`UNIQUE(isin)` fait son travail (`INSERT OR IGNORE`).

## Deux trucs pas comme prevu

Le sujet propose de cibler `table.c-table tr`, mais cette classe est
reutilisee par plusieurs tableaux sur la page, dont les indicateurs
hausse/baisse tout en haut qui n'ont rien a voir avec la liste d'actions.
Le vrai tableau du palmares a sa propre classe : `c-table-top-flop`.

Le sujet suggere de lire le code ISIN dans l'URL de la fiche
(`href.split("/")[-2]`). En verifiant dans `scrapy shell`, ce bout d'URL
(`1rPSOP`) est en fait le symbole interne de Boursorama, pas un code
ISIN. Le vrai ISIN (`FR0000050809` par exemple) n'apparait que sur la
fiche detail, dans `h2.c-faceplate__isin`. Le spider suit donc un lien de
plus vers chaque fiche pour l'aller chercher.

## Fichiers

- `items.py` : `ActionItem` (cours/volume/variation en types numeriques)
- `spiders/cac.py` : crawl en deux temps -- tableau puis fiche detail pour
  l'ISIN
- `pipelines.py` : `SQLitePipeline`, DDL du sujet, `INSERT OR IGNORE` pour
  les doublons
- `settings.py` : robots.txt, delai 1s, autothrottle, retry sur 5xx/429
