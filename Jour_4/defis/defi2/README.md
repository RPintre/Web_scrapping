# Defi 2 - OSINT sur un domaine que je connais (ipssi.fr)

`python td41_domaine.py ipssi.fr` -> [`rapport_ipssi.fr.json`](rapport_ipssi.fr.json)
(copie du rapport genere a la racine du TP).

## Ce qui surprend dans le rapport

Pas le nombre de sous-domaines -- il y en a **zero** trouves via
crt.sh, ce qui en soi n'est pas anodin (voir plus bas). La vraie
surprise, c'est l'etat du site au moment du crawl :

- **Statut HTTP 503** sur la page d'accueil ("Service Temporarily
  Unavailable", serveur nginx).
- **Certificat TLS invalide** : `certificat_tls_valide: false`. En
  testant a la main avec curl, l'erreur precise est `SEC_E_WRONG_PRINCIPAL`
  -- le certificat presente ne correspond pas au nom `ipssi.fr` demande.
  Autrement dit, soit un certificat expire/mal configure, soit un
  vhost par defaut qui repond a la place du bon.
- `robots.txt` renvoie du coup un `HTTP 400`, consequence du meme
  probleme cote serveur plutot qu'un blocage delibere.

## Combien de sous-domaines je ne connaissais pas ?

Zero trouves, donc zero surprise de ce cote -- mais **ce zero est
lui-meme a interpreter avec prudence**, pas comme un signal de securite
positif. crt.sh a fini par repondre correctement (`[]`) apres plusieurs
timeouts/502 lors des tests (le service est notoirement instable, voir
le README principal) ; un vrai audit ne conclurait "aucun sous-domaine
expose" qu'apres avoir croise avec au moins une deuxieme source
(brute-force DNS passif, Shodan, etc.), pas sur une seule requete a un
service gratuit connu pour timeouter.

## Le serveur est-il identifiable ? Utile pour un attaquant ?

Oui : `Server: nginx`, sans version precise ceci dit (pas de `nginx/1.x.y`
dans le header retourne). Un attaquant apprend "c'est du nginx", ce qui
oriente deja le choix des CVE a tester en priorite plutot que d'essayer
a l'aveugle sur tous les serveurs web existants -- mais sans le numero
de version, il devrait encore le fingerprinter autrement (comportement
sur des requetes malformees, headers optionnels, etc.).

## Sous-domaines de preprod/staging exposes ?

Aucun trouve ici (le crt.sh est revenu vide), donc pas de reponse
positive a verifier sur ce domaine precis. Le risque generique existe
neanmoins et vaut la peine d'etre garde en tete : un sous-domaine
`staging.` ou `preprod.` avec le meme code que la prod mais sans les
protections (WAF, rate-limiting, donnees de test parfois copiees
depuis la prod) est une des decouvertes crt.sh les plus frequentes en
pratique -- juste pas ici.

## Ce qu'un auditeur externe apprendrait en 5 minutes sur ipssi.fr

En cinq minutes de requetes 100% publiques, un auditeur verrait que le
site principal renvoie une erreur 503 avec un certificat TLS qui ne
correspond pas au nom de domaine demande -- un signe clair d'une
infrastructure web mal maintenue ou en cours de migration, plutot qu'un
probleme de securite applicative a proprement parler. Le WHOIS est
propre (domaine enregistre chez un registrar francais classique,
expiration lointaine en 2027, DNS chez le meme hebergeur AMEN), et
aucun sous-domaine oublie n'a ete detecte via crt.sh. Le verdict en 5
minutes serait donc : "l'exposition externe semble limitee, mais le
site public a un probleme operationnel/TLS actif au moment de
l'audit, a signaler en priorite avant de chercher plus loin."
