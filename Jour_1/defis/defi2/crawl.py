#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Defi 2 - lance un crawl horodate (reutilise scraper_bdm.py, pas de copier-coller)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scraper_bdm import scrape_all, sauver_csv  # noqa: E402

if __name__ == "__main__":
    sortie = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    articles = scrape_all(n)
    sauver_csv(articles, sortie)
