# -*- coding: utf-8 -*-
"""
Created on Sat Sep 23 18:14:50 2023

@author: Jorden
"""
import json
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

# Constants
DEFAULT_BASE_URL = "https://oddsbeater.nl/wedden/voetbal/nederland/eredivisie"
API_URL_PATTERN = 'https://oddsbeater.nl/api/oddsData'
ODDS_PROVIDER_ID = 23

def configure_driver():
    # Detecting the operating system
    if os.name == "nt":  # For Windows
        CHROMEDRIVER_PATH = "chromedriver.exe"
    else:  # For Linux and other Unix-like OS
        CHROMEDRIVER_PATH = "/usr/bin/chromedriver"  # System will find it in the PATH
        
    service_obj = Service(executable_path=CHROMEDRIVER_PATH)
    chrome_options = Options()
    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    chrome_options.add_argument("--headless")  # This line sets up headless mode
    driver = webdriver.Chrome(service=service_obj, options=chrome_options)
    return driver


def process_log(log, driver):
    try:
        log_data = json.loads(log["message"])["message"]
        
        if "Network.responseReceived" in log_data["method"] and "params" in log_data:
            url = log_data["params"]["response"]["url"]
            
            if API_URL_PATTERN in url:
                body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': log_data["params"]["requestId"]})
                return body.get("body", None)
    except Exception as e:
        #print(f"Error processing log: {e}")
        pass
    return None


def get_odds_data_dict(driver):
    logs = driver.get_log('performance')
    responses = [process_log(log, driver) for log in logs if process_log(log, driver)]
    odds_data = [json.loads(response) for response in responses]
    return {entry['odds'][0]['betObjectId']: entry for entry in odds_data if 'odds' in entry and len(entry['odds']) > 0}


def get_page_data(driver):
    script_element = driver.find_element(By.ID, "__NEXT_DATA__")
    data_json_str = script_element.get_attribute("innerHTML")
    return json.loads(data_json_str)


def build_odds_dict(events_list, odds_data_dict, competition):
    odds_dict = {}

    for date, events in events_list:
        for event in events:
            # Extract event details
            match_id, start_date_str, teams = event.get('id'), event.get('startdate'), event.get('participant', [])
            
            if not (match_id and start_date_str and len(teams) >= 2):
                continue

            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            except Exception as e:
                print(f"Failed to parse start date {start_date_str}: {e}")
                continue

            event_name = f"{teams[0].get('name', '')} - {teams[1].get('name', '')}"
            odds_data = odds_data_dict.get(match_id)
            team_ids = {team.get('id'): team.get('name', '') for team in teams}
            odds_list = []

            for item in odds_data.get('odds', []):
                for odd in item.get('odds', []):
                    if odd.get('oddsProvider') == ODDS_PROVIDER_ID:
                        team_id, odds = item.get('iparam'), odd.get('quote')
                        if team_id is not None and odds is not None:
                            odds_list.append((team_id, float(odds)))

            if odds_list:
                sorted_odds_list = [1.01, 1.01, 1.01]
                for team_id, odds in odds_list:
                    if team_id == 0:
                        sorted_odds_list[1] = odds
                    else:
                        team_name = team_ids.get(team_id)
                        if team_name:
                            team_names = [name.strip() for name in event_name.split(' - ')]
                            index = team_names.index(team_name)
                            if index == 0:
                                sorted_odds_list[0] = odds
                            else:
                                sorted_odds_list[2] = odds

                odds_dict[event_name] = {
                    'date': start_date,
                    'odds': {'bet365': sorted_odds_list},
                    'id': {'bet365': match_id},
                    'competition': competition
                }

    return odds_dict

def parse_oddsbeater(base_url=DEFAULT_BASE_URL):
    driver = configure_driver()
    driver.get(base_url)
    # Wait for the age verification button and click it
    try:
        age_verification_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, '//button[text()="Ik ben 24 jaar of ouder"]'))
        )
        #age_verification_button.click()
    except Exception as e:
        print("Failed to click the age verification button:", e)
        driver.close()  # Close the browser if there's an error
        return {}
    
    try:
        odds_data_dict = get_odds_data_dict(driver)
        page_data = get_page_data(driver)
    
        driver.close()
    
        page_props = page_data.get('props', {})
        events_list = page_props.get('pageProps', {}).get('eventsList', [])
        competition = page_props.get('pageProps', {}).get('leagueDetail', {}).get('name', "")
        return build_odds_dict(events_list, odds_data_dict, competition)
    except:
        return {}

if __name__ == "__main__":
    test = parse_oddsbeater("https://oddsbeater.nl/wedden/voetbal/engeland/premier-league")