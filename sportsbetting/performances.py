import sys 
sys.path.append(r'C:\Users\Jorden\Desktop\Staging')

import sportsbetting as sb
from sportsbetting.auxiliary_functions import merge_dict_odds, valid_odds
from sportsbetting.bookmakers import betcity, toto, unibet, zebet, jacks
from sportsbetting.user_functions import parse_competitions
from sportsbetting.basic_functions import gain

def keep_maximum_odds(odds1, odds2, books1, books2):
    out = [[], []]
    for odd1, odd2, book1, book2 in zip(odds1, odds2, books1, books2):
        if not (odd1 and odd2):
            continue
        if odd2 > odd1:
            out[0].append(odd2)
            out[1].append(book2)
        else:
            out[0].append(odd1)
            out[1].append(book1)
    return out


def get_middle_odds(odds1, odds2):
    bookmakers = odds1.keys() | odds2.keys()
    valid = False
    odds = {bookmaker:[1.01, 1.01] for bookmaker in bookmakers}
    for bookmaker1 in odds1:
        odds[bookmaker1][0] = odds1[bookmaker1][0]
    for bookmaker2 in odds2:
        if odds2[bookmaker2][1] != 1.01:
            valid = True
        odds[bookmaker2][1] = odds2[bookmaker2][1]
    if not valid:
        return None
    return odds


def merge_dicts_football(match, id_zebet, id_unibet, id_betcity, id_toto, id_jacks):
    odds = [
        toto.get_sub_markets_football_toto(id_toto),
        unibet.get_sub_markets_football_unibet(id_unibet),
        betcity.get_sub_markets_football_betcity(id_betcity),
        zebet.get_sub_markets_football_zebet(id_zebet),
        jacks.get_sub_markets_football_jacks(id_jacks),
    ]

    sub_markets = ['Both Teams to Score', 'Total Goals', 'Total Goals 1st half', 'Total Goals 2nd half', 'Shots on target', 'Shots on target by', 'Shots on target by',
                   'Total Goals by', 'Total Goals by', 'Total Goals by 1st half', 'Total Goals by 1st half', 'Total Shots', 'Total Shots by', 'Total Shots by',
                   'Both Teams to Score', 'Both Teams to Score 1st Half', 'Asian Handicap', 'Asian Handicap 1st Half', 'Asian Total', 'Asian Total 1st Half', 'Draw No Bet',
                   'Draw No Bet 1st Half']

    best = {}
    best_books = {}
    middles = {}
    surebets = {}
    
    for sub_market in sub_markets:
        
        odds_sub_market = valid_odds(merge_dict_odds([x.get(sub_market, {}) for x in odds], False), "football")
        players_limits = odds_sub_market.keys()
        previous_player = ""
        previous_limit = 0
        players = []

        for player_limit in players_limits:
            split_values = player_limit.split("_")

            if len(split_values) == 2:
                player, limit_str = split_values
                try:
                    limit = float(limit_str)
                    players.append([player, limit])
                except ValueError:
                    player = player_limit
                    players.append([player, None])
            else:
                player = player_limit
                players.append([player, None])
                
        for player, limit in sorted(list(players)):
            same_player = previous_player == player
            player_dict = player + ("_" +str(limit) if limit else "")
            previous_player_dict = previous_player + ("_"+str(previous_limit) if previous_limit else "")

            if player_dict in odds_sub_market:
                surebets[player + " / " + (str(limit) if limit else "no limit") + " " + sub_market] = {"match": match, "odds": odds_sub_market[player_dict]["odds"]}

                if same_player and previous_player_dict in odds_sub_market:
                    odds_middle = get_middle_odds(odds_sub_market[previous_player_dict]["odds"], odds_sub_market[player_dict]["odds"])
                    if odds_middle:
                        middles[player + " / " + (str(previous_limit) if previous_limit else "no limit") + " - " + (str(limit) if limit else "no limit") + " " + sub_market] = {
                            "odds": odds_middle, "match": match}
            previous_player, previous_limit = player, limit
  
    return surebets, middles


def merge_dicts_basketball(match, id_pinnacle, id_unibet, id_betcity, id_zebet, id_jacks):
    odds = [
        #betclic.get_sub_markets_players_basketball_betclic(id_betclic),
        #parionssport.get_sub_markets_players_basketball_parionssport(id_parionssport),
        pinnacle.get_sub_markets_players_basketball_pinnacle(id_pinnacle),
        jacks.get_sub_markets_players_basketball_jacks(id_jacks),
        unibet.get_sub_markets_players_basketball_unibet(id_unibet),
        betcity.get_sub_markets_players_basketball_betcity(id_betcity),
        zebet.get_sub_markets_players_basketball_zebet(id_zebet)
    ]
    
    sub_markets = ['Points + passes + rebonds', 'Passes', 'Rebonds', 'Points + passes', 'Points + rebonds', 'Passes + rebonds', 'Points', '3 Points']
    
    best = {}
    best_books = {}
    middles = {}
    surebets = {}
    for sub_market in sub_markets:
        odds_sub_market = valid_odds(merge_dict_odds([x.get(sub_market, {}) for x in odds], False), "basketball")
        players_limits = odds_sub_market.keys()
        previous_player = ""
        previous_limit = 0
        players = []
        for player_limit in players_limits:
            player, limit = player_limit.split("_")
            players.append([player, float(limit)])
        for player, limit in sorted(list(players)):
            same_player = previous_player == player
            player_dict = player + "_" + str(limit)
            previous_player_dict = previous_player + "_" + str(previous_limit)
            surebets[player + " / " + str(limit) + " " + sub_market] = {"match":match, "odds": odds_sub_market[player_dict]["odds"]}
            if same_player:
                odds_middle = get_middle_odds(odds_sub_market[previous_player_dict]["odds"], odds_sub_market[player_dict]["odds"])
                if odds_middle:
                    middles[player + " / " + str(previous_limit) + " - " + str(limit) + " " + sub_market] = {"odds": odds_middle, "match":match}
            previous_player, previous_limit = player, limit
            
    print(surebets)
    return surebets, middles


def merge_dicts_players_props_football(match, id_zebet, id_unibet, id_betcity, id_toto, id_livescorebet, id_jacks, id_holland_casino):
    odds = [
         #livescorebet.get_sub_markets_players_football_livescorebet(id_livescorebet),
         #toto.get_sub_markets_players_football_toto(id_toto),
         unibet.get_player_props_football_unibet(id_unibet),
         betcity.get_player_props_football_betcity(id_betcity),
         #zebet.get_sub_markets_players_football_zebet(id_zebet),
         #jacks.get_sub_markets_players_football_jacks(id_jacks),
         #holland_casino.get_sub_markets_players_football_holland_casino(id_holland_casino)
    ]
    
    sub_markets = ['Speler schoten op doel']
    
    #main_markets = ['Moneyline','Total gaols']
    #team_markets = ['']
    #period_markets = ['']
    #other_markets = ['']
    #player_markets = ['']
    
    best = {}
    best_books = {}
    middles = {}
    surebets = {}
    
    #with open('file.json', 'a') as outfile:
    #    outfile.write(json.dumps(odds[0]))
    #    outfile.write(",")
    #    outfile.close()
    
    for sub_market in sub_markets:
        odds_sub_market = valid_odds(merge_dict_odds([x.get(sub_market, {}) for x in odds], False), "football")
        
        players_limits = odds_sub_market.keys()
        previous_player = ""
        previous_limit = 0
        players = []
        
        for player_limit in players_limits:
            #try:
            player, limit = player_limit.split("_")
            players.append([player, float(limit)])
            #except:
            #    player, limit = player_limit.split("_")
            #    players.append([player, limit])
                
        for player, limit in sorted(list(players)):
            same_player = previous_player == player
            player_dict = player + "_" + str(limit)
            previous_player_dict = previous_player + "_" + str(previous_limit)
            surebets[player + " / " + str(limit) + " " + sub_market] = {"match":match, "odds": odds_sub_market[player_dict]["odds"]}
            
            if same_player:
                odds_middle = get_middle_odds(odds_sub_market[previous_player_dict]["odds"], odds_sub_market[player_dict]["odds"])
                if odds_middle:
                    middles[player + " / " + str(previous_limit) + " - " + str(limit) + " " + sub_market] = {"odds": odds_middle, "match":match}
            previous_player, previous_limit = player, limit
            
    #with open('new.json', 'a') as outfile:
    #    outfile.write(json.dumps(middles))
    #    outfile.write(",")
    #    outfile.close()        
    return surebets, middles


def get_surebets_players_basketball(bookmakers, competition):
    parse_competitions([competition], "basketball", *bookmakers)
    surebets = {}
    middles = {}
    sb.PROGRESS = 0
    n = len(sb.ODDS["basketball"])
    for match in sb.ODDS["basketball"]:
        if "id" not in sb.ODDS["basketball"][match]:
            continue
        
        #id_betclic = sb.ODDS["basketball"][match]["id"].get("betclic")
        #id_parionssport = sb.ODDS["basketball"][match]["id"].get("parionssport")
        id_pinnacle = sb.ODDS["basketball"][match]["id"].get("pinnacle")
        id_jacks = sb.ODDS["basketball"][match]["id"].get("jacks")
        id_unibet = sb.ODDS["basketball"][match]["id"].get("unibet")
        id_betcity = sb.ODDS["basketball"][match]["id"].get("betcity")
        id_zebet = sb.ODDS["basketball"][match]["id"].get("zebet")
        
        surebets_match, middles_match = merge_dicts_basketball(match, id_pinnacle, id_unibet, id_betcity, id_zebet, id_jacks)
        surebets_match_db_key = {}
        middles_match_db_key = {}
        
        for key, value in surebets_match.items():
            surebets_match_db_key[match + key] = value
            
        for key, value in middles_match.items():
            middles_match_db_key[match + key] = value    
        
        surebets.update(surebets_match_db_key)
        middles.update(middles_match_db_key)
        sb.PROGRESS += 100/n
    return surebets, middles

def get_surebets_players_football(bookmakers, competition):
    parse_competitions([competition], "football", *bookmakers)
    surebets = {}
    middles = {}
    sb.PROGRESS = 0
    n = len(sb.ODDS["football"])
    
    print(sb.ODDS["football"])
    print(n)
    
    for match in sb.ODDS["football"]:
        if "id" not in sb.ODDS["football"][match]:
            continue        
        id_jacks = sb.ODDS["football"][match]["id"].get("jacks")
        id_zebet = sb.ODDS["football"][match]["id"].get("zebet")
        id_unibet = sb.ODDS["football"][match]["id"].get("unibet")
        id_betcity = sb.ODDS["football"][match]["id"].get("betcity")
        id_toto = sb.ODDS["football"][match]["id"].get("toto")
        
        surebets_match, middles_match = merge_dicts_football(match, id_zebet, id_unibet, id_betcity, id_toto, id_jacks)
        surebets_match_db_key = {}
        middles_match_db_key = {}
        
        for key, value in surebets_match.items():
            surebets_match_db_key[match + key] = value
            
        for key, value in middles_match.items():
            middles_match_db_key[match + key] = value    
        
        surebets.update(surebets_match_db_key)
        middles.update(middles_match_db_key)
        sb.PROGRESS += 100/n
            
    return surebets, middles

if __name__ == "__main__":
    test_2 = merge_dicts_football('Test', 0, 0, '1021049370', '6960105', 0)