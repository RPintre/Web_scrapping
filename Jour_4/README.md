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
