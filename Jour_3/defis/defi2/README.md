# Defi 2 - CONCURRENT_REQUESTS, ca change quoi ?

Benchmark sur le spider `films`, limite a 100 films
(`CLOSESPIDER_ITEMCOUNT=100`) pour ne pas abuser du site. Logs bruts dans
`logs/`, donnees dans `resultats.csv`.

## Le premier essai n'a rien montre

En changeant juste `-s CONCURRENT_REQUESTS` entre 1 et 4, le temps ne
bougeait quasiment pas : 150.8s contre 149.2s (`logs/bench_c1.log` /
`bench_c4.log`). En y reflechissant : le spider fixe `DOWNLOAD_DELAY =
1.0` dans son `custom_settings`, et `settings.py` active
`AUTOTHROTTLE_ENABLED`. L'un des deux imposait de toute facon ~1
requete/seconde, peu importe le nombre de connexions ouvertes en
parallele. Une option `-s` en ligne de commande a bien priorite sur
`custom_settings`, mais je n'avais desactive ni le delai ni
l'autothrottle -- juste change la limite de concurrence.

Reessaye en neutralisant les deux explicitement :

```
-s AUTOTHROTTLE_ENABLED=False -s DOWNLOAD_DELAY=0 -s CONCURRENT_REQUESTS=N -s CONCURRENT_REQUESTS_PER_DOMAIN=N
```

## Resultats

| Mode | CONCURRENT_REQUESTS | Temps | Items | Items/s |
|---|---|---|---|---|
| throttle projet (1 req/s impose) | 1 | 150.8s | 101 | 0.67 |
| throttle projet (1 req/s impose) | 4 | 149.2s | 104 | 0.70 |
| brut (pas de delai) | 1 | 7.57s | 103 | 13.61 |
| brut (pas de delai) | 4 | 5.01s | 107 | 21.35 |
| brut (pas de delai) | 8 | 5.15s | 107 | 20.76 |
| brut (pas de delai) | 16 | 5.26s | 110 | 20.90 |

A partir de 4, le gain devient negligeable : le temps passe de 7.57s
(N=1) a 5.01s (N=4), puis stagne a 8 et 16 (5.15s, 5.26s). Un seul
domaine cible (allocine.fr) plafonne le debit avant meme d'atteindre 8
connexions -- la latence reseau/serveur devient le facteur limitant, pas
le nombre de requetes ouvertes cote client.

Pourquoi l'autothrottle peut battre une valeur fixe elevee : au-dela du
point de plafonnement, ouvrir plus de connexions n'accelere rien et
augmente le risque de 429/503 sur un site moins tolerant qu'allocine.fr,
donc des retries qui ralentissent tout au final. L'autothrottle ajuste le
delai a partir du temps de reponse mesure, il ne pousse jamais plus que
ce que le serveur absorbe. Le vrai crawl de 200 films (TD 3.1) tourne
4-5 minutes sans un seul retry avec ce reglage.

## Le ratio item/response

Ici il tourne entre 0.83 et 0.89. C'est normal : les pages de liste (10
films chacune) comptent comme des reponses mais ne produisent aucun item
elles-memes, seulement des requetes de suivi -- le ratio ne peut donc pas
atteindre 1.0 sur ce spider.

Un ratio en dessous de 0.5 serait un signal different : soit le
`CleanPipeline` jette une grosse partie des items (titre manquant, donc
selecteur casse), soit une bonne partie des reponses sont des erreurs
retentees sans jamais produire d'item. Dans les deux cas ca voudrait dire
revalider les selecteurs avant de relancer un crawl complet.
