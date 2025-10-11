# -*- coding: utf-8 -*-
"""
Created on Sun May 28 10:02:01 2023
@author: Admin
"""
import json
import time
import websocket
import requests
import datetime
import uuid

from threading import Thread, Event
import queue
import random

# Shared data structure
received_messages = queue.Queue()

# Use an event to signal when a message is received
message_received_event = Event()


def parse_circus_api(league_id):  
        
    def random_uuid():
        return str(uuid.uuid4())
    
    def get_match_id():
        try:
            # Make a GET request to the URL
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'}
            response = requests.get("https://stats.fn.sportradar.com/circus/nl/Europe:Berlin/gismo/stats_season_nextx/{}/20".format(league_id.split(',')[1]), headers=headers)
            
            # Convert the response to a Python dictionary
            data = response.json()
            
            # Initialize an empty dictionary to store the results
            results = []
            
            # Iterate over each match in the "matches" list
            for match in data['doc'][0]['data']['matches']:
                # Extract match id and teams
                match_id = str( match["_id"])+"01"
                results.append(int(match_id))
            return results
        except Exception as e:
            print(f"Exception occurred retrying: {e}")
            return[]
    
    # Get the event_id_list before initiating the WebSocket connection
    event_id_list = get_match_id()[0:-1]
    
    def on_open(ws):
        data = {
            "Id": random_uuid(),
            "TTL": 10,
            "MessageType": 1,
            "Message": json.dumps({
                "NodeType": 1,
                "Identity": random_uuid(),
                "EncryptionKey": "",
                "ClientInformations": {
                    "AppName": "Front;Registration-Origin: default",
                    "ClientType": "Responsive",
                    "Version": "1.0.0",
                    "UserAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0", 
                    "LanguageCode": "nl",
                    "RoomDomainName": "CIRCUSNL"
                }
            })
        }
        
        ws.send(json.dumps(data))
    
    
    def on_message(ws, message):
        #print(f"Received message: {message}")
        received_messages.put(message)
        message_received_event.set()  # Set the event when a message is received
              
        content_data = {
            "Entity": {
                "CacheId": random_uuid(),
                "EventIdList": event_id_list,  # Use your variable here
            },
            "InitialRequest": {
                "Language": "nl",
                "BettingActivity": 0,
                "PageNumber": 0,
                "OnlyShowcaseMarket": True,
                "IncludeSportList": True,
                "EventSkip": 0,
                "EventTake": 200,
                "EventType": 0,
                "SportId": 844,
                "RequestString": "LeagueIds={}&OnlyMarketGroup=Main".format(league_id.split(',')[0]),
            }
        }   
        inner_message = {
            "Direction": 1,
            "Id": random_uuid(),
            "Requests": [
                {
                    "Id": random_uuid(),
                    "Type": 201,
                    "Identifier": "ContinueLeaguesDataSourceFromCache",
                    "AuthRequired": False,
                    "Content": json.dumps(content_data)
                }
            ],
            "Groups": [],
        }
        data = {
            "Id": random_uuid(),
            "TTL": 10,
            "MessageType": 1000,
            "Message": json.dumps(inner_message)
        }
        ws.send(json.dumps(data))
    
    
    def on_error(ws, error):
        print(f"Error: {error}")
    
    
    def on_close(ws, close_status_code=None, close_msg=None):
        print("### closed ###")


    ws = websocket.WebSocketApp("wss://wss01.circus.nl:443",
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    MAX_RETRIES = 2
    attempts = 0
    content_received = False

    while not content_received and attempts < MAX_RETRIES:
        try:
            ws_thread = Thread(target=ws.run_forever)
            ws_thread.start()
        
            # Prefetch match IDs before starting WebSocket processing
            #event_id_list = get_match_id()[0:-1]

            message_count = 0
            MAX_TRIES = 2  # The maximum number of messages to process
            
            while not content_received and message_count < MAX_TRIES:
                message_received_event.wait()  # Wait for a message
            
                try:
                    raw_message = received_messages.get()  # Fetch the received message
                    
                    # Parse the raw_message into a Python dictionary
                    message_dict = json.loads(raw_message)
                    
                    # Check if the required keys and indices exist in the message
                    if 'Message' in message_dict:
                        inner_message = json.loads(message_dict['Message'])  # Parse the 'Message' key's value
                        if 'Requests' in inner_message and len(inner_message['Requests']) > 0 and 'Content' in inner_message['Requests'][0]:
                            message = json.loads(inner_message['Requests'][0]['Content'])  # Parse the nested JSON string
                            content_received = True  # Set the flag to break out of the loop
            
                except Exception as e:
                    print(f"Exception occurred while processing the message: {e}")
            
                # Increment the message count
                message_count += 1
            
                # Clear the event for the next iteration
                message_received_event.clear()

            ws.close()
            ws_thread.join()
        
        except Exception as e:
            print(f"Exception occurred retrying: {e}")
            attempts += 1
            
    try:
        #message = json.loads(message['Requests'][0]['Content'])
        competition = message['LeagueDataSource']['LeagueItems'][0]['LeagueName']
        odds_by_match = {}
        
        for match in message['LeagueDataSource']['LeagueItems'][0]['EventItems']:
            
            event_id = match['EventId']
            event_name = match['EventName'].replace(" : "," - ")
            date = datetime.datetime.fromisoformat(match['StartDate'].strip("Z"))
            match_odds = []
            
            for market_item in match['MarketItems']:  # Iterate through all market items
                if market_item['MarketName'] == 'Winnaar':  # Check if the market name is 'Winnaar'
                    for odd in market_item['OutcomeItems']:  # Iterate through the outcome items
                        match_odds.append(odd['Odd'])
                        
            odds_by_match[event_name] = {
                "date": date,
                "odds": {"circus": match_odds},
                "id": {"circus": event_id},
                "competition": competition
            }
        return odds_by_match
    
    except Exception as e:
        print(f"Exception occurred: {e}")
        return {}
    
    
    def parse_json_message():
        pass
       
    
if __name__ == "__main__":
   test = parse_circus_api('54375423,106529')