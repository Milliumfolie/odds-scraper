"""
ZeBet odds scraper
"""

from collections import defaultdict
import datetime
import re
import urllib
import urllib.error
import urllib.request

from datetime import datetime
import requests

from bs4 import BeautifulSoup
import re

import sys
sys.path.append(r'C:\Users\Jorden\Desktop\Staging')

import sportsbetting as sb
from sportsbetting.database_functions import is_player_in_db, add_player_to_db, is_player_added_in_db, is_in_db_site, get_formatted_name_by_id, get_sport_by_url

import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
import time

def parse_zebet(url):
    """
    Return the available odds for zebet
    """
    page = requests.get(url).text
    
    pattern = re.compile(r'<div class="uk-accordion uk-accordion-block item" data-uk-accordion="\{collapse: false\}">(.*?)</article>', re.DOTALL)
    match = pattern.search(page)
    if not match:
        return {}  # return empty dict if pattern not found
    
    section = match.group(1)
    soup = BeautifulSoup(section, 'lxml')
    
    odds_dict = {}
    current_year = datetime.now().year
    sport = get_sport_by_url(url, 'zebet')
    
    if sport == 'football':
        
        match_elements = soup.select('div.item-content.catcomp.item-bloc-type-1')
    
        for item_content in match_elements:
            # Extract data using CSS selectors
            date_time_str = item_content.select_one('div.bet-time').get_text(strip=True)
            date_time_obj = datetime.strptime(date_time_str, '%d/%m %H:%M').replace(year=current_year)
            match_name = item_content.select_one('div.uk-visible-small.uk-text-bold.uk-margin-left.uk-text-truncate').get_text(strip=True).replace(' / ', ' - ')
            odds_elements = item_content.select('span.pmq-cote')
            actors_elements = item_content.select('span.pmq-cote-acteur.uk-text-truncate')
            
            # Extract match ID from the href
            match_link = item_content.select_one('div.bet-activebets a')
            match_id = ''
            if match_link and match_link.has_attr('href'):
                href = match_link['href']  # e.g. "/nl/event/bon53-az_feyenoord"
                match = re.search(r'/event/([a-z0-9]+)-', href)
                if match:
                    match_id = match.group(1)  # "bon53"
            
            odds_ordered = {actor.get_text(strip=True): float(odd.get_text(strip=True).replace(',', '.')) for odd, actor in zip(odds_elements, actors_elements) if actor.get_text(strip=True) in ['1', 'X', '2']}
            final_odds = [odds_ordered[key] for key in ['1', 'X', '2']]
            
            odds_dict[match_name] = {
                'competition': '',
                'date': date_time_obj,
                'id': {"zebet": match_id},
                'odds': {"zebet": final_odds}
            }
    else:
        
        match_elements = soup.select('div.item-content.catcomp.item-bloc-type-2')
    
        for item_content in match_elements:
            
            # Extract data using CSS selectors
            date_time_str = item_content.select_one('div.bet-time').get_text(strip=True)
            date_time_obj = datetime.strptime(date_time_str, '%d/%m %H:%M').replace(year=current_year)
            match_name = item_content.select_one('div.uk-visible-small.uk-text-bold.uk-margin-left.uk-text-truncate').get_text(strip=True).replace(' / ', ' - ')
            odds_elements = item_content.select('span.pmq-cote')
            actors_elements = item_content.select('span.pmq-cote-acteur.uk-text-truncate')
            
            odds_ordered = {actor.get_text(strip=True): float(odd.get_text(strip=True).replace(',', '.')) for odd, actor in zip(odds_elements, actors_elements) if actor.get_text(strip=True) in ['1', 'X', '2']}
            final_odds = [odds_ordered[key] for key in ['1', '2']]
    
            odds_dict[match_name] = {
                'competition': '',
                'date': date_time_obj,
                'id': {"zebet": ''},
                'odds': {"zebet": final_odds}
            }
        
    return odds_dict

def parse_sport_zebet(url):
    """
    Retourne les cotes disponibles sur zebet pour un sport donné
    """
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    match_odds_hash = {}
    today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    year = str(today.year) + "/"
    date_time = None
    for line in soup.find_all():
        if "Zebet rencontre actuellement des difficultés techniques." in line.text:
            raise sb.UnavailableSiteException
        if "class" in line.attrs and "bet-event" in line["class"]:
            match = format_zebet_names(line.text.strip())
        if "class" in line.attrs and "bet-time" in line["class"]:
            try:
                date_time = datetime.datetime.strptime(year + " ".join(line.text.strip().split()),
                                                       "%Y/%d/%m %H:%M")
                if date_time < today:
                    date_time = date_time.replace(year=date_time.year + 1)
            except ValueError:
                date_time = "undefined"
        if "class" in line.attrs and "pari-1" in line["class"]:
            odds = list(map(lambda x: float(x.replace(",", ".")),
                            list(line.stripped_strings)[1::2]))
            if match not in match_odds_hash:
                match_odds_hash[match] = {}
            match_odds_hash[match]['odds'] = {"zebet": odds}
            match_odds_hash[match]['date'] = date_time
        if "href" in line.attrs and "/nl/event/" in line["href"]:
            match_id = line["href"].split("-")[0].split("/")[-1]
            if match not in match_odds_hash:
                match_odds_hash[match] = {}
            match_odds_hash[match]['id'] = {"zebet": match_id}
    print(match_odds_hash)
    return match_odds_hash


def format_zebet_names(match):
    """
    Returns match from a string available on ZeBet html
    """
    strings = match.split(" / ")
    if len(strings) == 2:
        return " - ".join(strings)
    if len(strings) == 4:
        return " - ".join(map(" / ".join, [strings[0:2], strings[2:4]]))
    if len(strings) == 3:
        reg_exp = r'[A-z]+\.[A-z\-]+\-[A-z]+\.[A-z\-]+'
        if re.findall(reg_exp, strings[0]):
            return " - ".join([strings[0], " / ".join(strings[1:3])])
        if re.findall(reg_exp, strings[2]):
            return " - ".join([" / ".join(strings[0:2]), strings[2]])
        if len(strings[0]) > max(len(strings[1]), len(strings[2])):
            return " - ".join([strings[0], " / ".join(strings[1:3])])
        if len(strings[2]) > max(len(strings[1]), len(strings[0])):
            return " - ".join([" / ".join(strings[0:2]), strings[2]])
    return ""


def get_sub_markets_players_basketball_zebet(id_match):
    """
    Get submarkets odds from basketball match
    """
    if not id_match:
        return {}
    url = 'https://www.zebet.nl/nl/event/' + id_match + '-'
    markets_to_keep = {
         #Nombre de passes décisives pour le joueur (prolongations incluses) ?':'Passes',
         #'Nombre de rebonds pour le joueur (prolongations incluses) ?':'Rebonds',
         #'Nombre de points marqués par le joueur (prolongations incluses) ?':'Points',
        'Meer of minder dan punten? (incl. verlenging)' : 'Points',
        'Nombre total de points + passes (prolongations incluses)' : 'Points + passes',
        'Nombre total de points + rebonds (prolongations incluses)' : 'Points + rebonds',
         #'Performance du joueur (points + rebonds + passes, prolongations incluses)' : 'Points + passes + rebonds'
    }
    soup = BeautifulSoup((urllib.request.urlopen(url)), features='lxml')
    sub_markets = {v:defaultdict(list) for v in markets_to_keep.values()}
    market_name = None
    for line in soup.find_all():
        if 'Zebet rencontre actuellement des difficultés techniques.' in line.text:
            raise sb.UnavailableSiteException
        if 'class' in line.attrs and 'bet-question' in line['class']:
            market_name = line.text.strip()
            
        if market_name in markets_to_keep:
            print(market_name)
            if 'class' in line.attrs:
                if 'pmq-cote' in line['class']:
                    odd = float(line.text.strip().replace(',', '.'))
            if 'class' in line.attrs and 'pmq-cote-acteur' in line['class']:
                plus = "+" in line.text or "Meer dan" in line.text
                limit = re.split(r'((Meer|Minder)\sdan\s|\s(\+|\-))', line.text.strip())[(-1)].strip().replace(",", ".")
                try:
                    _ = float(limit)
                except ValueError:
                    continue
                #player = re.split(r'((Meer|minder)\sdan\s|\s(\+|\-))', line.text.strip())[0].split("(")[0].strip()
                ref_player = "Match"
                #if is_player_added_in_db(player, "zebet"):
                #    ref_player = is_player_added_in_db(player, "zebet")
                #elif is_player_in_db(player):
                #    add_player_to_db(player, "zebet")
                #else:
                #    if sb.DB_MANAGEMENT:
                #        print(player, "zebet")
                #    continue
                
                last = -1
                key_player = ref_player + "_" + limit
                key_market = markets_to_keep[market_name]
                if key_player not in sub_markets[key_market]:
                    sub_markets[key_market][key_player] = {"odds":{"zebet":[]}}
                if plus:
                    sub_markets[key_market][key_player]["odds"]["zebet"].insert(0, odd)
                    last = 0
                    #if key_market == "Points":
                    #    sub_markets[key_market][key_player]["odds"]["zebet"].append(1.01)
                else:
                    sub_markets[key_market][key_player]["odds"]["zebet"].append(odd)
                if len(sub_markets[key_market][key_player]["odds"]["zebet"]) > 2:
                    del sub_markets[key_market][key_player]["odds"]["zebet"][last]
    for sub_market in sub_markets:
        sub_markets[sub_market] = dict(sub_markets[sub_market])
    return sub_markets


def get_sub_markets_football_zebet(id_match):
    """
    Get submarkets odds from football match
    """
    if not id_match:
        return {}
    url = 'https://www.zebet.nl/nl/event/' + id_match + '-'
    soup = BeautifulSoup((urllib.request.urlopen(url)), features='lxml')
    page_title = soup.title.text
    
    team_A = page_title.split('/')[0].strip()
    team_B = page_title.split('/')[1].split('-')[0].strip()
        
    # Check if both teams exist in the database
    id_team_A = is_in_db_site(team_A, "football", "zebet")
    id_team_B = is_in_db_site(team_B, "football", "zebet")
    
    if not id_team_A or not id_team_B:
        return {}  
    
    # Get formatted names
    team_A = get_formatted_name_by_id(id_team_A[0])
    team_B = get_formatted_name_by_id(id_team_B[0])
        
    
    
    markets_to_keep = {
        'Meer of minder dan doelpunten?':'Total Goals',
        'Meer/Minder Doelpunten - 1e helft?':'Total Goals 1st half',
        'Meer of minder doelpunten in 2e helft?':'Total Goals 2nd half',
         #'Both Teams To Score - 1st Half':'Both Teams To Score - 1st Half',
         #'Both Teams To Score - 2nd Half':'Both Teams To Score - 2nd Half',
         #'Both Teams to Score in both halves':'Both Teams to Score in both halves',
         #'Goal in both halves':'Goal in both halves',
         #'Draw No Bet':'Draw No Bet',
         #'Draw and both teams to score':'Draw and both to score',
         #'Total Shots on Target (Settled using Opta data)':'Shots on target',
         #'Total Shots on Target by {}'.format(team_A):'Shots on target by',
         #'Total Shots on Target by {}'.format(team_B):'Shots on target by',
         'Meer of minder dan doelpunt(en) voor {}'.format(team_A):'Total Goals by',
         'Meer of minder dan doelpunt(en) voor {}'.format(team_B):'Total Goals by',
         #'To score':'To score'
    }
    
    sub_markets = {v:defaultdict(list) for v in markets_to_keep.values()}
    market_name = None
    
    for line in soup.find_all():
        if 'Zebet rencontre actuellement des difficultés techniques.' in line.text:
            raise sb.UnavailableSiteException
        if 'class' in line.attrs and 'bet-question' in line['class']:
            market_name = line.text.strip()

        if market_name in markets_to_keep:
            if 'class' in line.attrs:
                if 'pmq-cote' in line['class']:
                    odd = float(line.text.strip().replace(',', '.'))
                    
            if 'class' in line.attrs and 'pmq-cote-acteur' in line['class']:
                plus = "+" in line.text or "Meer dan" in line.text
                limit = re.split(r'((Meer|Minder)\sdan\s|\s(\+|\-))', line.text.strip())[(-1)].strip().replace(",", ".")
                try:
                    _ = float(limit)
                except ValueError:
                    continue
                
                if 'voor' in market_name:
                    if team_A in market_name:
                        team_name = team_A
                    else:
                        team_name = team_B
                    id_team = is_in_db_site(team_name, "football", "zebet")
                    if id_team:
                        ref_player = get_formatted_name_by_id(id_team[0])
                else: 
                    ref_player = "Match"

                last = -1
                key_player = ref_player + "_" + limit
                key_market = markets_to_keep[market_name]
                
                if key_player not in sub_markets[key_market]:
                    sub_markets[key_market][key_player] = {"odds":{"zebet":[]}}
                if plus:
                    sub_markets[key_market][key_player]["odds"]["zebet"].insert(0, odd)
                    last = 0
                    if key_market == "Points":
                        sub_markets[key_market][key_player]["odds"]["zebet"].append(1.01)
                else:
                    sub_markets[key_market][key_player]["odds"]["zebet"].append(odd)
                if len(sub_markets[key_market][key_player]["odds"]["zebet"]) > 2:
                    del sub_markets[key_market][key_player]["odds"]["zebet"][last]
    for sub_market in sub_markets:
        sub_markets[sub_market] = dict(sub_markets[sub_market])
    return sub_markets


if __name__ == "__main__":
    #sb.DB_MANAGEMENT = True
    #test = get_sub_markets_football_zebet('4pn53')
    test = parse_zebet('https://www.zebet.nl/nl/competition/39613-wk_kwalificaties')