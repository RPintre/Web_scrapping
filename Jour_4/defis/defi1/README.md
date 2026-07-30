# Defi 1 - Calibrer le scoring de sentiment

## Ecart avec l'enonce

Le defi suppose un `mentions.csv` avec au moins 5 articles score=2 et 5
articles score=1 a relire. En pratique, le crawl reel de TD 4.3 (cible
SNCF, 5 flux RSS francophones, un seul passage) n'a remonte que **2
mentions**, toutes deux scorees **0 (neutre)** par le systeme de mots-cles
du sujet. Pas de quoi calculer un "taux de precision" au sens strict --
mais largement de quoi observer le probleme que le defi veut faire
toucher du doigt : lu a l'oeil, aucun des deux articles n'est neutre.

## Les 2 articles, relus pour de vrai

1. **Le Monde** -- *"Incendies dans le Sud-Ouest : la SNCF maintient
   jusqu'a dimanche l'annulation des TGV au sud de Bordeaux"*. Impact
   reel pour l'entreprise : negatif (service interrompu), meme si la
   cause (incendie) ne lui est pas imputable.
2. **BFMTV** -- *"la SNCF annonce une greve surprise en Normandie avec
   un trafic perturbe"*. Negatif sans ambiguite : greve, perturbation
   du service, voyageurs invites a reporter leur trajet.

Score original des deux : **0**. Ce sont donc deux faux negatifs a 100%
sur l'echantillon disponible -- pas un excellent point de depart pour
le systeme de scoring du sujet.

## Pourquoi le systeme original les rate

Ce n'est pas juste un manque de mots-cles : `MOTS_NEGATIFS` ne contient
ni "greve" ni "annulation" ni "perturbe", donc rien ne pouvait matcher.
Mais meme en ajoutant des mots, un piege plus profond guette : le
sujet ecrit `"condamne"`, `"benefice"` (sans accent) dans ses listes,
alors que le texte reel contient `"condamné"`, `"bénéfice"` (avec
accent) -- et la comparaison Python est un simple `in` sur des chaines
minuscules, sans normalisation Unicode. `"benefice" in "un bénéfice
record"` est **False**, silencieusement. Autrement dit, une bonne
partie des mots-cles du sujet ne peut deja pas matcher le francais
correctement accentue tel qu'il est ecrit dans la vraie presse.

## Recalibration testee (`recalibrer_scoring.py`)

Plutot que de relancer un crawl (qui donnerait un autre echantillon,
moins comparable), le script relit le `mentions.csv` deja produit et
recalcule le score avec une liste elargie -- **memes articles, seule la
calibration change** :

```
+3 negatifs : grève, annulation, perturbé
+3 positifs : bénéfice, résultat, hausse   (avec les accents corrects,
                                             cette fois)
```

Resultat :

| Article | Score v1 (sujet) | Score v2 (recalibre) |
|---|---|---|
| Incendies Sud-Ouest / annulation TGV | 0 | **1** |
| Greve surprise Normandie | 0 | **1** |

Les deux passent de faux-neutre a negatif correctement detecte.

## Conclusion

Sur cet echantillon (minuscule, il faut le dire honnetement), la
precision passe de 0/2 a 2/2 pour la detection du negatif. La vraie
lecon n'est pas "il manquait 3 mots" mais **l'absence de normalisation
des accents**, qui affecte silencieusement une bonne partie des mots
du sujet lui-meme (condamne/condamné, benefice/bénéfice...). Une vraie
correction en production ferait tourner `unicodedata.normalize("NFKD",
texte)` + suppression des accents des deux cotes de la comparaison,
pas seulement ajouter des mots un par un.
