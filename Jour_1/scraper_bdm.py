#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPSSI - Module Web Scraping - Jour 1
TP - Veille technologique automatisee : Blog du Moderateur

Scrape les N derniers articles (titre, url, date, categorie, chapeau),
exporte en CSV UTF-8 et persiste en SQLite (INSERT OR IGNORE).

NOTE : les selecteurs "officiels" du sujet (h2.post-title a, .cat-links a,
.entry-summary) ne matchent plus la structure actuelle du site (refonte).
Ce script utilise donc les selecteurs reels observes via DevTools sur
https://www.blogdumoderateur.com/articles/ (page d'archive, structure
stable), avec repli sur les selecteurs du sujet si le theme change encore.
"""

import argparse
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


def _title_link(card):
    """Lien titre : structure actuelle (header.entry-header a) puis repli sujet TP."""
    return (
        card.select_one("header.entry-header a")
        or card.select_one("h2.post-title a")
        or card.select_one("h3.entry-title a")
        or card.select_one("h2.entry-title a")
    )


def _categorie(card) -> str:
    """Categorie(s) : .cat-links a (sujet TP) sinon .favtag (structure actuelle)."""
    links = card.select(".cat-links a") or card.select("a[href*='/dossier/']")
    if links:
        textes = [a.get_text(strip=True) for a in links]
    else:
        textes = [t.get_text(strip=True) for t in card.select(".favtag")]
    return ", ".join(dict.fromkeys(textes))  # dedoublonne en gardant l'ordre


def parse_one(card) -> dict | None:
    """Extrait les 5 champs d'une carte <article>, ou None si non exploitable."""
    link = _title_link(card)
    if link is None:
        return None

    time_tag = card.select_one("time[datetime]")
    summary_tag = card.select_one(".entry-summary") or card.select_one(".entry-excerpt")

    return {
        "titre": link.get_text(strip=True),
        "url": link.get("href", "").strip(),
        "date": time_tag.get("datetime", "")[:10] if time_tag else "",
        "categorie": _categorie(card),
        "chapeau": summary_tag.get_text(strip=True)[:300] if summary_tag else "",
    }


def parse_articles(soup: BeautifulSoup) -> list[dict]:
    """List-comprehension : parse toutes les cartes, ignore celles sans titre/url."""
    return [a for c in soup.select("article") if (a := parse_one(c)) is not None]


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Scraper Blog du Moderateur (IPSSI TP)")
    parser.add_argument("--max", type=int, default=200, help="Nb max d'articles")
    parser.add_argument("--csv", default="articles.csv")
    parser.add_argument("--db", default="articles.db")
    args = parser.parse_args()

    print(f"Demarrage - cible : {args.max} articles")
    articles = scrape_all(args.max)

    if not articles:
        print("[ERREUR] aucun article collecte, verifiez la connectivite ou les selecteurs.")
        raise SystemExit(1)

    sauver_csv(articles, args.csv)
    sauver_sqlite(articles, args.db)
    print(f"Termine : {len(articles)} articles")


if __name__ == "__main__":
    main()
