#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPSSI - Module Web Scraping - Jour 1
TP - Veille technologique automatisee : Blog du Moderateur

Etape 1 : scraper une seule page (page d'accueil / archive des articles)
et verifier que les selecteurs CSS observes via DevTools fonctionnent.
"""

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.blogdumoderateur.com"
HEADERS = {
    "User-Agent": "IPSSI-scraper (+contact@ipssi.fr)",
    "Accept-Language": "fr-FR,fr;q=0.9",
}


def get_page(url: str) -> BeautifulSoup:
    """GET simple avec timeout, leve une exception sur erreur HTTP."""
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def parse_articles(soup: BeautifulSoup) -> list[dict]:
    """Extrait titre/url/date/categorie/chapeau de chaque <article> de la page."""
    articles = []
    for card in soup.select("article"):
        link = card.select_one("header.entry-header a")
        if link is None:
            continue

        time_tag = card.select_one("time[datetime]")
        summary_tag = card.select_one(".entry-excerpt")
        cat_tags = card.select(".favtag")

        articles.append({
            "titre": link.get_text(strip=True),
            "url": link.get("href", "").strip(),
            "date": time_tag.get("datetime", "")[:10] if time_tag else "",
            "categorie": ", ".join(t.get_text(strip=True) for t in cat_tags),
            "chapeau": summary_tag.get_text(strip=True)[:300] if summary_tag else "",
        })
    return articles


if __name__ == "__main__":
    soup = get_page(f"{BASE_URL}/articles/")
    arts = parse_articles(soup)
    print(f"{len(arts)} articles trouves sur la page")
    for a in arts[:3]:
        print(a["titre"][:60])
