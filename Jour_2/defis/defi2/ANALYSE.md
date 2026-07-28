# Defi 2 - empreinte anti-bot

Script : `bot_fingerprint.py`, contre bot.sannysoft.com (independant de
Doctolib/Les Echos). J'ai teste 4 configs au lieu de 2 pour separer l'effet
du headless de celui des flags anti-detection :

| Fichier                      | headless | flags stealth | navigator.webdriver |
|-------------------------------|:--------:|:--------------:|:---------------------:|
| normal.png                    | non      | non            | True                  |
| stealth.png                   | non      | oui            | False                 |
| headless_sans_stealth.png     | oui      | non            | True                  |
| headless_stealth.png          | oui      | oui            | False                 |

## Rouge -> vert entre normal et stealth

Un seul champ change : **WebDriver (New)**, `present (failed)` en rouge ->
`missing (passed)` en vert. Tout le reste (WebDriver Advanced, Chrome,
Permissions, plugins, WebGL, les tests fingerprint scanner en bas de page)
etait deja vert meme sans flag. Chrome 150 ne laisse pas grand chose
d'autre filtrer par defaut.

## Le champ webdriver est-il toujours detecte en stealth ?

Non, il passe bien a False des qu'on ajoute
`--disable-blink-features=AutomationControlled` +
`excludeSwitches=["enable-automation"]`. Confirme aussi directement avec
`driver.execute_script("return navigator.webdriver")` dans le script (voir
run.log).

## Et en headless, qu'est-ce qui devient rouge ?

En comparant headless_sans_stealth a normal : le **User Agent** passe au
rouge, parce qu'il contient "HeadlessChrome/150.0.0.0" au lieu de
"Chrome/150.0.0.0". C'est une signature completement explicite, pas besoin
d'analyse poussee pour la detecter.

Et ce champ reste rouge meme avec les flags stealth actives
(headless_stealth.png) : les deux flags du sujet ne touchent que
navigator.webdriver, pas la chaine User-Agent. Pour regler ca il faudrait
forcer l'UA a la main (`--user-agent=...` ou override CDP), ce que je n'ai
pas fait ici.

## Bilan

Les deux flags marchent bien sur navigator.webdriver, qui est le signal le
plus souvent verifie en pratique, mais ca ne rend pas un Chrome headless
invisible pour autant (l'UA trahit toujours HeadlessChrome). Et de toute
facon, un vrai systeme anti-bot ne se limite pas a ces 2-3 signaux JS :
lesechos.fr par exemple bloque a un niveau reseau (voir README principal)
qu'aucun flag Selenium ne change.
