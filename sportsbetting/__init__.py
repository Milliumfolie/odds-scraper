import collections
import json
import os
import queue
import re
import sys
import urllib.error
from pathlib import Path

ALL_ODDS_COMBINE = {}
ODDS = {}
TEAMS_NOT_FOUND = []
PROGRESS = 0
SUB_PROGRESS_LIMIT = 1
SITE_PROGRESS = collections.defaultdict(int)
QUEUE_TO_GUI = queue.Queue()
QUEUE_FROM_GUI = queue.Queue()
ODDS_INTERFACE = ""
EXPECTED_TIME = 0
INTERFACE = False
IS_PARSING = False
ABORT = False
SPORTS = ["basketball", "football", "handball", "hockey-sur-glace", "rugby", "tennis", "american-football", "darts"]
#PATH_DRIVER = "C:\\Users\\Jorden\\Desktop\\Sports-betting-master\\sportsbetting\\115"
SELENIUM_SITES = {"holland_casino"}
DB_BOOKMAKERS = ["betcity","jacks", "unibet", "zebet", "toto", "bet365", "vbet", "onecasino", "bingoal", "starcasino"]
BOOKMAKERS = sorted(DB_BOOKMAKERS)
BOOKMAKERS_BOOST = sorted(BOOKMAKERS + ["unibet"])
TEST = False
DB_MANAGEMENT = False
COOKIES_JOA_ACCEPTED = False
COOKIES_CIRCUS_ACCEPTED = False
COOKIES_BINGOAL_ACCEPTED = False
TRANSLATION = {}
BETA = True
SUREBETS = {}
MIDDLES = {}
MILES_RATES = {"5€": 385, "10€": 770, "20€": 1510, "50€": 3700, "100€": 7270, "200€": 14290, "500€": 35090, "1000€": 69000, "2000€": 135600, "5000€": 333330}
SEEN_SUREBET = {x: True for x in SPORTS}
FREEBETS_RATES = {bookmaker: 80 for bookmaker in BOOKMAKERS if bookmaker not in ["pinnacle", "betfair"]}

class UnavailableCompetitionException(Exception):
    """Exception raised when a competition is not found"""

class UnavailableSiteException(Exception):
    """Exception raised when a bookmaker site is unavailable"""

class AbortException(Exception):
    """Exception raised when the parsing is interrupted"""

def grp(pat, txt):
    """Return the first matching group of a regular expression"""
    res = re.search(pat, txt)
    return res.group(0) if res else "&"

def find_files(filename, search_path):
    """Return the absolute path of a file in a directory tree"""
    for root, _, files in os.walk(search_path):
        if filename in files:
            return os.path.abspath(os.path.join(root, filename))

PATH_DB = os.path.dirname(__file__) + "/resources/test.db"

PATH_FONT = os.path.dirname(__file__) + "/resources/DejaVuSansMono.ttf"

PATH_FREEBETS = os.path.dirname(__file__) + "/freebets.txt"