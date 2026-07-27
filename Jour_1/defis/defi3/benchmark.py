#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Defi 3 - Benchmark honnete du throttling (reutilise scraper_bdm.py)."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scraper_bdm import get_page, page_url, parse_articles  # noqa: E402


def benchmark(n_pages: int, delay: float) -> tuple[float, int]:
    t0 = time.time()
    total_articles = 0
    for page in range(1, n_pages + 1):
        soup = get_page(page_url(page))
        if soup is not None:
            total_articles += len(parse_articles(soup))
        if page < n_pages:
            time.sleep(delay)
    return time.time() - t0, total_articles


if __name__ == "__main__":
    pages_list = [2, 5, 10]
    delays = [0.5, 1.0, 2.0]
    resultats = {}

    for n in pages_list:
        for d in delays:
            duree, nb = benchmark(n, d)
            resultats[(n, d)] = duree
            print(f"pages={n:>2} delay={d}s -> {duree:.1f}s pour {nb} articles")

    print("\n# Pages | 0.5 s | 1.0 s | 2.0 s")
    for n in pages_list:
        ligne = " | ".join(f"{resultats[(n, d)]:.1f}s" for d in delays)
        print(f"# {n:>4}  | {ligne}")
