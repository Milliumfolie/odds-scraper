"""
Parser functions
"""
import locale
import sys

from sportsbetting.bookmakers import (betcity, unibet, jacks, zebet, toto, vbet, onecasino, bingoal, starcasino)
                                      
if sys.platform.startswith("win"):
    locale.setlocale(locale.LC_TIME, "fr")
elif sys.platform.startswith("linux"):
    locale.setlocale(locale.LC_TIME, "fr_FR.utf8")
else:  # sys.platform.startswith("darwin") # (Mac OS)
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")

def parse(site, url=""):
    """
    Return the odds for a given site
    """
    parse_functions = {
    "betcity" : betcity.parse_betcity,
    "unibet" : unibet.parse_unibet,
    "jacks" : jacks.parse_jacks,
    "zebet" : zebet.parse_zebet,
    "toto" : toto.parse_toto,
    #"livescorebet" : livescorebet.parse_livescorebet_api,
    #"circus" : circus_websocket.parse_circus_api,
    "bingoal": bingoal.parse_bingoal,
    #"bet365": Bet365.get_bet365_odds,
    "vbet": vbet.connect_and_get_odds,
    "onecasino": onecasino.parse_onecasino,
    "starcasino": starcasino.parse_starcasino_payload
    }
    return parse_functions[site](url)