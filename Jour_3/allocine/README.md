# TP Jour 3 - AlloCiné (TD 3.1)

Spider Scrapy qui recupere le top 200 des meilleurs films sur
[allocine.fr/film/meilleurs/](https://www.allocine.fr/film/meilleurs/) :
titre, annee, realisateur, note presse, note spectateurs, url de la fiche.

## Lancer

```bash
pip install scrapy
cd allocine
scrapy crawl films -L INFO
```

Ca genere `films.json` et `films.csv` (voir `FEEDS` dans `settings.py`).
Crawl complet teste : 200/200 films recuperes, aucune erreur HTTP.

## Ou le pseudo-code du sujet ne marche plus

Avant d'ecrire le spider j'ai valide chaque selecteur dans `scrapy shell`,
comme demande, et plusieurs de ceux donnes en exemple dans le sujet sont
casses sur le site actuel.

`a.button--right` (le lien "page suivante") n'existe plus : la pagination
n'affiche que des numeros de page (`?page=N`). Le spider reconstruit donc
l'URL suivante lui-meme, jusqu'a la page 20 (200 films / 10 par page).

`h1::text` recupere "Titre de Realisateur", pas le titre tout seul.
Retirer le nom en suffixe marche presque tout le temps, sauf sur les
co-realisations ou le h1 n'en cite que deux sur trois (*Spider-Man: New
Generation*, 3 realisateurs credites, 2 dans le h1). Le titre est lu
depuis la balise `<meta property="og:title">`, plus simple.

`.meta-body-direction a::text` ne renvoie rien : le nom du realisateur
est dans un `<span>`, pas un lien. Et une fiche peut avoir deux blocs
`.meta-body-direction` (realisateur "De" + scenariste "Par") -- seul le
premier est garde.

`.meta-body-item strong::text` pour l'annee ne matche rien non plus (pas
de `<strong>` a cet endroit). L'annee est extraite par regex depuis la
date de sortie complete.

Pour les notes, `.stareval-note:last-child::text` suppose que la note
presse est toujours affichee avant celle du public. Faux des qu'un film
n'a pas de note presse (frequent) : le spider va chercher directement le
bloc portant le bon libelle ("Presse" ou "Spectateurs").

## Fichiers

- `items.py` : `FilmItem`
- `spiders/films.py` : crawl liste -> fiche detail
- `pipelines.py` : `CleanPipeline` (trim, cast annee/notes, jette l'item
  sans titre)
- `settings.py` : robots.txt respecte, delai 1s, autothrottle, retry sur
  5xx/429
