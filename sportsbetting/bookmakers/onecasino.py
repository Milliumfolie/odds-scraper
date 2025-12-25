# -*- coding: utf-8 -*-
"""
Created on Sat Jun  7 12:12:31 2025

@author: Jorden
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# If you prefer webdriver-manager instead of Selenium Manager, uncomment these 2 lines:
# from webdriver_manager.chrome import ChromeDriverManager
# WDM = True  # set to False to use Selenium Manager (recommended since Selenium 4.6+)

import time
from datetime import datetime, timedelta, date

MONTHS_DUTCH = {
    "januari": 1, "februari": 2, "maart": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "augustus": 8, "september": 9, "oktober": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mrt": 3, "apr": 4, "mei": 5, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "okt": 10, "nov": 11, "dec": 12
}

def _make_driver(headless: bool = True) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # --- Option A: Selenium Manager (no hardcoded path; auto-matches Chrome 141) ---
    driver = webdriver.Chrome(options=options)

    # --- Option B: webdriver-manager (fallback) ---
    # if WDM:
    #     service = Service(ChromeDriverManager().install())
    #     driver = webdriver.Chrome(service=service, options=options)

    return driver

def _parse_dutch_date_label(label: str) -> date | None:
    """
    Accepts labels like 'Vandaag', 'Morgen', '10 juni', '10 juni 2025'.
    """
    label = label.strip().lower()

    if label == "vandaag":
        return datetime.today().date()
    if label == "morgen":
        return (datetime.today() + timedelta(days=1)).date()

    parts = label.split()
    try:
        if len(parts) == 2:
            day_str, month_str = parts
            year = datetime.today().year
        elif len(parts) == 3:
            day_str, month_str, year_str = parts
            year = int(year_str)
        else:
            return None

        day = int(day_str)
        month = MONTHS_DUTCH.get(month_str, 0)
        if month == 0:
            return None
        return datetime(year, month, day).date()
    except Exception:
        return None

def parse_onecasino(url: str, headless: bool = False):
    """Fetch page with Selenium and parse using `parse_onecasino_html`.

    Separating fetch and parse makes unit testing possible: `parse_onecasino_html`
    can be fed static HTML in tests without launching a browser.
    """
    driver = _make_driver(headless=headless)
    try:
        driver.get(url)
        # Wait for the main schedule blocks to appear
        wait = WebDriverWait(driver, 5)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.market-odd_odd")))
        html = driver.page_source
        # delegate parsing to html-based parser
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        parsed = parse_onecasino_html(soup)
        # Validate and normalize output
        from sportsbetting.parser_utils import validate_parser_output
        return validate_parser_output(parsed)
    except Exception as e:
        print(f"⚠️ Error fetching or parsing page: {e}")
        return {}
    finally:
        driver.quit()


def parse_onecasino_html(soup):
    """Parse a BeautifulSoup object and return the raw odds dict (non-normalized).

    Keep this function independent of Selenium so it can be tested with static HTML.
    """
    from sportsbetting.parser_utils import safe_text, parse_float
    odds_dict = {}

    date_items = soup.select(".date-item")

    for block in date_items:
        try:
            label_el = block.select_one(".date-title-label.text-truncate")
            label = safe_text(label_el, "").lower()
            event_date = _parse_dutch_date_label(label)
            if not event_date:
                print(f"⚠️ Could not parse date label: {label}")
                continue

            matches = block.select(".event-container")

            for match in matches:
                try:
                    home = safe_text(match.select_one(".event-team-home"))
                    away = safe_text(match.select_one(".event-team-away"))
                    event_name = f"{home} - {away}"
                    event_id = match.get("id")

                    # Start time (optional)
                    start_time = safe_text(match.select_one(".start-time"))

                    # Combine date + time
                    full_dt = None
                    if start_time:
                        try:
                            full_dt = datetime.strptime(f"{event_date} {start_time}", "%Y-%m-%d %H:%M")
                        except Exception:
                            full_dt = datetime.combine(event_date, datetime.min.time())

                    competition = "World Cup 2026 Qualifiers"

                    odds_elements = match.select(".market-odd_holder")
                    odds_list = []
                    for el in odds_elements[:3]:
                        # find element with odd
                        odd_el = el.select_one(".market-odd_odd")
                        val = parse_float(safe_text(odd_el))
                        if val is not None:
                            odds_list.append(val)

                    if len(odds_list) < 3:
                        print(f"⚠️ Skipping match '{event_name}' — one or more odds missing.")
                        continue

                    odds_dict[event_name] = {
                        "date": full_dt,
                        "odds": {"onecasino": odds_list},
                        "id": {"onecasino": event_id},
                        "competition": competition
                    }

                except Exception as e:
                    print(f"⚠️ Error parsing match: {e}")

        except Exception as e:
            print(f"⚠️ Error reading date block: {e}")

    return odds_dict

if __name__ == "__main__":
    url = 'https://sb.onecasino.com/nl/euro/sport/soccer/netherlands-eredivisie/200?tab=all'
    test = parse_onecasino(url, headless=False)
    print(test)
