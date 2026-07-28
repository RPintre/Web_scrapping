# TP Jour 2 - Doctolib & Les Echos

Scripts Selenium pour le TD2.1 (Doctolib) et le TD2.2 (Les Echos).

## Installation

```bash
pip install selenium requests beautifulsoup4 lxml
```

## Doctolib

```bash
python doctolib_scraper.py --specialty cardiologue --city lyon
python doctolib_scraper.py --specialty dentiste --city paris --headless --max-medecins 10
python doctolib_scraper.py --specialty dentiste --city paris --seulement-disponibles --max-medecins 5
python doctolib_scraper.py --specialty dentiste --city paris --compare-headless --max-medecins 5
```

Recupere les fiches de la premiere page de resultats (nom+specialite,
adresse, type de consultation, 3 premiers creneaux, url) -> `doctolib.json`.

`--seulement-disponibles` ne garde que les medecins qui ont au moins un
creneau reel (beaucoup n'ont aucune dispo en ligne, il faut souvent en
scanner pas mal pour en trouver 5 -- le script scrolle plus loin dans ce
cas). `--debug` affiche le HTML autour d'une carte quand un champ n'est
pas trouve, pratique pour corriger un selecteur casse.

### Pieges rencontres

Le `data-test='search-result-card'` donne dans le sujet ne matche plus
rien sur les pages actuelles de Doctolib -- le script se rabat alors sur
le lien vers la fiche du praticien (`a[href*='/specialite/ville/']`), qui
marche toujours. A partir de ce lien il faut remonter deux niveaux dans le
DOM pour retrouver la carte complete : le nom/adresse est dans une colonne
a gauche, et la zone de creneaux (`data-test-id='availabilities-
container'`) est une colonne soeur a droite, pas un enfant de la premiere.

Autre piege : certains `<h2>` du nom sont la pour le SEO mais Selenium les
juge "non visibles" (`.text` renvoie vide) -- le script lit `textContent`
a la place, en ne gardant que les noeuds texte directs pour ne pas
recuperer au passage du texte cache reserve aux lecteurs d'ecran (ex :
"Consultation video disponible" colle au nom).

Dernier piege, plus vicieux : `--headless` seul, teste a froid (sans
aucune requete avant), renvoyait systematiquement une page "Retry later"
-- alors que le mode normal marchait toujours. Rien a voir avec un
rate-limit d'enchainement : meme en `--headless=new`, Chrome garde
"HeadlessChrome" dans son User-Agent, et Doctolib bloque dessus. Le script
force donc un User-Agent de Chrome normal en headless (meme version que
le Chrome installe, pour rester coherent avec les Client Hints envoyes en
parallele).

## Les Echos

```bash
python lesechos_scraper.py --check-requests-only
python lesechos_scraper.py --max-articles 20
python lesechos_scraper.py --compare-headless --max-articles 10
```

-> `lesechos.json` (titre, rubrique, chapeau, heure_publi, premium, + url
en bonus pour verifier).

Les cartes de la une (balise `<article>`) ne contiennent que le titre, la
rubrique (lien `[data-testid='hubpage-links']`) et le badge premium
(`[data-testid='subscribe-badge']`) -- verifie en dumpant le HTML complet
via `--debug`, rien de tel que chapeau ou heure dans leur markup. Le
script visite donc en plus la page de chaque article (2e passe, delai
aleatoire entre les visites) pour lire la meta description (`<meta
name="description">`) comme chapeau -- forcement visible sans abonnement
puisque c'est le texte utilise pour le referencement -- et l'heure via
`<time datetime="...">` ou la meta `article:published_time` a defaut.
Dedoublonnage par URL au passage (Les Echos affiche parfois 2 cartes-titre
pour la meme actu).

Meme piege User-Agent que sur Doctolib : `--headless` seul renvoyait une
page "Access Denied" Akamai (voir plus bas), corrige de la meme facon en
forcant un User-Agent de Chrome normal en headless.

## Pourquoi Selenium et pas requests seul

Teste avec `requests` en premier, comme demande dans le sujet (etape 1 du
TD2.2, via `--check-requests-only`) :

```
GET https://www.lesechos.fr -> HTTP 403, 0 balise de titre trouvee
```

Le 403 renvoie une page "Access Denied" avec une reference
`errors.edgesuite.net` -- donc Akamai bloque directement au niveau du CDN,
avant meme d'atteindre le site. Pas la peine d'insister avec requests, il
faut un vrai navigateur.

## Deux blocages rencontres en developpant, meme cause

- doctolib.fr en `--headless` : "Retry later" systematique, meme a froid.
- lesechos.fr en `--headless` : "Access Denied" Akamai systematique, meme
  a froid (capture dans `screenshots/`).

Meme cause dans les deux cas : Chrome garde "HeadlessChrome" dans son
User-Agent meme en `--headless=new`, et les deux sites bloquent dessus.
Les deux scripts forcent maintenant un User-Agent de Chrome normal en
headless -- les deux modes fonctionnent depuis.

## Headless vs normal

```bash
python doctolib_scraper.py --specialty dentiste --city paris --compare-headless --max-medecins 5
python lesechos_scraper.py --compare-headless --max-articles 10
```

Chiffres reels obtenus sur Doctolib (5 medecins, apres avoir corrige le
piege du User-Agent ci-dessus) :

| Mode     | Duree  |
|----------|--------|
| normal   | 53.2s  |
| headless | 53.1s  |

Gain ~1.0x : quasiment aucune difference. Ca s'explique par le fait que ce
script passe le plus clair de son temps en attentes explicites
(`WebDriverWait`, scroll avec pauses de 1.5s) et en latence reseau vers
Doctolib, pas en rendu graphique -- desactiver le rendu (headless) n'a
donc presque rien a gagner ici. Le gain habituellement annonce (~2-3x)
vient surtout du cout du compositing sur des pages tres lourdes visuellement
ou des scrapes avec beaucoup moins d'attentes fixes.

Meme constat sur Les Echos (10 articles, apres le meme fix User-Agent) :

| Mode     | Duree  |
|----------|--------|
| normal   | 33.9s  |
| headless | 36.3s  |

Gain ~0.9x -- headless est meme legerement plus lent ici (dans le bruit
de mesure du reseau). Meme explication : le script est domine par les 2
passes (une par une + une visite par article avec delai aleatoire de
1.5 a 3s), pas par le rendu graphique.

## Screenshots

Au moins une capture d'echec par cible dans `screenshots/`, generee
automatiquement quand la page attendue ne charge pas.
