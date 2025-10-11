# -*- coding: utf-8 -*-
"""
Created on Sat May  6 12:36:40 2023
@author: Admin
"""
#import sys
import os
import re

import json
import datetime
import requests

# import sys 
# sys.path.append(r'C:\Users\Jorden\Desktop\Sports-betting-master')
# import sportsbetting as sb

def create_odds_dict(sports_data):
    """
    Creates a dictionary of match odds from sports data.
    
    :param sports_data: A dictionary containing sports data.
    :return: A dictionary with match odds.
    """
    match_odds_hash = {}

    for match in sports_data['eventList'].get('prematch', []):
        event_name = match.get('name')
        
        # Parse and validate the event date
        try:
            event_date_str = match.get('startDate', '')
            event_date = datetime.datetime.strptime(event_date_str, "%Y-%m-%d %H:%M:%S") if event_date_str else None
        except ValueError:
            # Log or handle the invalid date format
            print(f"Invalid date format for event: {event_name}")
            continue  # Skip to the next match if date is invalid
            
        valid_subbet_found = False  # Flag to check if a valid subbet is found
        odds_data = {}
        for subbet in match.get('importantSubbets', []):
            if not subbet:
                continue
    
            if subbet.get('name') == '1X2' or subbet.get('name') == 'Winnaar':
                # Convert odds to floats and handle missing or invalid data gracefully
                odds = [float(tip.get('odd', 0)) for tip in subbet.get('tips', [])]
                valid_subbet_found = True
                break  # Stop iterating if a valid subbet is found
    
        if not valid_subbet_found:
            continue  # Skip to the next match if no valid subbet is found
    
        competition_name = match.get('parents', {}).get('division', {}).get('name', 'Unknown Competition')
    
        match_odds_hash[event_name] = {
            'date': event_date,
            'odds': {'bingoal': odds},
            'id': {'bingoal': match.get('id', 'Unknown ID')},
            'competition': competition_name,
        }


    return match_odds_hash

def parse_bingoal(url):

    # Start a session
    session = requests.Session()
    
    try:
        # Make the initial request to the URL
        response = session.get("https://www.bingoal.nl/nl/Sport")
        page_source = response.text
    
        # Extract the _k value or other data from the page
        k_pattern = re.compile(r"_k\s*=\s*'([^']+)'")
        k_match = k_pattern.search(page_source)
        k_value = k_match.group(1) if k_match else None
    
        # Find and manage specific cookies if necessary
        csp_cookie = next((cookie for cookie in session.cookies if cookie.name == 'CSPSESSIONID-SP-80-UP-'), None)
        
        # Print the CSP Cookie
        # if csp_cookie:
        #     print("CSP Cookie:", csp_cookie)
        # else:
        #     print("CSP Cookie not found.")
            
        # Make an AJAX request to get the Authorization token
        token_url = "https://www.bingoal.nl/ajax/user.getToken"
        ajax_response = session.get(token_url)  # or use session.post(token_url) if required
    
        # Check if the AJAX request was successful
        if ajax_response.status_code == 200:
            # Assuming the response contains a JSON with the token
            token_info = ajax_response.json()
            auth_token = token_info.get("token")  # Change key according to actual response structure
            session_id = token_info.get("CSPCHD")  # Change key according to actual response structure
            #print("Session ID:", session_id)
            #print("Authorization Token:", auth_token)
        else:
            print("Failed to get token, status code:", ajax_response.status_code)

        
        # Prepare the headers with your authorization token
        headers = {
            "Authorization": f"Basic {auth_token}",  # Ensure this is the correct format for your token
        }
        
        odds_dict = session.get(url, headers=headers).json()
        odds_dict = create_odds_dict(odds_dict)
        return odds_dict
        
    except Exception as e:
        print(f"Failed to use Requests: {e}")
        return {}
        
if __name__ == "__main__":
    test = parse_bingoal('https://www.bingoal.nl/ajax/sport.getSportV2?type=prematch&sport=TENNIS&region=ATP&division=ATPAUSOPEN')