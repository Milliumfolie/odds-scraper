# -*- coding: utf-8 -*-
"""
Created on Sat Oct 26 11:40:06 2024

@author: Jorden
"""
import sys
import json
import uuid
import time
from datetime import datetime
import websocket

# Add the sportsbetting module path
sys.path.append(r'C:\Users\Jorden\Desktop\staging')
import sportsbetting

# Function to generate a random UUID for the rid
def random_uuid():
    return str(uuid.uuid4())

# Define WebSocket callbacks
def on_open(ws):
    print("Connection opened")
    # Send the initial command to request a session with a random rid
    init_message = {
        "command": "request_session",
        "params": {
            "language": "nld",
            "site_id": 18756479,
            "source": 42,
            "local_ip": "84.27.149.153",
            "release_date": "10/17/2024-12:16",
            "afec": "9Hf2IHv0cBymcpKgQob_JHMy3uVlRs9hJ2fL"
        },
        "rid": random_uuid()  # Generate a random rid
    }
    ws.send(json.dumps(init_message))
    print("Sent initial connection message:", json.dumps(init_message))

# Parse the odds data in the requested JSON format
def parse_odds_for_1x2(data):
    matches_data = {}

    # Check if 'game' data is present
    if 'data' in data and 'data' in data['data'] and 'game' in data['data']['data']:
        games = data['data']['data']['game']
        
        for game_id, game_info in games.items():
            team1_name = game_info.get("team1_name", "Unknown Team 1")
            team2_name = game_info.get("team2_name", "Unknown Team 2")
            match_name = f"{team1_name} - {team2_name}"
            
            start_ts = game_info.get("start_ts")
            match_date = datetime.fromtimestamp(start_ts) if start_ts else None
            
            competition_name = "None"
            
            match_data = {
                'date': match_date,
                'odds': {'vbet': []},
                'id': {'vbet': str(game_id)},
                'competition': competition_name
            }
            
            # Extract odds from WINNER markets
            if 'market' in game_info:
                for market_id, market_info in game_info['market'].items():
                    if market_info.get("display_key") == "WINNER":
                        odds = [None, None, None]  # Order: [home, draw, away]
                        for event_id, event_info in market_info['event'].items():
                            outcome = event_info["type_1"]
                            price = event_info["price"]
                            if outcome == "W1":
                                odds[0] = price
                            elif outcome == "X":
                                odds[1] = price
                            elif outcome == "W2":
                                odds[2] = price
                        
                        if all(odds):
                            match_data['odds']['vbet'] = odds
            
            if match_data['odds']['vbet']:
                matches_data[match_name] = match_data

    return matches_data

# Global variable to hold the odds data
odds_data = None

def on_message(ws, message):
    global odds_data
    print("Received:", message)
    response = json.loads(message)
    
    if response.get("code") == 0 and "data" in response and "sid" in response["data"]:
        session_id = response["data"]["sid"]
        print("Session established with sid:", session_id)
        
        get_message = {
            "command": "get",
            "params": {
                "source": "betting",
                "what": {
                    "game": ["id", "team1_name", "team2_name", "start_ts"],
                    "event": ["id", "price", "type_1", "name", "base", "order"],
                    "market": ["type", "name", "display_key", "base", "id", "express_id"]
                },
                "where": {
                    "competition": {"id": int(ws.competition_id)},
                    "game": {
                        "@or": [
                            {"visible_in_prematch": 1},
                            {"type": {"@in": [0, 2]}}
                        ]
                    },
                    "market": {
                        "@or": [
                            {
                                "display_key": "WINNER",
                                "display_sub_key": "MATCH"
                            }
                        ]
                    }
                },
                "subscribe": True
            },
            "rid": random_uuid()
        }
        ws.send(json.dumps(get_message))
        print("Sent specific 'get' command message:", json.dumps(get_message))
    
    elif 'data' in response and 'data' in response['data'] and 'game' in response['data']['data']:
        odds_data = parse_odds_for_1x2(response)
        ws.close()  # Close after parsing
        

def on_error(ws, error):
    print("Error:", error)

def on_close(ws, close_status_code, close_msg):
    print("Connection closed. Status:", close_status_code, "Message:", close_msg)

def connect_and_get_odds(url):
    global odds_data
    odds_data = None  # Reset odds data
    websocket_url = "wss://netherlands.prod.bc-swarm.com/"  # Ensure this is valid
    
    ws = websocket.WebSocketApp(
        websocket_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # Use a different attribute to store the competition ID to avoid conflicts with self.url
    ws.competition_id = url  # Set as a custom attribute
    
    ws.run_forever()
    return odds_data  # This will return the odds data once received

if __name__ == "__main__":
    odds = connect_and_get_odds("1957")
    print(json.dumps(odds, default=str, indent=4))







