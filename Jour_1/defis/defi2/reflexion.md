# Defi 2 - Detecter les nouveautes entre deux crawls

## Crawls reels effectues

- Crawl A : `crawl_A_20260727_1157.csv` (30 derniers articles, 11:57)
- Crawl B : `crawl_B_20260727_1207.csv` (30 derniers articles, 12:07)
- Ecart reel : **10 minutes** (le sujet suggere 2h/2 jours ; 10 min a
  ete choisi pour produire un resultat observable dans la duree de la
  session, cf. limite ci-dessous).

## Resultat du diff (`python diff_scrapes.py crawl_A_...csv crawl_B_...csv`)

```
Nouveaux : 0
Disparus : 0
Stables  : 30
```

Aucun changement en 10 minutes : les 30 memes articles sont presents
dans les deux crawls. C'est un resultat honnete, pas un echec du script
— voir l'estimation de debit ci-dessous, qui montre que c'est attendu.

## Combien d'articles nouveaux apparaissent en 24h sur ce site ?

Plutot que d'extrapoler depuis une fenetre de 10 minutes (trop courte
pour etre fiable), le debit reel a ete mesure sur les 200 derniers
articles collectes :

```
plus ancien article : 2026-06-02 09:55
plus recent article : 2026-07-27 11:04
span                : 55 jours, ~1h
debit moyen         : ~0.15 article/heure
estimation 24h       : ~4 articles/jour
```

Avec ~4 articles/jour (~1 toutes les 6h en moyenne), il est parfaitement
normal de ne voir aucune nouveaute sur une fenetre de 10 minutes. Le diff a 0/0/30 confirme la mesure, il
ne l'infirme pas.

## Quel intervalle de crawl garantit de ne manquer aucune publication sans depasser 1 crawl/heure ?

La contrainte impose au plus 1 crawl/heure. Avec un debit mesure de
~4 articles/24h (~1 toutes les 6h), un crawl **toutes les heures**
(frequence maximale autorisee par la contrainte) laisse une marge tres
confortable : en moyenne <1 nouvel article par intervalle, tres loin des
30 articles que chaque crawl recupere par defaut (fenetre tampon large).
Meme en cas de pic de publication (plusieurs articles en rafale), il
faudrait plus de 30 nouveaux articles en une heure pour qu'un crawl
horaire en manque un — un scenario tres improbable au vu du debit
observe. Conclusion : **1 crawl/heure** (la limite haute autorisee)
suffit largement ; on pourrait meme espacer davantage sans risque reel,
mais rester a la limite autorisee maximise la fraicheur des donnees sans
solliciter le serveur plus que necessaire.

## Validation synthetique du mecanisme

Le crawl reel n'ayant produit aucun changement (cf. debit mesure
ci-dessus), un test synthetique a ete fait pour prouver que
`diff_scrapes.py` detecte correctement un changement quand il y en a
un : `crawl_C_test_synthetique.csv` = copie de `crawl_B` avec un
article retire et un faux article ajoute.

```
python diff_scrapes.py crawl_B_20260727_1207.csv crawl_C_test_synthetique.csv

Nouveaux : 1
Disparus : 1
Stables  : 29
  [+] https://www.blogdumoderateur.com/test-validation-diff-fictif/
  [-] https://www.blogdumoderateur.com/google-3-nouveautes-ia/
```

Le mecanisme fonctionne comme attendu : le resultat "0 nouveaux / 0
disparus" observe entre les crawls A et B reels est donc bien le reflet
du faible debit de publication du site, pas d'un defaut du script.

## Limite de la methode

Un ecart de 10 minutes reste trop court pour observer un vrai cycle de
publication ; l'estimation de debit fiable vient ici de l'historique des
200 derniers articles (span de 55 jours), pas du diff a 10 minutes
lui-meme. Pour une mesure rigoureuse du debit sur 24h glissantes, il
faudrait relancer `crawl.py` a intervalles reguliers pendant une vraie
journee.
