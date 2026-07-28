# Defi 3 - robustesse face aux changements de site

## Ce qui est deja fait

Le pattern fallback demande dans le sujet (essayer un selecteur, puis un
autre, puis "n/a") est deja dans les deux scrapers, pas juste ecrit ici a
part :

- `doctolib_scraper.py` : `NAME_SELECTORS`, `ADDRESS_SELECTORS`,
  `SLOT_SELECTORS`, `CONSULTATION_MODE_SELECTORS` sont des listes
  essayees dans l'ordre par `first_text()`. `CARD_SELECTORS` fait pareil
  pour la carte elle-meme (l'attribut du sujet + un repli si Doctolib le
  change).
- `lesechos_scraper.py` : meme logique sur `ARTICLE_SELECTOR`,
  `TITLE_SELECTORS`, etc.

Si rien ne matche, le champ tombe sur "n/a" au lieu de faire planter tout
le run.

## Ce qui reste a faire dans 3 jours

Le sujet demande de relancer le scraper 3 jours plus tard sans y toucher
et de regarder ce qui casse. Ca ne se simule pas, ca depend de si Doctolib
change vraiment un truc entre-temps. `snapshot_diff.py` sert a
automatiser cette comparaison :

```bash
# depuis defis/defi3 -- attention, --output est relatif au dossier du
# script (doctolib_scraper.py), pas au dossier courant : le fichier
# atterrit donc dans Jour_2/, il faut le deplacer ici ensuite
python ../../doctolib_scraper.py --specialty cardiologue --city lyon --output j0.json
mv ../../j0.json .

# 3 jours plus tard, sans toucher au code
python ../../doctolib_scraper.py --specialty cardiologue --city lyon --output j3.json
mv ../../j3.json .

python snapshot_diff.py j0.json j3.json
```

`j0.json` deja genere le 28/07/2026 (10 medecins, cardiologue/lyon). Il
compare les deux JSON et dit quels champs sont passes a "n/a" entre les
deux (= selecteur casse). Reste a relancer pour de vrai dans 3 jours
(31/07/2026) et noter le resultat ici.

## Ce que j'ai deja observe a J0

Pendant que j'ecrivais le scraper, j'ai eu une `RuntimeError("Resultats
non charges...")` -- mais pas a cause d'un selecteur casse : la page
recue etait un "Retry later" du WAF de Doctolib (capture dans
screenshots/), pas la vraie page de resultats. C'est deja un exemple du
principe du defi : le meme `try/except` qui protege contre un selecteur
casse protege aussi contre ce genre de reponse inattendue, et le
screenshot m'a permis de voir tout de suite que ce n'etait pas un
probleme de code.
