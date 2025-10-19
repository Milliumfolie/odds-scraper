# -*- coding: utf-8 -*-
"""
Created on Sat Dec  2 11:02:32 2023
@author: Jorden

"""  
import asyncio

import sys 
sys.path.append(r'C:\Users\Jorden\Desktop\staging')
import sportsbetting

# undetected-playwright here!
from undetected_playwright.async_api import async_playwright, Playwright
#from sportsbetting.bookmakers.ParseBet365 import ParseBet365 # Assuming you've saved the OddsParser class in odds_parser.py
from sportsbetting.bookmakers.ParseBet365 import ParseBet365

async def run(playwright: Playwright, url):
    args = ["--disable-blink-features=AutomationControlled"]
    
    try:
        browser = await playwright.chromium.launch(headless=False, args=args)
        page = await browser.new_page()
        response_queue = asyncio.Queue()  # Create an asynchronous queue
        
        async def handle_request(request):
            try:
                if 'https://www.bet365.nl/matchmarketscontentapi/markets?' in request.url:
                    # Fetch and print the response text for a specific request
                    response = await request.response()
                    if response:
                        text = await response.text()
                        await response_queue.put(text)  # Store the response text in the queue
                    else:
                        print(f"Request made but no response for URL: {request.url}")
            except Exception as e:
                print(f"Error while handling request: {e}")

        page.on('request', handle_request)
        
        await page.goto(url)
        
        # Wait for the selector, with a timeout to prevent indefinite waiting
        try:
            await page.wait_for_selector('.sgl-ParticipantOddsOnly80_Odds', timeout=50000)
        except asyncio.TimeoutError:
            print("Selector not found in time.")

        try:
            # Wait for response text to be added to the queue, with a timeout
            page_content = await asyncio.wait_for(response_queue.get(), timeout=20)
            #print(f"Received page content: {page_content}")
        except asyncio.TimeoutError:
            print("No response was received within the timeout period.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await browser.close()
    
    #print(page_content)
    parser = ParseBet365(page_content)
    full_time_results = parser.get_full_time_results(url)
    
    return full_time_results

async def run_playwright(url):
    async with async_playwright() as playwright:
        return await run(playwright, url)

async def get_bet365_odds(url):
    try:
        return await run_playwright(url)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {}

async def main(competition):
    odds = await get_bet365_odds(competition)
    print(odds)

if __name__ == "__main__":
    #url = sys.argv[1]  # Get URL from command line argument
    url = 'https://www.bet365.nl/#/AC/B1/C1/D1002/E92212336/G40/'
    asyncio.run(main(url))