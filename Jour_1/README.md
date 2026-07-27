# TP - Veille technologique automatisee (Blog du Moderateur)

Scraper `scraper_bdm.py` qui collecte les derniers articles du Blog du
Moderateur (titre, url, date, categorie, chapeau) et les persiste en
CSV UTF-8 (`articles.csv`) et SQLite (`articles.db`, table `articles`,
dedoublonnage via `INSERT OR IGNORE` sur `url UNIQUE`).

## Usage

```bash
pip install requests beautifulsoup4
python scraper_bdm.py --max 200 --csv articles.csv --db articles.db
```

## 1.1 - robots.txt : le scraping de `/feed/` est-il autorise ?

Non. `https://www.blogdumoderateur.com/robots.txt` contient, pour
`User-agent: *` :

```
Disallow: /feed/
Disallow: /*/feed/
```

`/feed/` est donc explicitement interdit au crawl pour tout robot
generique. Ce script ne touche jamais `/feed/` : il ne cible que
`/articles/` et `/articles/page/N/`, chemins absents de la liste des
`Disallow` pour `User-agent: *`.

## 3 questions ethiques

**1. Ai-je le droit ?**
Oui pour les chemins scrapes (`/articles/`, `/articles/page/N/`) : ils
ne figurent pas dans les `Disallow` de `robots.txt` pour `User-agent: *`.
Les CGU du site couvrent la consultation de contenus editoriaux publics ;
l'usage ici est strictement educatif (TP IPSSI), non commercial, sans
republication du contenu. Le scraping de donnees publiques a des fins
educatives est admis dans l'UE (CJUE, arret Ryanair 2021) sous reserve
de respecter robots.txt, la non-collecte de donnees personnelles et la
discretion du crawl - les 3 conditions ci-dessous.

**2. Est-ce personnel ?**
Non. Les 5 champs collectes (titre, url, date, categorie, chapeau) sont
des metadonnees editoriales publiques rattachees a des articles, pas a
des personnes physiques identifiees. Aucune donnee de compte, email,
commentaire ou profil utilisateur n'est extraite.

**3. Suis-je discret ?**
Oui :
- `User-Agent` identifiable et honnete : `IPSSI-scraper (+contact@ipssi.fr)`
  (le vrai User-Agent envoye, pas un usurpation de navigateur).
- Throttling : `time.sleep(1.5)` entre chaque requete de pagination
  (dans la fourchette 1-2 s demandee).
- Retry respectueux : sur `429 Too Many Requests`, le script attend la
  duree indiquee par l'en-tete `Retry-After` (ou 10 s par defaut) avant
  de reessayer ; sur erreurs `5xx`/timeout, backoff exponentiel
  (`2**tentative`), 3 tentatives max, puis abandon propre de la page
  sans bombarder le serveur.

## Note sur les selecteurs

Les selecteurs CSS "officiels" fournis dans le sujet du TD
(`h2.post-title a`, `.cat-links a`, `.entry-summary`) ne correspondent
plus a la structure HTML actuelle du site (le theme WordPress a change
depuis la redaction du sujet). Inspection reelle via DevTools sur
`https://www.blogdumoderateur.com/articles/` :

| Champ      | Selecteur reellement utilise                  | Repli (selecteur du sujet) |
|------------|------------------------------------------------|-----------------------------|
| titre/url  | `header.entry-header a`                         | `h2.post-title a`           |
| date       | `time[datetime]` (attribut `datetime`, `[:10]`) | identique au sujet          |
| categorie  | `.favtag` (texte, pas de lien)                  | `.cat-links a`               |
| chapeau    | `.entry-excerpt`                                | `.entry-summary`             |

`scraper_bdm.py` essaie toujours le selecteur du sujet en repli, pour
rester fonctionnel si le theme change encore.

## Resultats

Voir la sortie de `python scraper_bdm.py --max 200` : le script vise
200 articles et s'arrete plus tot uniquement apres deux pages
consecutives sans nouvel article (quelques 404/erreurs de pagination
sont normaux, cf. checklist du sujet : minimum 180 lignes attendu).
