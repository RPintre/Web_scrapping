# Defi 1 - un site local : actu.fr

J'ai choisi actu.fr, edition Ile-de-France
([actu.fr/ile-de-france](https://actu.fr/ile-de-france/)) : presse
locale, une seule page suffit largement (~45 cartes d'articles, le sujet
en demande 20 minimum).

```bash
cd actu_local
scrapy shell "https://actu.fr/ile-de-france/"
scrapy crawl actu -L INFO
```

-> `articles.csv` (titre, lien, publication). Sur les 45 cartes de la
page, 31 ont ete gardees -- les 14 autres n'avaient pas de titre
exploitable, voir plus bas.

Item a 3 champs (`ArticleItem` : titre, lien, publication) + un
`CleanPipeline` qui trim les textes, corrige les liens casses (voir plus
bas), et jette l'item si le titre ou le lien manque.

## Ce qui a pose probleme

Premier essai avec un selecteur `a h1::text` : ca ne recuperait que 9
titres sur 45. En regardant le HTML de plus pres, le site utilise 3
gabarits de carte differents selon leur emplacement sur la page, et le
titre se retrouve tantot dans un h1, tantot un h2, tantot un h3. Corrige
en elargissant le selecteur aux trois.

Deuxieme surprise : une partie des liens sont litteralement doubles par
le site lui-meme (`https://actu.fr/https:/actu.fr/...`). Ca vient du
CMS, pas d'une erreur de parsing de mon cote, donc ca se corrige en
pipeline plutot qu'au niveau du selecteur.

## Comparaison avec AlloCine (les 5 lignes demandees par le sujet)

1. AlloCine a une seule carte film stable ; actu.fr en a 3 differentes
   selon la position de la carte sur la page.
2. AlloCine ne genere pas de liens casses ; actu.fr oui, sur pres de 2
   cartes sur 3 ici.
3. actu.fr melange dans le meme flux de vraies cartes article et des
   widgets (pubs, "articles les plus lus") qui partagent la classe CSS
   sans le meme contenu -- source des 14 items ignores.
4. Pas besoin de suivre un lien vers une fiche detail ici, tout est deja
   sur la page de liste, contrairement au crawl a deux niveaux
   d'AlloCine.
5. Plus une structure de site est heterogene, plus valider dans `scrapy
   shell` avant de coder devient indispensable -- c'est net sur actu.fr
   compare a AlloCine.
