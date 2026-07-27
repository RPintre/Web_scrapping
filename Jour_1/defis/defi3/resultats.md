# Defi 3 - Benchmark honnete du throttling

Mesures reelles (`python benchmark.py`, machine + connexion du poste de
dev, `blogdumoderateur.com/articles/page/N/`, un seul run, hors delai
applique apres la derniere page) :

```
# Pages | 0.5 s | 1.0 s | 2.0 s
#    2   | 0.8s  | 1.2s  | 2.3s
#    5   | 2.6s  | 4.7s  | 8.6s
#   10   | 5.7s  | 10.3s | 19.3s
```

Temps de requete pur (hors sleep), deduit des mesures : environ
**0.12-0.13 s/requete** sur ce site (serveur rapide, bonne connexion) -
la duree totale est donc dominee presque entierement par le `DELAY`
choisi, pas par le reseau.

## Au-dela de quel delai le scraping de 200 articles depasse 30 min ?

200 articles / 15 par page (structure `/articles/`) = 14 pages, soit
13 delais entre requetes. Avec un temps de requete pur de ~0.13 s :

```
temps_total ~= 13 * DELAY + 14 * 0.13
1800 s (30 min) = 13 * DELAY + 1.8
DELAY ~= (1800 - 1.8) / 13 ~= 138 s (~2 min 18 s)
```

Il faudrait un delai extreme (>= ~2 min entre chaque page) pour que le
scraping de 200 articles depasse 30 minutes. Avec des valeurs realistes
(0.5 a 5 s), on reste toujours tres largement sous ce seuil.

## Pour respecter une politique < 1 req/2 s, combien d'heures pour 500 articles ?

Deux lectures possibles selon la granularite des requetes :

- **Requetes de listing uniquement** (comme ce scraper, 15 articles par
  requete) : 500 articles ~= 34 pages ~= 33 delais de 2 s + temps de
  requete ~= 33*2 + 34*0.13 ~= **70 s (~1 min 10 s)**. Tres rapide car
  une seule requete ramene beaucoup d'articles a la fois.
- **Une requete par article** (si on doit ouvrir chaque page d'article
  individuellement, ex. pour recuperer le corps complet du texte) :
  500 requetes * 2 s ~= 1000 s ~= **~16-17 minutes**, toujours en dessous
  d'une heure mais nettement plus lent que la version "listing".

Dans les deux cas, respecter `< 1 req/2 s` reste largement compatible
avec une duree raisonnable pour ce volume ; le facteur limitant n'est
jamais le reseau mais le nombre de requetes HTTP necessaires.

## Conclusion : quel compromis vitesse/discretion en production ?

Vu que le temps reseau reel est negligeable (~0.13 s/requete) face a
n'importe quel `DELAY` politique (0.5 a 2 s), il n'y a aucune raison de
sacrifier la discretion pour la vitesse sur ce volume d'articles : le
gain de temps entre `DELAY=0.5s` et `DELAY=2s` reste de l'ordre de la
dizaine de secondes sur 200 articles, contre un risque de charge/429
beaucoup plus eleve cote serveur avec un delai agressif. En production,
je garderais un `DELAY` proche de 1.5-2 s (comme dans `scraper_bdm.py`),
avec respect strict des `Retry-After` sur 429 et backoff exponentiel sur
5xx : la marge de securite est quasi gratuite en temps, donc autant la
prendre.
