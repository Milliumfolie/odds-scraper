"""
Toto odds scraper
"""
from collections import defaultdict
from datetime import datetime
import json

import sys
sys.path.append(r'C:\Users\Jorden\Desktop\Staging')

import re
import requests

from sportsbetting.database_functions import (
    get_sport_by_url
)

import sportsbetting as sb
from sportsbetting.database_functions import (
    is_player_in_db, add_player_to_db, is_player_added_in_db,
    add_close_player_to_db, get_sport_by_url, is_in_db_site, get_formatted_name_by_id
)


def parse_toto_api(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                   'Cookie': 'visid_incap_2280939=+szz8WCnQPO//pGIGXQsb0RKkWUAAAAAQUIPAAAAAACqUGiFayL/tNKNPai4ndst; incap_ses_1077_2280939=kY09ZzgHqEnuFuk6ikbyDmlKkWUAAAAAxCmw61iiKbW1JCXsCWis3g==; path=/; Domain=.toto.nl'}
        data = requests.get(url, headers=headers, timeout=3)
        data = data.json()
    except requests.exceptions.RequestException as e:
        print(f"Error while requesting URL: {url}\nError: {e}")
        return {}
    
    except requests.Timeout:
        print("The request timed out")
        return{}
    
    sport = get_sport_by_url(url, 'toto')
    odds_dict = {}
    try:
        
        for event in data.get("data", {}).get("events", []):
            event_name = event.get("name", "").replace(" v ", " - ")  # replace 'v' with '-'
            start_date = datetime.strptime(event.get("startTime", ""), "%Y-%m-%dT%H:%M:%SZ")  # convert to datetime
            competition = event.get("type", {}).get("name", "")

            # Create a dictionary to store odds
            odds = {}
            
            if sport == 'football':
                odds = {'H': 1.01, 'D': 1.01, 'A': 1.01}
    
                for market in event.get("markets", []):
                    for outcome in market.get("outcomes", []):
                        odds_type = outcome.get("subType")
                        decimal_odds = outcome.get("prices", [{}])[0].get("decimal")
    
                        if odds_type in odds:  # only update if odds_type is H, D, or A
                            odds[odds_type] = decimal_odds
    
                odds_list = list(odds.values())
            
            if sport == 'tennis' or sport == 'tennis' or sport == 'basketball' or sport == 'american-football':
                odds = {'H': 1.01, 'A': 1.01}
    
                for market in event.get("markets", []):
                    if market['name'] == 'Money Line':
                        for outcome in market.get("outcomes", []):
                            odds_type = outcome.get("subType")
                            decimal_odds = outcome.get("prices", [{}])[0].get("decimal")
        
                            if odds_type in odds:  # only update if odds_type is H, D, or A
                                odds[odds_type] = decimal_odds
        
                    odds_list = list(odds.values())

            odds_dict[event_name] = {
                "date": start_date,
                "odds": {"toto": odds_list},
                "id": {"toto": event.get("id")},
                "competition": competition
            }
    except Exception as e:
        print(f"Error while processing event: \nError: {e}")
        return {}

    return odds_dict
        

def parse_toto(url):
    """
    Get Unibet odds from url
    """
    #id_league, sport = get_id_league(url)
    if url:
        return parse_toto_api(url)
    print("Wrong toto url")
    return {}


def get_sub_markets_football_toto(id_match):
    """
    Get submarkets odds from football match
    """
    if not id_match:
        return {}
    url = 'https://content.toto.nl/content-service/api/v1/q/events-by-ids?eventIds={}&includeChildMarkets=true&includeCollections=true&includePriceHistory=false&includeCommentary=true&includeIncidents=false&includeRace=false&includeMedia=true&includePools=false'.format(id_match)
    content = requests.get(url).content
    data = json.loads(content)['data']
    
    team_A = data.get('events', [{}])[0]['teams'][0].get('name', '')
    team_B = data.get('events', [{}])[0]['teams'][1].get('name', '')
    
    # Check if both teams exist in the database
    id_team_A = is_in_db_site(team_A, "football", "toto")
    id_team_B = is_in_db_site(team_B, "football", "toto")
    
    if not id_team_A or not id_team_B:
        return {}  
    
    # Get formatted names
    team_A = get_formatted_name_by_id(id_team_A[0])
    team_B = get_formatted_name_by_id(id_team_B[0])
        

    markets_to_keep = {
        'Total Goals Over/Under': 'Total Goals',
        '1st Half Total Goals Over/Under': 'Total Goals 1st Half',
        '2nd Half Total Goals Over/Under': 'Total Goals 2nd Half',
        #'Schot op doel': 'Shots on target',
        #f'Totaal aantal schoten op doel door {team_A} (afgehandeld volgens Opta-gegevens)': f'Shots on target by',
        #f'Totaal aantal schoten op doel door {team_B} (afgehandeld volgens Opta-gegevens)': f'Shots on target by',
        f'{team_A} Total Goals Over/Under': f'Total Goals by',
        f'{team_B} Total Goals Over/Under': f'Total Goals by',
        f'Half Time {team_A} Total Goals Over/Under': f'Total Goals by 1st Half',
        f'Half Time {team_B} Total Goals Over/Under': f'Total Goals by 1st Half',
        #'Totaal aantal schoten (afgehandeld volgens Opta-gegevens)': 'Total Shots',
        #f'Totaal aantal schoten door {team_A} (afgehandeld volgens Opta-gegevens)': f'Total Shots by',
        #f'Totaal aantal schoten door {team_B} (afgehandeld volgens Opta-gegevens)': f'Total Shots by',
        #'Both Teams to Score': 'Both Teams to Score',
        'Both Teams to Score in 1st Half': 'Both Teams to Score 1st Half',
        '2nd Half Both Teams to Score': 'Both Teams to Score 2nd Half',
        #'Asian Handicap': 'Asian Handicap',
        #'Asian Handicap – 1e Helft': 'Asian Handicap 1st Half',
        #'Asian Totaal': 'Asian Total',
        #'Asian Totaal - 1e Helft': 'Asian Total 1st Half', 
        'Draw No Bet': 'Draw No Bet',
        'Half Time Draw No Bet': 'Draw No Bet 1st Half',
        '2nd Half Draw No Bet': 'Draw No Bet 2nd Half'
    }
    
    def find_market_key(market_name, team_A, team_B):
        for key, value in markets_to_keep.items():
            if market_name.startswith(key.replace('{team_A}', team_A).replace('{team_B}', team_B)):
                return value
        return None
    
    
    sub_markets = {v:defaultdict(list) for v in markets_to_keep.values()}
    for market_class_list in data['events'][0]['markets']:
        market_name = market_class_list['name']
        #print(market_name)
        
        market_key = find_market_key(market_name, team_A, team_B)
        if not market_key or " After " in market_name:
            continue
        
        print(market_name)
        
        if team_A in market_name:
            ref_player = team_A
        elif team_B in market_name:
            ref_player = team_B
        else:
            ref_player = "Match"
            
        selections = market_class_list['outcomes']

        for selection in selections:
            limit = None
            try:
                odd = selection['prices'][0]['decimal']
            except:
                odd = float(1.01)
            if "Over/Under" in market_name:
                limit = str(market_class_list['handicapValue'])
        
            plus = "Over" in selection['name']
            key_player = ref_player
            key_market = market_key
        
            if len(selections) == 1:
                odds = [odd, 1.01]  # Add both values to the list directly
        
            if limit:
                key_player = ref_player + "_" + limit
            if key_player not in sub_markets[key_market]:
                sub_markets[key_market][key_player] = {"odds": {"toto": []}}
            if len(selections) == 1:
                sub_markets[key_market][key_player]["odds"]["toto"] = odds
            else:
                if plus:
                    sub_markets[key_market][key_player]["odds"]["toto"].insert(0, odd)
                else:
                    sub_markets[key_market][key_player]["odds"]["toto"].append(odd)
        
        for sub_market in sub_markets:
            sub_markets[sub_market] = dict(sub_markets[sub_market])
        
    return sub_markets


def get_player_props_football_toto(id_match):
    """
    Get submarkets odds from football match
    """
    if not id_match:
        return {}
    url = 'https://content.toto.nl/content-service/api/v1/q/events-by-ids?eventIds={}&includeChildMarkets=true&includeCollections=true&includePriceHistory=false&includeCommentary=true&includeIncidents=false&includeRace=false&includeMedia=true&includePools=false'.format(id_match)
    content = requests.get(url).content
    data = json.loads(content)['data']

    markets_to_keep = {
        'Schot op doel': 'Speler schoten op doel',
    }
    
    sub_markets = {v:defaultdict(list) for v in markets_to_keep.values()}
    
    for market_class_list in data['events'][0]['markets']:
        market_name = market_class_list['name']
        print(market_name)
        
        if market_name in markets_to_keep:
            print(market_name)
                     
            selections = market_class_list['outcomes']
            for selection in selections:
                try:
                    odd = selection['prices'][0]['decimal']
                except:
                    odd = float(1.01)
                
                # extract the limit using regex
                match = re.search(r"\d+", selection['name'])
                if match:
                    limit = float(match.group())-0.5
                else:
                    continue
                
                # Extract the name and number using regex
                match = re.search(r"(\D+) \d+", selection['name'])
                if match:
                    ref_player = match.group(1)
                    print("Extracted name:", ref_player)
                else:
                    continue
                
                if is_player_in_db(ref_player):
                    ref_player = is_player_added_in_db(ref_player, "toto")
                else:
                    add_close_player_to_db(ref_player, "toto")
                    ref_player = is_player_added_in_db(ref_player, "toto")
                
                if ref_player == None:
                    continue
                
                key_player = ref_player + "_" + str(limit)
                key_market = markets_to_keep[market_name]
                odds = [odd, 1.01]  # Add both values to the list directly    
                
                if key_player not in sub_markets[key_market]:
                    sub_markets[key_market][key_player] = {"odds": {"toto": []}}
                #if len(selections) == 1:
                    sub_markets[key_market][key_player]["odds"]["toto"] = odds
                else:
                    sub_markets[key_market][key_player]["odds"]["toto"].insert(0, odd)

            for sub_market in sub_markets:
                sub_markets[sub_market] = dict(sub_markets[sub_market])
            
    return sub_markets


if __name__ == "__main__":
    #test = parse_toto_api('https://content.toto.nl/content-service/api/v1/q/event-list?maxMarkets=10&orderMarketsBy=displayOrder&marketSortsIncluded=--%2CMR&marketGroupTypesIncluded=MATCH_RESULT%2CROLLING_SPREAD%2CROLLING_TOTAL%2CSTATIC_SPREAD%2CSTATIC_TOTAL&eventSortsIncluded=MTCH&includeChildMarkets=true&drilldownTagIds=656')
    test = get_sub_markets_football_toto(6960105)