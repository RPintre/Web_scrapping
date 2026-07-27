# Defi 1 - Selecteurs CSS : jeuxvideo.com

Site choisi : **jeuxvideo.com** (actualites jeux video), page cible
`https://www.jeuxvideo.com/actualites.htm`.

Domaine different du Blog du Moderateur (jeux video vs tech-business) et
structure HTML differente : theme Bootstrap avec des `div.card`, pas de
balise `<article>`, pas de `time[datetime]`.

Verification prealable : `robots.txt` de jeuxvideo.com autorise
`User-agent: *` sur `/actualites.htm` (seuls `/abonnements/`,
`/administration/`, `/rss/`, etc. sont exclus).

## Selecteurs identifies (DevTools)

| Champ      | Selecteur CSS                    | Extraction                                   |
|------------|-----------------------------------|-----------------------------------------------|
| carte      | `div.card`                        | conteneur d'un article de la liste            |
| titre      | `h3.card-title a`                 | `.get_text(strip=True)`                       |
| url        | `h3.card-title a`                 | `['href']` (relative, `/news/...`) + prefixe `https://www.jeuxvideo.com` |
| date       | `.card__textMuted`                | `.get_text(strip=True)` -> texte relatif ("Il y a 5 heures") |
| categorie  | `.card__contentType`              | `.get_text(strip=True)` (ex: "News jeu")      |

## Reflexion (3 phrases)

Plus simple : pas de pagination complexe a gerer pour un extrait de 20
articles, une seule page suffit, et les classes CSS (`.card-title`,
`.card__contentType`) sont explicites et faciles a reperer dans
DevTools. Plus difficile : contrairement au Blog du Moderateur qui expose
une date ISO exploitable via `time[datetime]`, jeuxvideo.com n'affiche
qu'une date relative en texte ("Il y a 5 heures"), qu'il faudrait
parser/normaliser soi-meme pour un usage fiable (pas de balise `<time>`
du tout sur la page). Le selecteur du titre est du meme type structurel
(un texte de titre dans un heading `h3` avec un lien `<a>` a l'interieur,
comme `h3.entry-title`/`header.entry-header a` sur le Blog du Moderateur)
meme si les classes CSS sont evidemment specifiques a chaque theme.
