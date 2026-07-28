#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Defi 3 - robustesse face aux changements de site

Compare deux exports JSON pris a des dates differentes (meme scraper, pas de
modif entre les deux) et liste ce qui a disparu/apparu et quels champs sont
passes a "n/a" (= un selecteur ne trouve plus rien). Voir NOTES.md.

python doctolib_scraper.py --specialty cardiologue --city lyon --output j0.json
# 3 jours plus tard, sans toucher au code
python doctolib_scraper.py --specialty cardiologue --city lyon --output j3.json
python snapshot_diff.py j0.json j3.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load(path: str) -> dict[str, dict]:
    with open(path, encoding="utf-8") as f:
        records = json.load(f)
    key_field = "url_fiche" if "url_fiche" in (records[0] if records else {}) else "titre"
    return {r.get(key_field, i): r for i, r in enumerate(records)}


def diff(old_path: str, new_path: str) -> None:
    old = load(old_path)
    new = load(new_path)

    disparus = old.keys() - new.keys()
    apparus = new.keys() - old.keys()
    communs = old.keys() & new.keys()

    print(f"Fiches communes : {len(communs)}")
    print(f"Disparues       : {len(disparus)}")
    print(f"Nouvelles       : {len(apparus)}")

    champs_casses: dict[str, int] = {}
    for key in communs:
        for champ, valeur in new[key].items():
            ancienne_valeur = old[key].get(champ)
            etait_ok = ancienne_valeur not in ("n/a", "", None, [], ["n/a"])
            est_cassee = valeur in ("n/a", "", None, [], ["n/a"])
            if etait_ok and est_cassee:
                champs_casses[champ] = champs_casses.get(champ, 0) + 1

    if champs_casses:
        print("\nChamps devenus 'n/a' entre les deux runs (selecteur probablement casse) :")
        for champ, count in sorted(champs_casses.items(), key=lambda kv: -kv[1]):
            print(f"  - {champ} : {count} fiche(s)")
    else:
        print("\nAucun champ n'est devenu 'n/a' entre les deux runs.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage : python snapshot_diff.py ancien.json nouveau.json")
        sys.exit(1)
    diff(sys.argv[1], sys.argv[2])
