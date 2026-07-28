# Defi 1 - cookie forensics

Script : `cookie_forensics.py`. Resultats bruts dans `cookies_dump.json`
(genere en direct sur doctolib.fr, maiia.com, qare.fr, livi.fr).

## Precision sur first-party / third-party

`driver.get_cookies()` ne renvoie que les cookies du domaine sur lequel on
est, donc a peu pres tout ressort "first-party" par domaine (les
navigateurs bloquent les cookies tiers classiques depuis un moment, du
coup la plupart des trackers passent maintenant par le domaine du site
lui-meme). Ce qui reste vraiment identifiable, c'est l'editeur derriere le
nom du cookie -- c'est ce que j'ai utilise pour le classement ci-dessous
plutot que le domaine brut.

## 3 cookies tiers repérés

| Nom | Site | Domaine | Duree | Valeur | Vendeur |
|---|---|---|---|---|---|
| `__cf_bm` | doctolib | .doctolib.fr | session courte (~30 min) | opaque, signee | Cloudflare Bot Management (anti-bot, pas du tracking pub) |
| `_ga` / `_ga_XXXXXXX` | qare | .qare.fr | ~2 ans | lisible : `GA1.1.<client_id>.<timestamp>` | Google Analytics |
| `_uetsid` / `_uetvid` | qare | .qare.fr | session / ~13 mois | id opaque | Microsoft Advertising (UET, ex-Bing Ads) |
| `datadome` | maiia | .maiia.com | ~1 an | token opaque | DataDome, anti-bot/anti-fraude -- le meme genre de protection que celle qui m'a bloque sur lesechos.fr |
| `rxVisitor` / `rxvt` | maiia | .maiia.com | longue / session | timestamp + id visiteur en clair | Contentsquare, analytics comportemental |

Plus parlant que n'importe quel cookie individuel : le `didomi_token` de
qare.fr contient, une fois decode (base64 -> JSON), la liste complete des
vendeurs tiers actives par l'utilisateur :

```json
"vendors": { "enabled": [
  "google", "c:pianohybr-...", "c:unbounce", "c:linkedin-...",
  "c:facebookc-...", "c:snapchatf-...", "c:microsoft-...",
  "c:contentsquare", "c:hubspot", "c:posthog-...", "c:googleana-...",
  "c:tiktok-...", "c:braze-..."
]}
```

13 vendeurs tiers nommes explicitement (Google, Piano, Unbounce, LinkedIn,
Facebook, Snapchat, Microsoft, Contentsquare, HubSpot, PostHog, Google
Analytics, TikTok, Braze), plus Stripe/AWS/Zendesk dans `vendors_li`
(vendeurs bases sur l'interet legitime plutot que le consentement). C'est
Didomi lui-meme qui liste ses clients tiers en clair dans son propre
cookie de consentement.

**Variabilite constatee** : en relancant le script un peu plus tard sans
rien changer, qare.fr est passe de 4 a 9 cookies (les 5 en plus : `_ga`,
`_ga_XXXXXXX`, `_uetsid`, `_uetvid`, `euconsent-v2`), et maiia.com a perdu
son cookie `tarteaucitron` (present au premier essai, absent au second,
alors que dans les deux cas le script n'a pas trouve de bouton a cliquer).
Les cookies analytics/pub ne sont visiblement pas tous poses de facon
deterministe des le premier chargement -- un point a garder en tete pour
tout script qui compterait sur la presence garantie d'un cookie precis.

## Le cookie a reproduire pour la Strategie 2 (Doctolib)

`didomi_token`, domaine .doctolib.fr, secure=false, sameSite=Lax, ~1 an de
duree de vie. Valeur = un JSON encode en base64 :

```json
{
  "user_id": "19fa80ab-63c8-68fc-bac7-ba2eb2032295",
  "created": "2026-07-28T09:25:02.140Z",
  "updated": "2026-07-28T09:25:02.140Z",
  "version": null
}
```

Donc pour bypasser la banniere sans cliquer, il suffit d'injecter un
`didomi_token` avec un UUID genere localement et les dates du jour, avant
le premier chargement de page. Didomi ne verifie que la presence et la
structure du token, pas une signature complexe.

## Comparaison Maiia / Qare / Livi

- Doctolib et Qare utilisent tous les deux **le meme CMP, Didomi**, avec
  exactement le meme nom de cookie (`didomi_token`). Ca fait sens, ce sont
  deux acteurs de la e-sante qui utilisent probablement le meme
  prestataire pour le consentement.
- Maiia utilise un CMP different, Tarteaucitron (solution open-source
  francaise), avec un format de cookie totalement different -- meme si son
  cookie de consentement n'est pas toujours present d'un run a l'autre
  (voir plus haut).
- Livi : le bouton n'a pas ete trouve avec le XPath generique utilise ici
  (0 cookie recu), a verifier a la main sur ce site puisque son libelle de
  bouton doit etre different de "Accepter"/"J'accepte".

## Ce que ca dit

Accepter "Tout accepter" chez Doctolib ne pose quasiment pas de cookie
publicitaire : le seul cookie tiers notable est un cookie anti-bot
(Cloudflare), pas un tracker marketing -- coherent avec le fait que ce
meme site m'a bloque plusieurs fois pendant mes tests (voir README
principal). A l'inverse, le `didomi_token` de Qare montre bien le
principe RGPD de consentement par finalite : chaque tiers marketing
(Google, Meta, LinkedIn, TikTok...) a son propre etat de consentement
liste individuellement, pas un "tout ou rien" global.
