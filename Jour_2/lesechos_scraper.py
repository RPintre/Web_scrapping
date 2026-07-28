#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TD 2.2 - Les Echos

--check-requests-only teste d'abord si requests suffit (etape 1 du sujet).
Sinon, scrape la une avec Selenium : titre, rubrique, chapeau, heure_publi,
premium, pour chaque article -> lesechos.json.

python lesechos_scraper.py --check-requests-only
python lesechos_scraper.py --max-articles 20
python lesechos_scraper.py --max-articles 20 --headless
python lesechos_scraper.py --compare-headless
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://www.lesechos.fr"
WAIT_TIMEOUT = 15
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"
DELAI_ENTRE_ARTICLES = (1.5, 3.0)

ARTICLE_SELECTOR = "article, [class*='article-item'], [class*='card-article']"
TITLE_SELECTORS = "h2, h3, [class*='title']"
RUBRIQUE_SELECTORS = "[data-testid='hubpage-links'] a, [class*='rubrique'], [class*='category']"
# vu dans le HTML reel (--debug) : le badge premium porte cet attribut,
# pas de classe "premium"/"abonne"
PREMIUM_SELECTORS = "[data-testid='subscribe-badge']"

# Le chapeau et l'heure ne sont pas sur les cartes de la une (verifie via
# --debug : rien de tel dans leur HTML), seulement sur la page de chaque
# article. La meta description est plus fiable qu'un <p> quelconque : c'est
# le chapo public utilise pour le referencement, donc forcement visible
# meme sans abonnement.
CHAPO_META_SELECTOR = "meta[name='description']"
CHAPO_FALLBACK_SELECTORS = "p"
HEURE_SELECTORS = "time[datetime]"
HEURE_META_SELECTOR = "meta[property='article:published_time']"


def check_requests_only() -> bool:
    print(f"[REQUESTS] GET {URL} ...")
    try:
        r = requests.get(
            URL,
            headers={"User-Agent": "IPSSI-scraper (+contact@ipssi.fr)"},
            timeout=10,
        )
        soup = BeautifulSoup(r.text, "lxml")
        titres = soup.select("h2, h3")
        print(f"[REQUESTS] HTTP {r.status_code} - {len(titres)} balises de titre trouvees")
        if r.status_code != 200:
            print(f"[REQUESTS] -> Bloque (HTTP {r.status_code}). Selenium necessaire.")
            return False
        if len(titres) == 0:
            print("[REQUESTS] -> 0 titre : page chargee en JS. Selenium necessaire.")
            return False
        print("[REQUESTS] -> Le HTML brut contient des titres, `requests` pourrait suffire.")
        return True
    except requests.RequestException as err:
        print(f"[REQUESTS] Erreur reseau : {err}. Selenium necessaire.")
        return False


def make_driver(headless: bool = False) -> webdriver.Chrome:
    opts = webdriver.ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        # meme piege que sur Doctolib : Chrome garde "HeadlessChrome" dans
        # son User-Agent en --headless=new, et Akamai bloque dessus
        # ("Access Denied" des la 1ere requete). On force un UA de Chrome
        # normal, meme version que le Chrome installe.
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
        )
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    return webdriver.Chrome(options=opts)


def save_debug_screenshot(driver, context: str) -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SCREENSHOT_DIR / f"lesechos_erreur_{context}_{int(time.time())}.png"
    driver.save_screenshot(str(path))
    print(f"[SCREENSHOT] {path}")


def load_homepage(driver) -> None:
    driver.get(URL)
    try:
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ARTICLE_SELECTOR))
        )
    except Exception as err:
        save_debug_screenshot(driver, "accueil_non_charge")
        raise RuntimeError(f"Page d'accueil non chargee : {err}") from err


TEXTE_NOEUD_DIRECT_JS = (
    "return Array.from(arguments[0].childNodes)"
    ".filter(n => n.nodeType === 3)"
    ".map(n => n.textContent)"
    ".join(' ');"
)


def premier_texte(art, selectors: str) -> str:
    # textContent (pas .text) : certains sites gardent des balises "cachees"
    # pour le SEO que Selenium juge non visibles -- .text renverrait vide
    # meme quand le texte est bien present (deja rencontre sur Doctolib).
    for el in art.find_elements(By.CSS_SELECTOR, selectors):
        try:
            texte = (el.parent.execute_script(TEXTE_NOEUD_DIRECT_JS, el) or "").strip()
        except Exception:
            texte = ""
        if not texte:
            texte = (el.get_attribute("textContent") or "").strip()
        if texte:
            return texte
    return ""


def extraire_articles(driver, max_articles: int, debug: bool = False) -> list[dict]:
    """Passe 1 : ce qui est visible directement sur la une (titre, rubrique,
    premium) + l'url de la fiche pour completer chapeau/heure ensuite."""
    articles = driver.find_elements(By.CSS_SELECTOR, ARTICLE_SELECTOR)
    resultats: list[dict] = []
    seen_urls: set[str] = set()
    debug_montres = 0
    for i, art in enumerate(articles):
        if len(resultats) >= max_articles:
            break
        try:
            titre = premier_texte(art, TITLE_SELECTORS)
            if not titre:
                if debug and debug_montres < 3:
                    html = art.get_attribute("outerHTML") or ""
                    print(f"--- DEBUG article #{i} (titre introuvable) ---")
                    print(html[:2000])
                    print("--- FIN DEBUG ---")
                    debug_montres += 1
                continue

            rubrique = premier_texte(art, RUBRIQUE_SELECTORS)
            premium = bool(art.find_elements(By.CSS_SELECTOR, PREMIUM_SELECTORS))

            url = ""
            liens = art.find_elements(By.CSS_SELECTOR, "a[href]")
            if liens:
                url = liens[0].get_attribute("href") or ""
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)

            resultats.append(
                {
                    "titre": titre,
                    "rubrique": rubrique,
                    "chapeau": "",
                    "heure_publi": "",
                    "premium": premium,
                    "url": url,
                }
            )
        except Exception as err:
            print(f"Article ignore : {err}")
    return resultats


def extraire_chapeau_page(driver, debug: bool = False) -> str:
    try:
        meta = driver.find_element(By.CSS_SELECTOR, CHAPO_META_SELECTOR)
        contenu = (meta.get_attribute("content") or "").strip()
        if contenu:
            return contenu[:300]
    except NoSuchElementException:
        pass
    texte = premier_texte(driver, CHAPO_FALLBACK_SELECTORS)
    if texte:
        return texte[:300]
    if debug:
        print("--- DEBUG page article : pas de meta description ni de <p> ---")
    return ""


def extraire_heure_page(driver) -> str:
    try:
        el = driver.find_element(By.CSS_SELECTOR, HEURE_SELECTORS)
        datetime_attr = el.get_attribute("datetime") or ""
        match = re.search(r"T(\d{2}:\d{2})", datetime_attr)
        if match:
            return match.group(1)
        texte = (el.get_attribute("textContent") or "").strip()
        if texte:
            return texte
    except NoSuchElementException:
        pass
    try:
        meta = driver.find_element(By.CSS_SELECTOR, HEURE_META_SELECTOR)
        match = re.search(r"T(\d{2}:\d{2})", meta.get_attribute("content") or "")
        if match:
            return match.group(1)
    except NoSuchElementException:
        pass
    return ""


def completer_details(driver, articles: list[dict], debug: bool = False) -> None:
    """Passe 2 : visite chaque fiche article pour recuperer chapeau + heure,
    absents des cartes de la une. Delai aleatoire entre chaque visite."""
    for art in articles:
        url = art.get("url")
        if not url:
            continue
        try:
            driver.get(url)
            art["chapeau"] = extraire_chapeau_page(driver, debug=debug)
            art["heure_publi"] = extraire_heure_page(driver)
        except WebDriverException as err:
            print(f"Fiche inaccessible ({url}) : {err}")
        time.sleep(random.uniform(*DELAI_ENTRE_ARTICLES))


def scrape_lesechos(max_articles: int, headless: bool, debug: bool = False) -> tuple[list[dict], float]:
    t0 = time.time()
    driver = make_driver(headless=headless)
    try:
        load_homepage(driver)
        articles = extraire_articles(driver, max_articles, debug=debug)
        completer_details(driver, articles, debug=debug)
    finally:
        driver.quit()
    elapsed = time.time() - t0
    return articles, elapsed


def compare_headless(max_articles: int) -> list[dict]:
    articles_normal, t_normal = scrape_lesechos(max_articles, headless=False)
    print(f"Normal : {t_normal:.1f}s")

    _, t_headless = scrape_lesechos(max_articles, headless=True)
    print(f"Headless: {t_headless:.1f}s")

    if t_headless > 0:
        print(f"Gain : {t_normal / t_headless:.1f}x plus rapide")
    return articles_normal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-articles", type=int, default=20)
    parser.add_argument("--output", default="lesechos.json")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--compare-headless", action="store_true")
    parser.add_argument("--check-requests-only", action="store_true")
    parser.add_argument("--debug", action="store_true", help="affiche le HTML des articles non reconnus")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.check_requests_only:
        check_requests_only()
        return 0

    if args.compare_headless:
        articles = compare_headless(args.max_articles)
    else:
        articles, elapsed = scrape_lesechos(args.max_articles, args.headless, debug=args.debug)
        print(f"Termine en {elapsed:.1f}s")

    output_path = Path(__file__).parent / args.output
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    print(f"{len(articles)} articles exportes dans {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
