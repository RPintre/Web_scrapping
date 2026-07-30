# Defi 3 - Croiser veille et historique Wikipedia

## Article de depart

Dans `veille.db`, aucune mention n'a de `score_alerte` 1 ou 2 tel quel
(voir Defi 1 : les deux articles collectes etaient scores 0 par le
systeme original). Apres la recalibration du Defi 1, l'article
**"la SNCF annonce une greve surprise en Normandie avec un trafic
perturbe"** (BFMTV, 30/07/2026 09:56 UTC) passe a score 1. C'est celui
que je retiens ici.

## Historique Wikipedia de la SNCF

Attention : `SNCF` est une redirection. La vraie page (et son
historique) est *Societe nationale des chemins de fer francais*. Sur
les 50 dernieres revisions (jusqu'au 17 juillet 2026 inclus, donc
aucune dans les 13 jours precedant le crawl), **aucune ne mentionne la
greve du 30 juillet ni les resultats du 1er semestre 2026** annonces
par la presse ces derniers jours (voir `fiche_entite.json` du TD 4.2 :
articles 20 Minutes / franceinfo / Liberation du 28-29/07 sur "1,2
milliard d'euros de benefices au premier semestre"). Au moment du
crawl, ni l'un ni l'autre evenement n'a encore de trace dans
l'historique.

## Mais un cas comparable existe deja dans l'historique

En cherchant un edit du meme type (chiffres financiers) pour comparer,
je suis tombe sur la revision **233646130** (Teek36, 26 fevrier 2026,
resume *"Maj resultats financiers 2025 (infobox)"*) :

```
diff=prev&oldid=233646130
```

Le diff montre le passage, dans l'infobox :
- `chiffre d'affaires` : 41,8 Md€ (2023) -> 43,0 Md€ (2025)
- `resultat net` : 1,3 Md€ (2023) -> **1,8 Md€ (2025)**

... avec pour reference exacte un article du **Monde du meme jour**
(26/02/2026) : *"La SNCF enregistre un benefice net de 1,8 milliard
d'euros en 2025, cinquieme annee de resultats positifs d'affilee"*.
Autrement dit : la-dessus, Wikipedia a ete mis a jour **le jour meme**
de la publication du resultat annuel, avec une source de presse en
bonne et due forme.

## Conclusion : Wikipedia, source fiable pour la veille temps reel ?

Les deux constats se completent plus qu'ils ne se contredisent.
Wikipedia PEUT etre mis a jour tres vite quand un chiffre marquant
(resultat annuel) sort et qu'un contributeur motive s'en empare
(exemple du 26 fevrier, meme jour que la presse). Mais ce n'est ni
automatique ni garanti : les resultats du 1er semestre 2026, annonces
il y a deux jours au moment du crawl, n'y sont pas encore ; et une
greve regionale, meme relayee par plusieurs medias nationaux, n'a
quasiment aucune chance d'y apparaitre un jour (pas assez "encyclopedique"
face au filtre editorial des contributeurs).

**Non, Wikipedia n'est pas une source fiable pour la veille temps
reel.** C'est une source fiable pour verifier, a posteriori et avec un
delai variable (de "le jour meme" a "jamais"), qu'un evenement a
laisse une trace suffisamment notable pour un contributeur benevole --
ce qui en fait un bon complement de recoupement, pas un flux de
surveillance en soi.
