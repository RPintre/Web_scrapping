#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Defi 1 - cookie forensics

Visite chaque site, accepte la banniere si possible, dump tous les cookies
(driver.get_cookies()) dans cookies_dump.json. Voir ANALYSE.md pour le detail.

python cookie_forensics.py
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

OUTPUT_DIR = Path(__file__).parent

SITES = {
    "doctolib": "https://www.doctolib.fr/cardiologue/lyon",
    "maiia": "https://www.maiia.com",
    "qare": "https://www.qare.fr",
    "livi": "https://www.livi.fr",
}

COOKIE_ACCEPT_XPATH = (
    '//button[contains(text(),"Accepter") or contains(text(),"Tout accepter") '
    'or contains(text(),"J\'accepte") or contains(@aria-label,"Accepter")]'
)


def registrable_domain(url: str) -> str:
    """Approximation simple du domaine "principal" d'un site (sans sous-domaine)."""
    host = urlparse(url).netloc
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def dump_cookies_for(label: str, url: str) -> list[dict]:
    site_domain = registrable_domain(url)
    opts = webdriver.ChromeOptions()
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(options=opts)

    try:
        driver.get(url)
        try:
            btn = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable((By.XPATH, COOKIE_ACCEPT_XPATH))
            )
            btn.click()
            print(f"[{label}] Banniere cookies acceptee")
        except Exception:
            print(f"[{label}] Pas de banniere cliquable trouvee (ou deja bloque/absent)")

        cookies = driver.get_cookies()
        for c in cookies:
            cookie_domain = c.get("domain", "").lstrip(".")
            c["classification"] = (
                "first-party" if cookie_domain.endswith(site_domain) else "third-party"
            )

        print(f"[{label}] {len(cookies)} cookie(s) trouve(s)")
        return cookies
    finally:
        driver.quit()


def main() -> None:
    all_results: dict[str, list[dict]] = {}
    for label, url in SITES.items():
        try:
            all_results[label] = dump_cookies_for(label, url)
        except Exception as err:
            print(f"[{label}] Echec : {err}")
            all_results[label] = []

    output_path = OUTPUT_DIR / "cookies_dump.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"Resultats -> {output_path}")


if __name__ == "__main__":
    main()
