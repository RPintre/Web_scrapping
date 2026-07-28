# TP Jour 2 - Doctolib & Les Echos

Scripts Selenium pour le TD2.1 (Doctolib) et le TD2.2 (Les Echos).

Etat actuel de ce depot : **Doctolib fait**, Les Echos et les defis pas
encore commites (a venir dans de prochains commits).

## Installation

```bash
pip install selenium
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

## Headless vs normal

```bash
python doctolib_scraper.py --specialty dentiste --city paris --compare-headless --max-medecins 5
```

Chiffres reels obtenus (5 medecins, apres avoir corrige le piege du
User-Agent ci-dessus) :

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

## Screenshots

Capture d'echec automatique dans `screenshots/` quand la liste de
resultats ne charge pas (utile aussi bien pour un vrai changement de site
que pour les deux episodes de blocage ci-dessus).
