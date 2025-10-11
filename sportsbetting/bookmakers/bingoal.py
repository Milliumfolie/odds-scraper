"""
bingoal odds scraper
"""
from collections import defaultdict
import datetime

import json
import sys 
sys.path.append(r'C:\Users\Jorden\Desktop\Staging')

import requests

import sportsbetting as sb
from sportsbetting.database_functions import (
    is_player_in_db, add_player_to_db, is_player_added_in_db,
    add_new_player_to_db, is_in_db_site, get_formatted_name_by_id, add_close_player_to_db, get_sport_by_url
)


def parse_bingoal_api(url):
    """
    Get bingoal odds from league id and sport.
    Args:
        url (str): The URL to the bingoal API.
    Returns:
        dict: A dictionary containing the parsed odds data.
    Raises:
        requests.exceptions.RequestException: If the request to the API fails.
    """
    
    sport = get_sport_by_url(url, 'bingoal')
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        matches = data.get("events", [])
        odds_by_match = {}

        for match in matches:
            event = match.get("event", {})
            bet_offers = match.get("betOffers", [])

            name = event.get("name")
            date = datetime.datetime.fromisoformat(event["start"].strip("Z"))
            competition = event.get("group")

            match_odds = []
            if sport == 'football':
                for bet_offer in bet_offers:
                    outcomes = bet_offer.get("outcomes", [])
    
                    for outcome in outcomes:
                        if outcome.get("status") == "OPEN":
                            match_odds.append(outcome["odds"] / 1000)
                        else:
                            match_odds.append(1000)
            
            if sport == 'tennis' or sport == 'tennis' or sport == 'basketball' or sport == 'american-football':
                for bet_offer in bet_offers:
                    outcomes = bet_offer.get("outcomes", [])
                    
                    for outcome in outcomes:
                        if outcome.get("status") == "OPEN":
                            match_odds.append(outcome["odds"] / 1000)
                        else:
                            match_odds.append(1000)
                    if len(match_odds) >= 2:
                        break
                
            odds_by_match[name] = {
                "date": date,
                "odds": {"bingoal": match_odds},
                "id": {"bingoal": event["id"]},
                "competition": competition
            }

        return odds_by_match

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"JSON error: {e}")
        return {}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {}


def parse_bingoal(url):
    """
    Get bingoal odds from url
    """
    if url:
        return parse_bingoal_api(url)
    print("Wrong unibet url")
    return {}


def get_ref_player(market_name, team_A, team_B):
    if market_name == 'Total Goals':
        return 'Match'
    elif 'Total Shots on Target by' in market_name or 'Total Goals by' in market_name:
        team_name = team_A if team_A in market_name else team_B
        id_team = is_in_db_site(team_name, 'football', 'bingoal')
        if id_team:
            return get_formatted_name_by_id(id_team[0])
        else:
            return 'Match'
    elif 'To score' in market_name:
        player = market_class_list['outcomes'][0]['participant']
        ref_player = player
        if is_player_added_in_db(player, 'bingoal'):
            ref_player = is_player_added_in_db(player, 'bingoal')
        elif is_player_in_db(player):
            add_player_to_db(player, 'bingoal')
        else:
            if sb.DB_MANAGEMENT:
                print(player, 'bingoal')
                add_close_player_to_db(player, 'bingoal')
            else:
                return 'Match'
        return ref_player
    else:
        return 'Match'


def get_sub_markets_players_basketball_bingoal(id_match):
    """
    Get submarkets odds from basketball match
    """
    if not id_match:
        return {}
    url = 'https://eu-offering.kambicdn.org/offering/v2018/bingoalnl/betoffer/event/' + str(id_match) + '.json?lang=nl_NL&market=NL'
    content = requests.get(url).content
    parsed = json.loads(content)
    
    markets_class_list = parsed.get('betOffers', [])
    markets_to_keep = {
        'Points, rebounds & assists by the player - Including Overtime':'Points + passes + rebonds',
        'Assists by the player - Including Overtime':'Passes',
        'Rebounds by the player - Including Overtime':'Rebonds',
         #'Performance du Joueur (Points + Passes)':'Points + passes',
         #'Performance du Joueur (Points + Rebonds)':'Points + rebonds',
         #'Performance du Joueur (Passes + Rebonds)':'Passes + rebonds',
        "Points scored by the player - Including Overtime":"Points",
         #"Equipe à domicile - Nombre de 3 points marqués":"3 Points",
         #"Equipe à l'exterieur - Nombre de 3 points marqués":"3 Points",
        '3-point field goals made by the player - Including Overtime':"3 Points",
        "Nombre total de 3 pts marqués dans le match":"3 Points"
    }
    sub_markets = {v:defaultdict(list) for v in markets_to_keep.values()}
    for market_class_list in markets_class_list:
        market_name = market_class_list['criterion']['englishLabel']
        print(market_name)
        if market_name not in markets_to_keep:
            continue
        
        # team_name = market.get("event{}Name".format(market["marketType"]
        #                                             .split(" - ")[0]
        #                                             .replace(" ", "")))
        # id_team = is_in_db_site(team_name, "basketball", "unibet")
        # if id_team:
        #     ref_player = get_formatted_name_by_id(id_team[0])
        
        is_3_pts = "3 points marqués" in market_name
        if "3 pts marqués" in market_name:
            ref_player = "Match"
            is_3_pts = True
        
        selections = market_class_list['outcomes']
        for selection in selections:
            odd = round(selection['odds']/1000,10)
            limit = str(selection['line']/1000)
            plus = "OVER" in selection['type']
            
            if not is_3_pts:
                player = selection['participant']
                ref_player = player
                if is_player_added_in_db(player, "bingoal"):
                    ref_player = is_player_added_in_db(player, "bingoal")
                elif is_player_in_db(player):
                    add_player_to_db(player, "bingoal")
                else:
                    if sb.DB_MANAGEMENT:
                        print(player, "bingoal")
                        add_close_player_to_db(player,"bingoal")
                    else:
                        continue
            key_market = markets_to_keep[market_name]
            #if key_market == "Points":
            #    limit = str(float(market_name.split()[2])-0.5)
            key_player = ref_player + "_" + limit
            if key_player not in sub_markets[key_market]:
                sub_markets[key_market][key_player] = {"odds":{"bingoal":[]}}
            if plus:
                sub_markets[key_market][key_player]["odds"]["bingoal"].insert(0, odd)
            else:
                sub_markets[key_market][key_player]["odds"]["bingoal"].append(odd)
            if key_market == "Points":
                sub_markets[key_market][key_player]["odds"]["bingoal"].append(1.01)
    for sub_market in sub_markets:
        sub_markets[sub_market] = dict(sub_markets[sub_market])
    return sub_markets


def get_sub_markets_football_bingoal(id_match):
    """
    Get submarkets odds from football match.
    """
    if not id_match:
        return {}
    
    url = f'https://eu1.offering-api.kambicdn.com/offering/v2018/bingoalnl/betoffer/event/{id_match}.json?lang=en_GB&market=NL'
    response = requests.get(url)
    data = response.json()
    if data['events'][0]['state'] == 'STARTED':
        return {}
    
    bet_offers = data["betOffers"]

    team_A = data.get('events', [{}])[0].get('homeName', '')
    team_B = data.get('events', [{}])[0].get('awayName', '')
    
    # Check if both teams exist in the database
    id_team_A = is_in_db_site(team_A, "football", "bingoal")
    id_team_B = is_in_db_site(team_B, "football", "bingoal")
    
    if not id_team_A or not id_team_B:
        return {}  
    
    # Get formatted names
    team_A = get_formatted_name_by_id(id_team_A[0])
    team_B = get_formatted_name_by_id(id_team_B[0])
        
    markets_to_keep = {
        'Total Goals': 'Total Goals',
        'Total Goals - 1st Half': 'Total Goals 1st Half',
        'Total Goals - 2nd Half': 'Total Goals 2nd Half',
        f'Total Goals by {team_A}': f'Total Goals by',
        f'Total Goals by {team_B}': f'Total Goals by',
        'Both Teams To Score': 'Both Teams to Score',
        'Both Teams To Score - 1st Half': 'Both Teams to Score 1st Half',
        'Both Teams To Score - 2nd Half': 'Both Teams to Score 2nd Half',
        'Total Shots on Target (Settled using Opta data)': 'Shots on target',
        f'Total Shots on Target by {team_A} (Settled using Opta data)': f'Shots on target by',
        f'Total Shots on Target by {team_B} (Settled using Opta data)': f'Shots on target by',
        'Asian Handicap': 'Asian Handicap',
        'Asian Totaal': 'Asian Total',
        }

    hedgeable_markets = defaultdict(lambda: defaultdict(lambda: {"odds": {"bingoal": []}, "limit": ""}))
    for bet_offer in bet_offers:
        
        market_name = bet_offer["criterion"]["label"]
        if market_name not in markets_to_keep:
            continue
        
        print(market_name)
                
        outcomes = bet_offer.get("outcomes", [])
        if (len(outcomes) == 2 and all("odds" in outcome for outcome in outcomes)):
            market_name = bet_offer["criterion"]["label"]
            
            general_name = markets_to_keep.get(market_name, market_name)
            limit = str(bet_offer["outcomes"][0]['line']/1000) if "line" in bet_offer["outcomes"][0] else ""
            for outcome in bet_offer["outcomes"]:
                if "odds" in outcome:
                    odds_value = float(outcome["odds"]/1000)
                elif "oddsFractional" in outcome:
                    odds_value = float(outcome["oddsFractional"]["numerator"]/outcome["oddsFractional"]["denominator"] + 1)
                else:
                    continue
                
                if "by" in general_name:
                    team_name = team_A if team_A in market_name else team_B
                    odds_key = f"{team_name}_{limit}"
                else:
                    odds_key = f"Match_{limit}"
                
                if outcome["type"] == "OT_OVER":
                    hedgeable_markets[general_name][odds_key]["odds"]["bingoal"].insert(0, odds_value)
                else:
                    hedgeable_markets[general_name][odds_key]["odds"]["bingoal"].append(odds_value)
                hedgeable_markets[general_name][odds_key]["limit"] = limit

    for market in hedgeable_markets:
        hedgeable_markets[market] = dict(hedgeable_markets[market])

    return dict(hedgeable_markets)


def get_player_props_football_bingoal(id_match):
    """
    Get player props from a football match.

    Args:
        id_match (str): The ID of the football match.

    Returns:
        dict: A dictionary containing the player props.
    """
    if not id_match:
        return {}
    
    
    url = f'https://eu1.offering-api.kambicdn.com/offering/v2018/bingoalnl/betoffer/event/{id_match}.json?lang=nl_NL&market=NL'
    
    response = requests.get(url)
    parsed = response.json()
    
    markets_class_list = parsed.get('betOffers', [])
    markets_to_keep = {
        'Player\'s shots on target (Settled using Opta data)': 'Speler schoten op doel',
    }
    
    sub_markets = {v: defaultdict(lambda: {"odds": {"bingoal": [1.01, 1.01]}, "limit": ""}) for v in markets_to_keep.values()}
    for market_class_list in markets_class_list:
        market_name = market_class_list.get('criterion', {}).get('englishLabel', '')
        
        if market_name in markets_to_keep:
            
            outcomes = market_class_list.get('outcomes', [])
            for outcome in outcomes:
                if outcome.get('status') == 'OPEN':
                    participant = outcome.get('participant')
                    if is_player_in_db(participant):
                        participant = is_player_added_in_db(participant, "bingoal")
                    else:
                        add_new_player_to_db(participant)
                        add_player_to_db(participant, "bingoal")
                        participant = is_player_added_in_db(participant, "bingoal")
                    
                    odds = outcome.get('odds', 1000) / 1000
                    line = outcome.get('line', 0) / 1000
                    outcome_label = outcome.get('englishLabel')
                    if participant:
                        key = f'{participant}_{line}'
                        market_naam = markets_to_keep[market_name]
                        if key not in sub_markets[market_naam]:
                            sub_markets[market_naam][key] = {'odds': {'bingoal': [1.01, 1.01]}, 'limit': line}
                        if outcome_label == 'Over':
                            sub_markets[market_naam][key]['odds']['bingoal'][0] = odds
                        else:
                            sub_markets[market_naam][key]['odds']['bingoal'][1] = odds

    sub_markets = {k: dict(v) for k, v in sub_markets.items()}      
    return sub_markets


if __name__ == '__main__':
    #sb.DB_MANAGEMENT = True
    test = parse_bingoal_api('https://eu1.offering-api.kambicdn.com/offering/v2018/bingoalnl/listView/football/spain/la_liga.json?lang=nl_NL&market=NL')
    #test = get_sub_markets_football_bingoal('1021150919')