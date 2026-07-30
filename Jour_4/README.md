# TP Jour 4 - OSINT

Trois TD sur le meme theme : re-utiliser requests/BS4/Scrapy pour du
renseignement en sources ouvertes, cadre legal strict (voir
[ETHIQUE.md](ETHIQUE.md)).

## TD 4.1 - Empreinte de domaine

```bash
pip install requests python-whois
python td41_domaine.py doctolib.fr
python td41_domaine.py ipssi.fr
```

-> `rapport_<domaine>.json` (WHOIS, headers HTTP, sous-domaines
crt.sh, robots.txt).

Cible principale : **doctolib.fr** (cloudflare, CSP + HSTS presents,
WHOIS propre). Deuxieme cible pour le Defi 2 : **ipssi.fr**, mon ecole
-- voir plus bas, le resultat est plus interessant que prevu.

### crt.sh est franchement instable

Sur les deux domaines testes, `crt.sh` a renvoye tour a tour un
timeout, un 502 et un 404 avant de repondre correctement -- pas une
fois de suite pareil. Le script retente une fois avec un timeout large
(45s) et remonte l'erreur telle quelle plutot que de la masquer.
`rapport_doctolib.fr.json` contient d'ailleurs l'un de ces echecs
(502 Bad Gateway) au lieu d'une vraie liste de sous-domaines -- pas un
bug du script, juste ce service public gratuit qui craque des qu'un
domaine a beaucoup de certificats historiques.

### ipssi.fr : le certificat ne correspond pas au domaine

Verifie en direct : `https://ipssi.fr` renvoie un **503** avec un
**certificat TLS invalide** (`SEC_E_WRONG_PRINCIPAL` avec curl -- le
certificat presente n'est pas celui du domaine demande). Le script
gerait deja les erreurs SSL du sujet par un `except Exception`, mais
ca les passait sous silence ; je l'ai modifie pour retenter en
`verify=False` et **signaler** `certificat_tls_valide: false` dans le
rapport plutot que de planter -- un certificat casse est en soi une
info d'exposition, pas juste un obstacle technique a contourner.

## TD 4.2 - Fiche entite

```bash
pip install requests feedparser beautifulsoup4 lxml
python td42_entite.py SNCF
```

-> `fiche_entite.json` (SIREN, infobox + intro Wikipedia, 10 derniers
articles de presse via Google News RSS).

### L'URL SIRENE du sujet ne resout plus

`api.annuaire-entreprises.data.gouv.fr` (celle du sujet) est en
NXDOMAIN. L'API officielle actuelle est
`recherche-entreprises.api.gouv.fr`, dont le schema JSON differe aussi
un peu : `activite_principale` et `tranche_effectif_salarie` sont sous
la cle `siege`, pas a la racine du resultat comme le code du sujet le
suppose. Le script est adapte en consequence.

Autre detail utile : chercher juste "SNCF" fait remonter en premier
resultat la bonne entite (`SOCIETE NATIONALE SNCF`, SIREN 552049447),
qui correspond bien au SIREN affiche dans l'infobox Wikipedia -- une
petite verification croisee gratuite, pratique pour confirmer qu'on
cible la bonne structure juridique (le nom d'usage d'une entreprise
recouvre souvent plusieurs entites SIRENE distinctes, une maison mere
et ses filiales).

## TD 4.3 - Veille Scrapy

```bash
cd veille
scrapy crawl rss_spider -L INFO
```

-> `veille/mentions.csv` + `veille/veille.db` (table `mentions`,
`UNIQUE(url)`, `score_alerte`).

Cible : **SNCF**. Le sujet propose 5 flux "une" generalistes -- teste
en pratique, ils ne remontent quasiment jamais une entreprise precise
(0 mention SNCF sur les 4 flux qui repondent, un run complet). Les
rubriques **Economie** des memes medias captent bien mieux ce genre de
veille (3-4 mentions SNCF au meme instant contre 0 sur les flux
generalistes), donc j'ai swap les flux "une" contre leurs equivalents
Economie -- toujours 5 flux de medias francophones, juste mieux
cibles pour l'usage reel du TD. Les Echos garde son flux "une" du
sujet a titre de temoin : il **403** systematiquement, meme constat
Akamai que sur le TD Les Echos du Jour 2.

Resultat d'un crawl : 2 mentions, toutes deux scorees **0 (neutre)**
par le systeme de mots-cles du sujet -- alors qu'a la lecture, les deux
articles sont clairement negatifs (greve, trains annules). Voir
[defis/defi1](defis/defi1/README.md) pour pourquoi, et comment la
recalibration corrige les deux scores.

## Defis autonomes

- [defi1](defis/defi1/README.md) : pourquoi le scoring original rate
  les 2 seules mentions collectees, et un bug plus profond (pas de
  normalisation des accents) derriere ce raté.
- [defi2](defis/defi2/README.md) : OSINT sur ipssi.fr -- certificat
  TLS casse, 503, zero sous-domaine trouve.
- [defi3](defis/defi3/README.md) : croisement veille/Wikipedia --
  un vrai edit Wikipedia du jour meme retrouve pour les resultats
  annuels 2025, mais rien encore pour la greve ou les resultats du
  1er semestre 2026 au moment du crawl.
