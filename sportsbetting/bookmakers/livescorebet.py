"""
Livescorebet odds scraper
"""

from collections import defaultdict
from datetime import datetime
import json

import requests

import sys 
sys.path.append(r'C:\Users\jorden\Desktop\Sports-betting-master')

#import sportsbetting as sb
from sportsbetting.database_functions import (
    is_player_in_db, add_player_to_db, is_player_added_in_db,
    add_new_player_to_db, is_in_db_site, get_formatted_name_by_id, get_sport_by_url
)

def parse_livescorebet_api(url):
    """
    Get Livescorebet odds from a given URL for different sports.
    """
    sport = get_sport_by_url(url, 'livescorebet')
    
    try:
        data = requests.get(url).json()
    except requests.exceptions.RequestException as e:
        print(f"Error while requesting URL: {url}\nError: {e}")
        return {}
    
    odds_dict = {}
    try:
        for category in data["events"]["categories"]:
            
            competition = category["name"]
            for event in category["events"]:
                event_name = event["name"].replace(" Vs ", " - ").replace(" Vs. ", " - ").replace(" vs. ", " - ").replace(" vs ", " - ")  # replace 'Vs' with '-'
                start_date = datetime.strptime(event["startTime"], "%Y-%m-%d %H:%M:%S")  # convert to datetime
                
                # Create a dictionary to store odds
                odds = {}
                
                if sport == 'football':
                    odds = {'H': 1.01, 'D': 1.01, 'A': 1.01}
                    
                    for market in event["markets"]:
                        if market["name"] == "1X2":
                            for selection in market["selections"]:
                                odds_type = selection["outcomeType"]
                                decimal_odds = selection["odds"]
                                
                                # We only consider Home, Tie and Away odds
                                if odds_type in ["HOME", "TIE", "AWAY"]:
                                    if odds_type == "HOME":
                                        odds['H'] = decimal_odds
                                    elif odds_type == "TIE":
                                        odds['D'] = decimal_odds
                                    else:  # "AWAY"
                                        odds['A'] = decimal_odds
                                        
                    odds_list = list(odds.values())
                
                if sport == 'tennis' or sport == 'tennis' or sport == 'basketball' or sport == 'american-football':
                    odds = {'H': 1.01, 'A': 1.01}
                    
                    for market in event["markets"]:
                        if market["name"] == "Winner" or market["name"] == "Wedstrijdresultaat" or market["name"] == "Winnaar":
                            for selection in market["selections"]:
                                odds_type = selection["outcomeType"]
                                decimal_odds = selection["odds"]
                                if odds_type == "HOME":
                                    odds['H'] = decimal_odds
                                if odds_type == "AWAY":  # "AWAY"
                                    odds['A'] = decimal_odds
                                    
                    odds_list = list(odds.values())
                                
                odds_dict[event_name] = {
                    "date": start_date,
                    "odds": {"livescorebet": odds_list},
                    "id": {"livescorebet": event["id"]},
                    "competition": competition
                }
                
    except Exception as e:
        print(f"Error while processing event: {e}")
        return{}
        
    return odds_dict


def parse_livescorebet(url):
    """
    Get Livescorebet odds from url
    """
    if url:
        return parse_livescorebet_api(url)
    print("Wrong livescorebet url")
    return {}


def get_sub_markets_players_basketball_unibet(id_match):
    """
    Get submarkets odds from basketball match
    """
    if not id_match:
        return {}
    url = 'https://www.unibet.fr/zones/event.json?eventId=' + id_match
    content = requests.get(url).content
    parsed = json.loads(content)
    markets_class_list = parsed.get('marketClassList', [])
    markets_to_keep = {
        'Performance du Joueur (Points + Rebonds + Passes)':'Points + passes + rebonds',
        'Nombre de passes du joueur':'Passes',
        'Nombre de rebonds du joueur':'Rebonds',
        'Performance du Joueur (Points + Passes)':'Points + passes',
        'Performance du Joueur (Points + Rebonds)':'Points + rebonds',
        'Performance du Joueur (Passes + Rebonds)':'Passes + rebonds',
        "Joueur marquant 20 points ou plus":"Points",
        "Joueur marquant 25 points ou plus":"Points",
        "Joueur marquant 30 points ou plus":"Points",
        "Joueur marquant 35 points ou plus":"Points",
        "Joueur marquant 40 points ou plus":"Points",
        "Equipe à domicile - Nombre de 3 points marqués":"3 Points",
        "Equipe à l'exterieur - Nombre de 3 points marqués":"3 Points",
        "Nombre total de 3 pts marqués dans le match":"3 Points"
    }
    sub_markets = {v:defaultdict(list) for v in markets_to_keep.values()}
    for market_class_list in markets_class_list:
        market_name = market_class_list['marketName']
        if market_name not in markets_to_keep:
            continue
        markets = market_class_list['marketList']
        for market in markets:
            team_name = market.get("event{}Name".format(market["marketType"]
                                                        .split(" - ")[0]
                                                        .replace(" ", "")))
            id_team = is_in_db_site(team_name, "basketball", "unibet")
            if id_team:
                ref_player = get_formatted_name_by_id(id_team[0])
            is_3_pts = "3 points marqués" in market["marketName"]
            if "3 pts marqués" in market["marketName"]:
                ref_player = "Match"
                is_3_pts = True
            selections = market['selections']
            for selection in selections:
                price_up = int(selection['currentPriceUp'])
                price_down = int(selection['currentPriceDown'])
                odd = round(price_up / price_down + 1, 2)
                limit = selection['name'].split(' de ')[(-1)].replace(",", ".")
                plus = "Plus de" in selection['name']
                if not is_3_pts:
                    player = selection['name'].split(' - ')[0]
                    ref_player = player
                    if is_player_added_in_db(player, "unibet"):
                        ref_player = is_player_added_in_db(player, "unibet")
                    elif is_player_in_db(player):
                        add_player_to_db(player, "unibet")
                    else:
                        if sb.DB_MANAGEMENT:
                            print(player, "unibet")
                            add_new_player_to_db(player)
                        else:
                            continue
                key_market = markets_to_keep[market_name]
                if key_market == "Points":
                    limit = str(float(market_name.split()[2])-0.5)
                key_player = ref_player + "_" + limit
                if key_player not in sub_markets[key_market]:
                    sub_markets[key_market][key_player] = {"odds":{"unibet":[]}}
                if plus:
                    sub_markets[key_market][key_player]["odds"]["unibet"].insert(0, odd)
                else:
                    sub_markets[key_market][key_player]["odds"]["unibet"].append(odd)
                if key_market == "Points":
                    sub_markets[key_market][key_player]["odds"]["unibet"].append(1.01)
    for sub_market in sub_markets:
        sub_markets[sub_market] = dict(sub_markets[sub_market])
    return sub_markets


def get_sub_markets_players_football_livescorebet(id_match):
    """
    Get submarkets odds from basketball match
    """
    if not id_match:
        return {}
    url = 'https://gateway-nl.livescorebet.com/sportsbook/gateway/v1/view/event?eventid=' + str(id_match)
    content = requests.get(url).content
    parsed = json.loads(content)
    markets_class_list = parsed['event']
    event_name = parsed['event']['name'].replace(" Vs "," - ").replace(" vs "," - ")
    team_A, team_B = event_name.split(" - ")
    
    markets_to_keep = {
        'Totaal aantal doelpunten':'Total Goals',
        'Totaal aantal doelpunten - 1e helft':'Total Goals 1st half',
        'Totaal aantal doelpunten - 2e helft':'Total Goals 2nd half',
        'Schoten op Doel Specials':'Shots on target by',
        #'Total Goals - 1st Half':'Total Goals 1st half',
        #'Total Goals - 2nd Half':'Total Goals 2nd half',
        #'Both Teams To Score - 1st Half':'Both Teams To Score - 1st Half',
        #'Both Teams To Score - 2nd Half':'Both Teams To Score - 2nd Half',
        #'Both Teams to Score in both halves':'Both Teams to Score in both halves',
        #'Goal in both halves':'Goal in both halves',
        #'Draw No Bet':'Draw No Bet',
        #'Draw and both teams to score':'Draw and both to score',
        #'Total Shots on Target (Settled using Opta data)':'Shots on target',
        'Total Shots on Target by {}'.format(team_A):'Shots on target by',
        'Total Shots on Target by {}'.format(team_B):'Shots on target by',
        '{} totaal aantal doelpunten'.format(team_A.split(' ')[-1]):'Total Goals by',
        '{} totaal aantal doelpunten'.format(team_B.split(' ')[-1]):'Total Goals by',
         #'To score':'To score'
    }
    
    
    sub_markets = {v:defaultdict(list) for v in markets_to_keep.values()}
    for market_class_list in markets_class_list['markets']:
        market_name = market_class_list['name']
        
        print(market_name)

        if market_name not in markets_to_keep:
            continue
        
        marketkind = "OU"
        
        if market_name == 'Totaal aantal doelpunten' or market_name == 'Totaal aantal doelpunten - 2e helft' or 'Total Goals by' in markets_to_keep[market_name]:
            try: 
                marketkind = market_class_list['marketKind']
            except:
                continue
            
        if marketkind == "OU":
            pass
        else:
            continue
        
        selections = market_class_list['selections']
        for selection in selections:
            
            if market_name == "Schoten op Doel Specials" or "Total Goals by" in markets_to_keep[market_name]:
                if team_A in selection['name'] or team_A in market_name:
                    team_name = team_A
                elif team_B in selection['name'] or team_B in market_name:
                    team_name = team_B
                else:
                    team_name = 'Match'
                    
                id_team = is_in_db_site(team_name, "football", "livescorebet")
                if id_team:
                    ref_player = get_formatted_name_by_id(id_team[0])
                else:
                    continue 
            else:
                ref_player = 'Match'
            
            try:
                odd = float(selection['odds'])
            except:
                odd = float(1)   
            plus = False
            
            if "totaal" in market_name.lower():
                try:
                    limit = selection['hcp']
                    plus = "OVER" in selection['outcomeType']
                except:
                    continue
            
            elif 'Schoten op Doel' or 'Total Number of Goals' in market_name:
                limit = ''.join([s for s in list(selection['name']) if s.isdigit()])
                limit = str(float(limit)-0.5)
                
            else:    
                limit = None
                
            key_player = ref_player
            key_market = markets_to_keep[market_name]
            
            if key_market == "Points":
                limit = str(selection['name'].split()[1].strip('+')) 
            if limit:
                key_player = ref_player + "_" + limit
            if key_player not in sub_markets[key_market]:
                sub_markets[key_market][key_player] = {"odds":{"livescorebet":[]}}
            if plus:
                sub_markets[key_market][key_player]["odds"]["livescorebet"].insert(0, odd)
            else:
                sub_markets[key_market][key_player]["odds"]["livescorebet"].append(odd)            
            if "Shots on target" in key_market:
                sub_markets[key_market][key_player]["odds"]["livescorebet"].append(1.01)
                
    for sub_market in sub_markets:
        sub_markets[sub_market] = dict(sub_markets[sub_market])
        
    sub_markets.pop('Totaal aantal doelpunten', None)
    return sub_markets

if __name__ == "__main__":
    #est = get_sub_markets_players_football_livescorebet("SBTE_27764439")
    test = parse_livescorebet_api("https://gateway-nl.livescorebet.com/sportsbook/gateway/v1/view/events/matches?categoryid=SBTC3_88808&interval=ALL&lang=nl-nl")
    #parse_competitions(["Dutch Eredivisie", "French Ligue 1", "Italy Serie A", "England Premier League", "Germany Bundesliga", "Spanish La Liga"], "football", "livescorbet")