#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Defi 2 - Detecter les nouveautes entre deux crawls (code fourni par le sujet)."""

import csv


def charger_urls(chemin: str) -> set:
    with open(chemin, encoding="utf-8") as f:
        return {row["url"] for row in csv.DictReader(f)}


def diff_scrapes(csv_ancien: str, csv_nouveau: str) -> dict:
    anciens = charger_urls(csv_ancien)
    nouveaux = charger_urls(csv_nouveau)
    return {
        "nouveaux": sorted(nouveaux - anciens),
        "disparus": sorted(anciens - nouveaux),
        "inchanges": len(anciens & nouveaux),
    }


if __name__ == "__main__":
    import sys

    r = diff_scrapes(sys.argv[1], sys.argv[2])
    print(f"Nouveaux : {len(r['nouveaux'])}")
    print(f"Disparus : {len(r['disparus'])}")
    print(f"Stables  : {r['inchanges']}")
    for url in r["nouveaux"]:
        print(f"  [+] {url}")
    for url in r["disparus"]:
        print(f"  [-] {url}")
