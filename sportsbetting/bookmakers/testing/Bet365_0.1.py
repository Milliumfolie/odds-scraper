# -*- coding: utf-8 -*-
"""
Created on Sat Dec 2 11:02:32 2023
@author: Jorden
"""

import asyncio
import sys

# Add staging path
sys.path.append(r'C:\Users\Jorden\Desktop\staging')

import sportsbetting
# undetected-playwright here!
from undetected_playwright.async_api import async_playwright, Playwright
from sportsbetting.bookmakers.ParseBet365 import ParseBet365


async def run(playwright: Playwright, url: str):
    args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
        "--no-sandbox",
        "--disable-dev-shm-usage",
    ]

    try:
        browser = await playwright.chromium.launch(
            channel="chrome",
            headless=False,
            args=args
        )
        page = await browser.new_page()
        response_queue = asyncio.Queue()  # Create an asynchronous queue

        async def handle_request(request):
            try:
                if 'https://www.bet365.nl/matchmarketscontentapi/markets?' in request.url:
                    # Fetch and store the response text
                    response = await request.response()
                    if response:
                        text = await response.text()
                        await response_queue.put(text)
                    else:
                        print(f"Request made but no response for URL: {request.url}")
            except Exception as e:
                print(f"Error while handling request: {e}")

        page.on('request', handle_request)
        await page.goto(url)

        # Wait for the selector, with timeout to prevent indefinite waiting
        try:
            await page.wait_for_selector('.sgl-ParticipantOddsOnly80_Odds', timeout=5000000)
        except asyncio.TimeoutError:
            print("Selector not found in time.")

        try:
            # Wait for response text from queue
            page_content = await asyncio.wait_for(response_queue.get(), timeout=20)
        except asyncio.TimeoutError:
            print("No response was received within the timeout period.")
            page_content = None
        except Exception as e:
            print(f"An error occurred: {e}")
            page_content = None
        finally:
            await browser.close()

        if page_content:
            parser = ParseBet365(page_content)
            full_time_results = parser.get_full_time_results(url)
            return full_time_results

        return {}

    except Exception as e:
        print(f"Unexpected error during run: {e}")
        return {}


async def run_playwright(url: str):
    async with async_playwright() as playwright:
        return await run(playwright, url)


async def get_bet365_odds(url: str):
    try:
        return await run_playwright(url)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {}


async def main(competition: str):
    odds = await get_bet365_odds(competition)
    print(odds)


if __name__ == "__main__":
    # url = sys.argv[1]  # Uncomment if you want to take from CLI
    url = 'https://www.bet365.nl/#/AC/B1/C1/D1002/E91422157/G40/'
    asyncio.run(main(url))
