#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Defi 2 - empreinte anti-bot

Compare Chrome/Selenium normal, avec flags anti-detection, et en headless
contre bot.sannysoft.com. Un screenshot par config -> voir ANALYSE.md.

python bot_fingerprint.py
"""

from __future__ import annotations

import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By

URL = "https://bot.sannysoft.com"
OUTPUT_DIR = Path(__file__).parent


def run(label: str, headless: bool, stealth: bool) -> bool:
    opts = webdriver.ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
    if stealth:
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])

    try:
        driver = webdriver.Chrome(options=opts)
    except Exception as err:
        print(f"[{label}] Chrome n'a pas pu demarrer : {err}")
        return False

    try:
        driver.get(URL)
        time.sleep(2)  # laisser les tests JS de la page tourner
        screenshot_path = OUTPUT_DIR / f"{label}.png"
        driver.save_screenshot(str(screenshot_path))
        print(f"[{label}] screenshot -> {screenshot_path}")

        webdriver_flag = driver.execute_script("return navigator.webdriver")
        print(f"[{label}] navigator.webdriver = {webdriver_flag}")
        return True
    except Exception as err:
        print(f"[{label}] Echec en cours de route : {err}")
        return False
    finally:
        driver.quit()


def main() -> None:
    run("normal", headless=False, stealth=False)
    run("stealth", headless=False, stealth=True)
    run("headless_sans_stealth", headless=True, stealth=False)
    run("headless_stealth", headless=True, stealth=True)


if __name__ == "__main__":
    main()
