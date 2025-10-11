# -*- coding: utf-8 -*-
"""
Created on Sat Jun  7 12:12:31 2025

@author: Jorden
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

from datetime import datetime
from datetime import timedelta

MONTHS_DUTCH = {
    "januari": 1, "februari": 2, "maart": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "augustus": 8, "september": 9, "oktober": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mrt": 3, "apr": 4, "mei": 5, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "okt": 10, "nov": 11, "dec": 12
}

CHROMEDRIVER_PATH = r'C:\Users\Jorden\Desktop\Staging\chromedriver.exe'


def parse_onecasino(url, headless=True):
    chromedriver_path = r'C:\Users\Jorden\Desktop\Staging\chromedriver.exe'
    
    options = Options()
    #options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")

    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)

    odds_dict = {}

    try:
        driver.get(url)
        time.sleep(5)

        date_items = driver.find_elements(By.CLASS_NAME, "date-item")

        for block in date_items:
            try:
                # Get the date label (e.g., "Vandaag", "Morgen", "10 juni")
                label = block.find_element(By.CSS_SELECTOR, ".date-title-label.text-truncate").text.strip().lower()
                print(label)
                
                # Convert to datetime.date
                if label == "vandaag":
                    event_date = datetime.today().date()
                elif label == "morgen":
                    event_date = (datetime.today() + timedelta(days=1)).date()
                else:
                    try:
                        
                        day_str, month_str, year_str = label.split()
                        print(day_str)
                        print(month_str)
                        day = int(day_str)
                        month = MONTHS_DUTCH.get(month_str, 0)
                        year = datetime.today().year
                        event_date = datetime(year, month, day).date()
                    except:
                        print(f"⚠️ Could not parse date label: {label}")
                        continue

                matches = block.find_elements(By.CLASS_NAME, "event-container")

                for match in matches:
                    try:
                        home = match.find_element(By.CLASS_NAME, "event-team-home").text.strip()
                        away = match.find_element(By.CLASS_NAME, "event-team-away").text.strip()
                        event_name = f"{home} - {away}"
                        event_id = match.get_attribute("id")

                        try:
                            start_time = match.find_element(By.CLASS_NAME, "start-time").text.strip()
                        except:
                            start_time = ""

                        # Combine date + time
                        if start_time:
                            try:
                                full_dt = datetime.strptime(f"{event_date} {start_time}", "%Y-%m-%d %H:%M")
                            except:
                                full_dt = None
                        else:
                            full_dt = None

                        competition = "World Cup 2026 Qualifiers"
                        odds_elements = match.find_elements(By.CLASS_NAME, "market-odd_holder")
                        
                        odds_list = []
                        valid = True

                        for el in odds_elements[:3]:
                            try:
                                val = el.find_element(By.CLASS_NAME, "market-odd_odd").text.strip()
                                odds_list.append(float(val))
                            except:
                                valid = False
                                
                        if not valid:
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

    finally:
        driver.quit()

    return odds_dict

if __name__ == "__main__":
    url = 'https://sb.onecasino.com/nl/euro/sport/soccer/netherlands-eredivisie/200?tab=all'
    test = parse_onecasino(url)