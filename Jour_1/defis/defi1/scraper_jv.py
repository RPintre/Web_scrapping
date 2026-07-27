#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Defi 1 - Adapter le scraper a un site de mon choix : jeuxvideo.com
Reutilise get_page() et sauver_csv() de scraper_bdm.py (aucun copier-coller).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scraper_bdm import get_page, sauver_csv  # noqa: E402

BASE_URL = "https://www.jeuxvideo.com"
LISTING_URL = f"{BASE_URL}/actualites.htm"


def parse_articles(soup, limite: int = 20) -> list[dict]:
    return [
        {
            "titre": link.get_text(strip=True),
            "url": BASE_URL + link["href"] if link["href"].startswith("/") else link["href"],
            "date": date_tag.get_text(strip=True) if date_tag else "",
            "categorie": cat_tag.get_text(strip=True) if cat_tag else "",
        }
        for c in soup.select("div.card")
        if (link := c.select_one("h3.card-title a")) is not None
        for date_tag in [c.select_one(".card__textMuted")]
        for cat_tag in [c.select_one(".card__contentType")]
    ][:limite]


def main() -> None:
    soup = get_page(LISTING_URL)
    if soup is None:
        print(f"[ERREUR] impossible de recuperer {LISTING_URL}")
        return

    articles = parse_articles(soup, limite=20)
    print(f"{len(articles)} articles extraits depuis {LISTING_URL}")

    sortie = Path(__file__).parent / "articles_jeuxvideo.csv"
    sauver_csv(articles, str(sortie))


if __name__ == "__main__":
    main()
