#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPSSI - Module Web Scraping - Jour 1
TP - Veille technologique automatisee : Blog du Moderateur

Etape 3 : persistance des articles collectes en CSV UTF-8 et en SQLite
(deduplication via INSERT OR IGNORE sur url UNIQUE).
"""

import csv
import sqlite3
import time

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.blogdumoderateur.com"
LISTING_PATH = "/articles"
DELAY_BETWEEN_REQUESTS = 1.5  # secondes, throttling : 1-2 s entre requetes
TIMEOUT = 10
HEADERS = {
    "User-Agent": "IPSSI-scraper (+contact@ipssi.fr)",
    "Accept-Language": "fr-FR,fr;q=0.9",
}
CHAMPS = ["titre", "url", "date", "categorie", "chapeau"]


def page_url(page: int) -> str:
    """URL de la page N de l'archive des articles (page 1 = /articles/)."""
    if page == 1:
        return f"{BASE_URL}{LISTING_PATH}/"
    return f"{BASE_URL}{LISTING_PATH}/page/{page}/"


def get_page(url: str, tries: int = 3) -> BeautifulSoup | None:
    """GET avec timeout, retry exponentiel sur 5xx/429/timeout, abandon sur 4xx."""
    for attempt in range(tries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if r.status_code == 429:
                wait = int(r.headers.get("Retry-After", 10))
                print(f"[429] {url} -> attente {wait}s avant retry")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except requests.Timeout:
            print(f"[TIMEOUT] tentative {attempt + 1}/{tries} sur {url}")
            time.sleep(2 ** attempt)
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code < 500:
                print(f"[HTTPError] {url} -> {e} (erreur 4xx definitive, page ignoree)")
                return None
            print(f"[HTTPError 5xx] tentative {attempt + 1}/{tries} sur {url} -> {e}")
            time.sleep(2 ** attempt)
        except requests.RequestException as e:
            print(f"[ERREUR RESEAU] {url} -> {e}")
            return None
    print(f"[ECHEC] abandon apres {tries} tentatives : {url}")
    return None


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


def scrape_all(max_articles: int = 200) -> list[dict]:
    """Boucle de pagination : s'arrete a max_articles ou apres 2 pages vides."""
    collected: list[dict] = []
    seen: set[str] = set()
    page = 1
    empty_streak = 0

    while len(collected) < max_articles:
        url = page_url(page)
        soup = get_page(url)
        if soup is None:
            print(f"[INFO] page {page} inaccessible, arret de la pagination.")
            break

        nouveaux = [a for a in parse_articles(soup) if a["url"] not in seen]

        if not nouveaux:
            empty_streak += 1
            print(f"[INFO] page {page} sans nouvel article ({empty_streak}/2).")
            if empty_streak >= 2:
                print("[INFO] deux pages sans nouvel article, arret.")
                break
        else:
            empty_streak = 0

        for a in nouveaux:
            if len(collected) >= max_articles:
                break
            collected.append(a)
            seen.add(a["url"])

        print(f"[INFO] page {page} -> {len(nouveaux)} nouveaux | total={len(collected)}/{max_articles}")
        page += 1
        time.sleep(DELAY_BETWEEN_REQUESTS)

    return collected[:max_articles]


def sauver_csv(articles: list[dict], chemin: str = "articles.csv") -> None:
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CHAMPS, extrasaction="ignore")
        w.writeheader()
        w.writerows(articles)
    print(f"CSV : {len(articles)} lignes -> {chemin}")


DDL = """
CREATE TABLE IF NOT EXISTS articles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    titre       TEXT NOT NULL,
    url         TEXT NOT NULL UNIQUE,
    date        TEXT,
    categorie   TEXT,
    chapeau     TEXT,
    scraped_at  TEXT DEFAULT CURRENT_TIMESTAMP
)
"""


def sauver_sqlite(articles: list[dict], chemin: str = "articles.db") -> None:
    with sqlite3.connect(chemin) as cx:
        cx.execute(DDL)
        inserted = 0
        for a in articles:
            try:
                cx.execute(
                    "INSERT OR IGNORE INTO articles (titre,url,date,categorie,chapeau) "
                    "VALUES (:titre,:url,:date,:categorie,:chapeau)",
                    a,
                )
                inserted += cx.execute("SELECT changes()").fetchone()[0]
            except sqlite3.Error as e:
                print(f"[Erreur SQLite] {e}")
        cx.commit()
    print(f"SQLite : {inserted} nouvelles lignes inserees dans {chemin}")


if __name__ == "__main__":
    articles = scrape_all(200)
    print(f"Termine : {len(articles)} articles collectes")
    sauver_csv(articles)
    sauver_sqlite(articles)
