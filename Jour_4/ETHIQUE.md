# Ethique -- TP OSINT (Jour 4)

Trois questions pour chaque TD : ai-je le droit, est-ce personnel, suis-je discret.

## TD 4.1 -- Empreinte de domaine (doctolib.fr + ipssi.fr)

**Ai-je le droit ?** Oui. WHOIS, crt.sh et robots.txt sont des registres et
services publics faits pour etre interroges de l'exterieur -- aucune
authentification, aucun bypass. Je n'ai rien scrape derriere un login.

**Est-ce personnel ?** Non. Registrar, dates de creation/expiration du
domaine, serveurs DNS, headers HTTP, sous-domaines : ce sont des
donnees techniques d'infrastructure, pas des donnees a caractere
personnel au sens RGPD.

**Suis-je discret ?** User-Agent identifiable (`IPSSI-OSINT
(+r.pintre@gmail.com)`), `time.sleep(1)` avant chaque analyse, une
poignee de requetes par domaine (WHOIS, HEAD, robots.txt, crt.sh) --
rien qui ressemble a du bruteforce ou a un scan de ports.

## TD 4.2 -- Fiche entite (SNCF)

**Ai-je le droit ?** Oui. SIRENE (recherche-entreprises.api.gouv.fr)
est l'annuaire officiel des entreprises francaises, ouvert et sans cle.
Wikipedia est sous licence libre. Google News RSS est un flux public
concu pour etre agrege.

**Est-ce personnel ?** Non : SIREN, adresse du siege social (adresse
d'un etablissement, pas d'une personne), effectif en tranche, infobox
Wikipedia, titres de presse. Aucun nom de salarie autre que les
dirigeants deja publics (President-directeur general etc., deja dans
l'infobox Wikipedia elle-meme).

**Suis-je discret ?** `time.sleep(1)` entre les sources, une seule
requete par source, User-Agent identifiable. Le flux RSS Google News
n'est meme pas throttle par le site lui-meme (il est concu pour etre
interroge automatiquement).

## TD 4.3 -- Veille Scrapy (cible : SNCF)

**Ai-je le droit ?** Oui pour 4 flux sur 5 (`ROBOTSTXT_OBEY=True`,
Scrapy a bien recupere et respecte le robots.txt de chacun). Pour
lesechos.fr, la reponse est non applicable : le flux renvoie 403 avant
meme que la question de robots.txt se pose (voir README) -- le spider
ne contourne rien, il constate le blocage et log une erreur HTTP.

**Est-ce personnel ?** Non : titres et resumes d'articles de presse
deja publics, avec la source et l'URL d'origine. Aucune extraction de
commentaires ni de profils de lecteurs.

**Suis-je discret ?** `DOWNLOAD_DELAY=1.0` + `RANDOMIZE_DOWNLOAD_DELAY`,
`CONCURRENT_REQUESTS_PER_DOMAIN` par defaut (Scrapy = 8, mais un seul
flux par domaine ici de toute facon), User-Agent identifiable
(`IPSSI-OSINT-veille (+r.pintre@gmail.com)`). Un crawl complet ne fait
que 5 requetes RSS + 5 requetes robots.txt.

## Sur le cadre legal en general

Rien ici ne relevait de l'article 323-1 du code penal (acces frauduleux
a un STAD) : toutes les cibles sont des services publics ou des
contenus editoriaux sans aucune barriere d'acces contournee. La seule
base legale mobilisee est l'interet legitime (RGPD art. 6) pour une
veille documentee et proportionnee -- pas de profilage individuel, pas
de donnees sensibles.
