"""
Defi 1 - Calibrer le scoring de sentiment.

Relit mentions.csv (produit par TD 4.3) et recalcule score_alerte avec
une liste de mots-cles elargie, pour comparer avant/apres sur les
memes articles (plus rigoureux qu'un nouveau crawl : meme donnees,
seule la calibration change).
"""

import csv
from pathlib import Path

MENTIONS_CSV = Path(__file__).parent.parent.parent / "veille" / "mentions.csv"

# Listes originales du sujet (TD 4.3)
MOTS_NEGATIFS_V1 = ["fraude", "amende", "condamne", "scandale", "plainte",
                     "liquidation", "faillite", "perquisition", "accuse"]
MOTS_POSITIFS_V1 = ["croissance", "benefice", "record", "acquisition", "innovation",
                     "nomination", "partenariat", "expansion", "investissement"]

# +3 mots negatifs / +3 positifs, choisis a partir des 2 vrais articles
# collectes (grève + annulation de trains) plutot que devines a l'aveugle.
MOTS_NEGATIFS_V2 = MOTS_NEGATIFS_V1 + ["grève", "annulation", "perturbé"]
MOTS_POSITIFS_V2 = MOTS_POSITIFS_V1 + ["bénéfice", "résultat", "hausse"]


def score(texte: str, mots_neg: list[str], mots_pos: list[str]) -> int:
    texte = texte.lower()
    neg = sum(1 for m in mots_neg if m in texte)
    pos = sum(1 for m in mots_pos if m in texte)
    return 1 if neg > pos else (2 if pos > neg else 0)


def main():
    with open(MENTIONS_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"{len(rows)} mentions dans {MENTIONS_CSV.name}\n")

    for row in rows:
        texte = row["titre"] + " " + row["resume"]
        s1 = score(texte, MOTS_NEGATIFS_V1, MOTS_POSITIFS_V1)
        s2 = score(texte, MOTS_NEGATIFS_V2, MOTS_POSITIFS_V2)
        print(f"[{row['source']}] {row['titre'][:70]}")
        print(f"  score original (v1) : {s1}   score recalibre (v2) : {s2}")
        print()


if __name__ == "__main__":
    main()
