# -*- coding: utf-8 -*-
"""
Created on Sun Jan 21 15:02:26 2024

@author: Jorden
"""
import json
import requests
import sqlite3

def get_main_countries(sport):
    """
    Retrieves the main countries associated with a given sport.
    
    Args:
    sport (str): The sport for which to retrieve the countries.
    
    Returns:
    dict: A dictionary mapping country names to their corresponding IDs.
    """
    url = f"https://stats.fn.sportradar.com/circus/nl/Europe:Berlin/gismo/config_tree_mini/41/{sport}/1"
    response = requests.get(url)
    data = response.json()
    
    country_dict = {}
    for country in data['doc'][0]['data'][0]['realcategories']:
        country_dict[country['name']]= country['_id']

    return country_dict

def get_main_competition_from_id(sport, countries_id):
    competition_dict = {}
    for country_name, country_id in countries_id.items():
        url = f"https://stats.fn.sportradar.com/circus/nl/Europe:Berlin/gismo/config_tree_mini/41/{sport}/1/{country_id}"
        response = requests.get(url)
        data = response.json()
        for competition_key, competition in data['doc'][0]['data'][0]['realcategories'][0]['uniquetournaments'].items():

            competition_dict[competition['currentseason']] = {"competition": country_name + ' ' + competition['name'],
                                                              "country": country_name}
                                                              
    return competition_dict
    
def get_teams_from_competition_id(competition_id):
    teams_dict = {}
    for competition_id, none in competition_id.items():
        url = f"https://stats.fn.sportradar.com/circus/nl/Europe:Berlin/gismo/stats_formtable/{competition_id}"
        response = requests.get(url)
        data = response.json()
       
        # Check if 'teams' exists and is a non-empty list
        if 'teams' in data['doc'][0]['data'] and data['doc'][0]['data']['teams']:
            for team in data['doc'][0]['data']['teams']:
                team_name = team['team']['name']
                team_id = team['team']['_id']
                teams_dict[team_id] = {'name': team_name,
                                        'season_id':competition_id}

    return teams_dict

def insert_competitions(competitions):
    conn = sqlite3.connect('sports.db')
    cursor = conn.cursor()

    for season_id, comp_info in competitions.items():
        cursor.execute("INSERT INTO competitions VALUES (?, ?, ?)",
                       (season_id, comp_info['competition'], comp_info['country']))

    conn.commit()
    conn.close()


def insert_teams(teams):
    conn = sqlite3.connect('sports.db')
    cursor = conn.cursor()

    for team_id, team_info in teams.items():
        cursor.execute("INSERT INTO teams VALUES (?, ?, ?)",
                       (team_id, team_info['name'], team_info['season_id']))

    conn.commit()
    conn.close()


if __name__ == '__main__':
    
    
    # Establish a connection to the database (this will create the file if it does not exist)
    conn = sqlite3.connect('sports.db')
    
    # Create a cursor object using the cursor() method
    cursor = conn.cursor()
    
    # Create table - COMPETITIONS
    cursor.execute('''CREATE TABLE IF NOT EXISTS competitions
                      (season_id INTEGER PRIMARY KEY, 
                       competition_name TEXT, 
                       country TEXT)''')
    
    # Create table - TEAMS
    cursor.execute('''CREATE TABLE IF NOT EXISTS teams
                      (team_id INTEGER PRIMARY KEY,
                       name TEXT,
                       season_id INTEGER,
                       FOREIGN KEY(season_id) REFERENCES competitions(season_id))''')
    
    # Commit the transaction
    conn.commit()
    
    # Close the connection
    conn.close()
    
    
    
    
    countries_id = get_main_countries(0)
    keys_to_include = {'Nederland'}
    
    countries_id = {k: countries_id[k] for k in keys_to_include if k in countries_id}
    competitions = get_main_competition_from_id(0, countries_id)
    teams = get_teams_from_competition_id(competitions)
    
    insert_competitions(competitions)
    insert_teams(teams)