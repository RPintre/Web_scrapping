"""
TD 4.2 - Cartographie publique d'une entite (OSINT).

Cible retenue : SNCF (institution publique, EPIC ferroviaire). Trois
sources publiques : annuaire SIRENE (data.gouv.fr), Wikipedia
(infobox + intro), presse (Google News RSS).

Usage :
    python td42_entite.py SNCF
    python td42_entite.py TotalEnergies
"""

import json
import time

import feedparser
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "IPSSI-OSINT (+r.pintre@gmail.com)"}


def chercher_sirene(nom: str) -> dict:
    """API recherche-entreprises.api.gouv.fr -- pas besoin de cle API.

    Note : le sujet pointe vers api.annuaire-entreprises.data.gouv.fr/v3,
    dont le nom d'hote ne resout plus (DNS NXDOMAIN teste en pratique).
    L'API officielle actuelle est recherche-entreprises.api.gouv.fr, et
    son schema JSON differe aussi de celui du sujet : activite_principale
    et tranche_effectif_salarie sont sous la cle "siege", pas a la racine
    de chaque resultat.
    """
    url = f"https://recherche-entreprises.api.gouv.fr/search?q={nom}&limit=1"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("results"):
            ent = data["results"][0]
            siege = ent.get("siege", {}) or {}
            return {
                "siren": ent.get("siren"),
                "denomination": ent.get("nom_complet"),
                "adresse_siege": siege.get("adresse"),
                "code_naf": siege.get("activite_principale"),
                "date_creation": ent.get("date_creation") or siege.get("date_creation"),
                "tranche_effectif": siege.get("tranche_effectif_salarie"),
            }
        return {"resultat": "Non trouve dans SIRENE"}
    except Exception as e:
        return {"erreur": str(e)}


def scraper_wikipedia(nom: str) -> dict:
    """Scraper l'infobox et l'intro de la page Wikipedia."""
    slug = nom.replace(" ", "_")
    url = f"https://fr.wikipedia.org/wiki/{slug}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")

        infobox = {}
        table = soup.select_one("table.infobox, table.wikitable")
        if table:
            for tr in table.select("tr"):
                th = tr.select_one("th")
                td = tr.select_one("td")
                if th and td:
                    cle = th.get_text(strip=True)
                    val = td.get_text(" ", strip=True)[:200]
                    infobox[cle] = val

        intro = ""
        for p in soup.select("#mw-content-text p"):
            txt = p.get_text(strip=True)
            if len(txt) > 80:
                intro = txt[:500]
                break

        return {"infobox": infobox, "intro": intro, "url": url}
    except Exception as e:
        return {"erreur": str(e)}


def veille_presse(nom: str, nb_max: int = 10) -> list[dict]:
    """Google News RSS : articles recents mentionnant l'entite."""
    query = nom.replace(" ", "+")
    url = f"https://news.google.com/rss/search?q={query}&hl=fr&gl=FR&ceid=FR:fr"
    feed = feedparser.parse(url)
    return [
        {
            "titre": e.get("title", ""),
            "source": e.get("source", {}).get("title", ""),
            "date": e.get("published", ""),
            "lien": e.get("link", ""),
        }
        for e in feed.entries[:nb_max]
    ]


def construire_fiche(nom: str) -> dict:
    print(f"[*] Construction de la fiche pour : {nom}")
    fiche = {"entite": nom}
    fiche["sirene"] = chercher_sirene(nom)
    time.sleep(1)
    fiche["wikipedia"] = scraper_wikipedia(nom)
    time.sleep(1)
    fiche["presse"] = veille_presse(nom)
    fiche["nb_articles"] = len(fiche["presse"])
    return fiche


if __name__ == "__main__":
    import sys

    nom = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "SNCF"
    fiche = construire_fiche(nom)
    with open("fiche_entite.json", "w", encoding="utf-8") as f:
        json.dump(fiche, f, indent=2, ensure_ascii=False)
    print("[+] Fiche sauvegardee : fiche_entite.json")
    print(f"    SIREN : {fiche['sirene'].get('siren', 'n/a')}")
    print(f"    Articles: {fiche['nb_articles']}")
