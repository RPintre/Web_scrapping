#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TD 2.1 - Doctolib

Scrape la premiere page de resultats pour une specialite/ville donnee et
sort un JSON avec, par medecin : nom_specialite, adresse, type_consultation,
prochains_creneaux (3 max), url_fiche.

python doctolib_scraper.py --specialty cardiologue --city lyon
python doctolib_scraper.py --specialty dentiste --city paris --headless
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "https://www.doctolib.fr"
WAIT_TIMEOUT = 15
COOKIE_BANNER_TIMEOUT = 5
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"

# data-test='search-result-card' donne par le sujet, + un repli au cas ou
# Doctolib change l'attribut (data-testid)
CARD_SELECTORS = [
    "div[data-test='search-result-card']",
    "div[data-testid='search-result-card']",
]

COOKIE_ACCEPT_XPATH = '//button[contains(text(),"Accepter") or contains(text(),"Tout accepter")]'

NAME_SELECTORS = ["h2, h3, [class*='name']"]
LINK_SELECTOR = "a[href*='/']"
# vu dans le HTML reel (--debug) : chaque jour a des cases [class*='h-40'],
# soit un vrai creneau, soit un tiret "-" (placeholder = rien ce jour-la)
AVAILABILITIES_CONTAINER_SELECTOR = "[data-test-id='availabilities-container']"
SLOT_CELL_SELECTOR = "[class*='h-40'] span"
SLOT_PLACEHOLDER = "—"
# vu dans le HTML reel (--debug) : l'icone video porte cet attribut, pas de
# classe "consultation-mode"
TELEHEALTH_ICON_SELECTOR = "[data-test-id='telehealth-icon'], [data-icon-name='solid/video']"


@dataclass
class Medecin:
    nom_specialite: str = "n/a"
    adresse: str = "n/a"
    type_consultation: list[str] = field(default_factory=lambda: ["n/a"])
    prochains_creneaux: list[str] = field(default_factory=list)
    url_fiche: str = "n/a"


def make_driver(headless: bool = False) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # meme en --headless=new, Chrome garde "HeadlessChrome" dans son
        # User-Agent (confirme dans defis/defi2) -- Doctolib bloque
        # systematiquement dessus ("Retry later" des la 1ere requete, teste
        # a froid, donc pas un rate-limit). On force un UA de Chrome normal.
        # version alignee sur le Chrome reellement installe (voir
        # defis/defi2/run.log) : un decalage entre l'UA et les Client Hints
        # (Sec-CH-UA, envoyes automatiquement avec la vraie version) serait
        # lui-meme un signal de detection.
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
        )
    # limite (sans la supprimer completement, cf defi 2) la detection
    # d'automatisation
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--window-size=1280,1000")
    options.add_argument("--lang=fr-FR")
    return webdriver.Chrome(options=options)


def save_debug_screenshot(driver, context: str) -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    safe_context = re.sub(r"[^a-zA-Z0-9_-]+", "_", context)[:80]
    path = SCREENSHOT_DIR / f"doctolib_erreur_{safe_context}_{int(time.time())}.png"
    try:
        driver.save_screenshot(str(path))
        print(f"[SCREENSHOT] {path}")
    except WebDriverException as err:
        print(f"[SCREENSHOT] Impossible de sauvegarder ({context}) : {err}")


def accept_cookies(driver, wait: WebDriverWait) -> None:
    # Strategie 1 (celle utilisee ici) : cliquer sur le bouton Accepter.
    #
    # Strategie 2, plus robuste : injecter direct le cookie "didomi_token"
    # (via driver.add_cookie puis refresh) au lieu de cliquer -- voir
    # defis/defi1 pour le nom et la structure exacte du cookie.
    #
    # Strategie 3 : profil Chrome persistant (--user-data-dir=...) pour ne
    # plus jamais revoir la banniere d'une execution a l'autre.
    try:
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, COOKIE_ACCEPT_XPATH)))
        btn.click()
        print("Cookies acceptes")
    except TimeoutException:
        print("Pas de banniere detectee")


def wait_for_results(driver, wait: WebDriverWait, specialty: str, city: str) -> tuple[str, bool]:
    """Renvoie (selecteur, est_un_lien). data-test='search-result-card' (donne
    par le sujet) ne matche plus rien sur les pages actuelles -> repli sur le
    lien vers la fiche du praticien, qui lui marche toujours."""
    for selector in CARD_SELECTORS:
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            print("Resultats charges")
            return selector, False
        except TimeoutException:
            continue

    link_selector = f"a[href*='/{specialty}/{city}/']"
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, link_selector)))
        print("Resultats charges (via les liens de fiche)")
        return link_selector, True
    except TimeoutException:
        pass

    save_debug_screenshot(driver, "resultats_non_charges")
    raise RuntimeError("Resultats non charges : aucune carte medecin trouvee.")


def scroll_to_bottom(driver, pauses: int = 3) -> None:
    last_h = driver.execute_script("return document.body.scrollHeight")
    for _ in range(pauses):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1.5)
        new_h = driver.execute_script("return document.body.scrollHeight")
        if new_h == last_h:
            break
        last_h = new_h


TEXTE_NOEUD_DIRECT_JS = (
    "return Array.from(arguments[0].childNodes)"
    ".filter(n => n.nodeType === 3)"
    ".map(n => n.textContent)"
    ".join(' ');"
)


def texte_noeud_direct(el) -> str:
    """Ne recupere que les noeuds texte DIRECTS de l'element (ignore les
    spans imbriques, souvent du texte cache pour lecteurs d'ecran, ex :
    'Consultation video disponible' colle au nom du medecin)."""
    try:
        return (el.parent.execute_script(TEXTE_NOEUD_DIRECT_JS, el) or "").strip()
    except WebDriverException:
        return ""


def extraire_adresse(carte) -> str:
    # L'adresse n'a pas de classe dediee : elle se repere via l'icone
    # aria-label="Adresse", puis les <p> du bloc juste apres (rue, code
    # postal + ville).
    try:
        paragraphes = carte.find_elements(
            By.XPATH, ".//*[@aria-label='Adresse']/ancestor::div[1]/following-sibling::div[1]//p"
        )
    except NoSuchElementException:
        return "n/a"
    textes = [
        texte_noeud_direct(p) or (p.get_attribute("textContent") or "").strip() for p in paragraphes
    ]
    textes = [t for t in textes if t]
    return ", ".join(textes) if textes else "n/a"


def first_text(carte, selectors: list[str]) -> str | None:
    for selector in selectors:
        for el in carte.find_elements(By.CSS_SELECTOR, selector):
            # textContent plutot que .text : Doctolib garde des balises
            # "deprecated" que Selenium juge non visibles (.text vide) alors
            # que le texte y est bien present.
            texte = texte_noeud_direct(el) or (el.get_attribute("textContent") or "").strip()
            if texte:
                return texte
    return None


def resoudre_carte(element, is_link: bool):
    """A partir du lien de fiche, remonte au plus proche ancetre qui contient
    aussi l'icone d'adresse, PUIS encore un niveau au-dessus : sur la page de
    resultats, la carte est en fait 2 colonnes cote a cote (flex-row) --
    nom/adresse a gauche, zone de creneaux (data-test-id='availabilities-
    container') a droite, comme deux enfants du meme parent. S'arreter a la
    colonne de gauche fait qu'on ne voit jamais les creneaux."""
    if not is_link:
        return element
    try:
        colonne = element.find_element(By.XPATH, "./ancestor::div[.//*[@aria-label='Adresse']][1]")
    except NoSuchElementException:
        try:
            return element.find_element(By.XPATH, "./ancestor::div[3]")
        except NoSuchElementException:
            return element
    try:
        return colonne.find_element(By.XPATH, "./..")
    except NoSuchElementException:
        return colonne


def extraire_medecins(
    driver,
    max_medecins: int,
    selector: str,
    is_link: bool,
    debug: bool = False,
    seulement_disponibles: bool = False,
) -> list[dict]:
    elements = driver.find_elements(By.CSS_SELECTOR, selector)
    resultats: list[dict] = []
    seen_urls: set[str] = set()
    debug_montres = 0

    for i, element in enumerate(elements):
        if len(resultats) >= max_medecins:
            break
        try:
            carte = resoudre_carte(element, is_link)

            nom = first_text(carte, NAME_SELECTORS)
            if not nom:
                if debug and i < 3:
                    html = carte.get_attribute("outerHTML") or ""
                    print(f"--- DEBUG carte #{i} (nom introuvable) ---")
                    print(html[:1500])
                    print("--- FIN DEBUG ---")
                continue

            adr = extraire_adresse(carte)

            url = element.get_attribute("href") if is_link else None
            if not url:
                liens = carte.find_elements(By.CSS_SELECTOR, LINK_SELECTOR)
                url = "n/a"
                for lien in liens:
                    href = lien.get_attribute("href") or ""
                    if href and "doctolib.fr" in href and "/rubriques/" not in href:
                        url = href
                        break
            if url in seen_urls:
                continue

            creneaux: list[str] = []
            conteneurs = carte.find_elements(By.CSS_SELECTOR, AVAILABILITIES_CONTAINER_SELECTOR)
            if conteneurs:
                creneaux = [
                    texte
                    for el in conteneurs[0].find_elements(By.CSS_SELECTOR, SLOT_CELL_SELECTOR)
                    if (texte := (el.get_attribute("textContent") or "").strip())
                    and texte != SLOT_PLACEHOLDER
                ][:3]

            if debug and not creneaux and debug_montres < 3:
                zones = carte.find_elements(By.CSS_SELECTOR, "[data-test-id='availabilities-container']")
                if zones:
                    html = zones[0].get_attribute("outerHTML") or ""
                    print(f"--- DEBUG carte #{i} ({nom}) : availabilities-container ---")
                    print(html[:6000] or "(vide)")
                else:
                    html = carte.get_attribute("outerHTML") or ""
                    print(f"--- DEBUG carte #{i} ({nom}) : pas de availabilities-container, fin de carte ---")
                    print(html[-2000:])
                print("--- FIN DEBUG ---")
                debug_montres += 1

            if seulement_disponibles and not creneaux:
                continue

            types: list[str] = []
            if adr != "n/a":
                types.append("Cabinet")
            if carte.find_elements(By.CSS_SELECTOR, TELEHEALTH_ICON_SELECTOR):
                types.append("Video")

            seen_urls.add(url)
            resultats.append(
                Medecin(
                    nom_specialite=nom,
                    adresse=adr,
                    type_consultation=types or ["n/a"],
                    prochains_creneaux=creneaux,
                    url_fiche=url,
                ).__dict__
            )
        except NoSuchElementException as err:
            print(f"Carte ignoree : {err}")

    return resultats


def scrape_doctolib(
    specialty: str,
    city: str,
    max_medecins: int,
    headless: bool,
    debug: bool = False,
    seulement_disponibles: bool = False,
) -> tuple[list[dict], float]:
    t0 = time.time()
    driver = make_driver(headless=headless)
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    try:
        url = f"{BASE_URL}/{specialty}/{city}"
        driver.get(url)
        accept_cookies(driver, wait)
        selector, is_link = wait_for_results(driver, wait, specialty, city)
        # si on filtre sur les disponibilites, il faut scroller plus loin
        # pour avoir assez de candidats (beaucoup n'auront pas de creneau)
        scroll_to_bottom(driver, pauses=8 if seulement_disponibles else 3)
        medecins = extraire_medecins(
            driver,
            max_medecins,
            selector,
            is_link,
            debug=debug,
            seulement_disponibles=seulement_disponibles,
        )
    finally:
        driver.quit()
    return medecins, time.time() - t0


def compare_headless(specialty: str, city: str, max_medecins: int) -> list[dict]:
    medecins_normal, t_normal = scrape_doctolib(specialty, city, max_medecins, headless=False)
    print(f"Normal : {t_normal:.1f}s")

    # petite pause avant le 2e run : Doctolib applique un rate-limit court
    # terme si on enchaine deux scrapes complets immediatement (deja
    # rencontre pendant le dev, voir README.md)
    time.sleep(10)

    try:
        _, t_headless = scrape_doctolib(specialty, city, max_medecins, headless=True)
    except RuntimeError as err:
        print(f"Headless: echec ({err}) -- probablement le rate-limit court terme de Doctolib.")
        return medecins_normal

    print(f"Headless: {t_headless:.1f}s")
    if t_headless > 0:
        print(f"Gain : {t_normal / t_headless:.1f}x plus rapide")
    return medecins_normal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--specialty", required=True, help="ex: cardiologue, dentiste, ...")
    parser.add_argument("--city", required=True, help="ex: lyon, paris, ...")
    parser.add_argument("--max-medecins", type=int, default=10)
    parser.add_argument("--output", default="doctolib.json")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--debug", action="store_true", help="affiche le HTML des cartes non reconnues")
    parser.add_argument(
        "--seulement-disponibles",
        action="store_true",
        help="ne garde que les medecins avec au moins un creneau trouve",
    )
    parser.add_argument(
        "--compare-headless",
        action="store_true",
        help="relance le scraping avec et sans fenetre visible et compare la duree",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.compare_headless:
        medecins = compare_headless(args.specialty, args.city, args.max_medecins)
    else:
        medecins, elapsed = scrape_doctolib(
            specialty=args.specialty,
            city=args.city,
            max_medecins=args.max_medecins,
            headless=args.headless,
            debug=args.debug,
            seulement_disponibles=args.seulement_disponibles,
        )
        print(f"Termine en {elapsed:.1f}s")

    output_path = Path(__file__).parent / args.output
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(medecins, f, indent=2, ensure_ascii=False)
    print(f"{len(medecins)} medecins exportes dans {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
