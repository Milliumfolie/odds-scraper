# -*- coding: utf-8 -*-
"""
bet365_scraper.py
Importable Bet365 odds scraper (async Playwright under the hood).

Public API:
    get_bet365_odds(url, username=None, password=None,
                    storage_path="bet365_state.json", force_login=False,
                    headless=False, timeout_sec=60) -> dict

- If storage_path exists, it reuses the session (no login).
- If not, it logs in once (needs username/password) and saves the session.
- Works from terminal and from Spyder/Jupyter (Windows Proactor loop in a worker).
"""

import os
import sys
import asyncio
import threading
from pathlib import Path
from typing import Optional, Dict

# Project path so we can import your parser
sys.path.append(r"C:\Users\Jorden\Desktop\staging")
from sportsbetting.bookmakers.ParseBet365 import ParseBet365  # type: ignore

# Use PROACTOR loop on Windows (supports asyncio subprocess)
if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from undetected_playwright.async_api import async_playwright, Playwright


# ---------- Small helpers ----------
async def _click_if_exists(page_or_frame, selector, timeout=2000) -> bool:
    try:
        await page_or_frame.locator(selector).first.click(timeout=timeout)
        return True
    except Exception:
        return False

async def _accept_cookies_if_present(page):
    for sel in [
        'button:has-text("Accept All")',
        'button:has-text("Accept")',
        'button:has-text("Akkoord")',
        'button:has-text("Alles accepteren")',
        '[data-testid="uc-accept-all-button"]',
        'button[mode="primary"]:has-text("Accept")',
    ]:
        if await _click_if_exists(page, sel, timeout=1500):
            break

async def _ensure_login_form(page):
    if await page.locator(".lms-StandardLogin_Container").first.is_visible():
        return
    # Try to open login UI from header/menu
    for sel in [
        'button:has-text("Inloggen")',
        'button:has-text("Log In")',
        '[data-bet365-test="header-login"]',
        'text=Inloggen',
        'text=Log In',
        'button[aria-label*="Login"]',
    ]:
        if await _click_if_exists(page, sel, timeout=2000):
            break
    try:
        await page.locator(".lms-StandardLogin_Container").first.wait_for(timeout=5000)
    except Exception:
        pass

# ---------- Login based on your provided HTML ----------
async def _login(page, username: str, password: str) -> bool:
    """
    Logs in using Bet365's standard login form (classes from shared HTML).
    Returns True if a logged-in indicator appears.
    """
    if not username or not password:
        raise RuntimeError("Missing credentials for login().")

    await page.goto("https://www.bet365.nl/#/HO/", wait_until="domcontentloaded")
    await _accept_cookies_if_present(page)
    await _ensure_login_form(page)

    # Fill username/password using the exact classes
    try:
        await page.fill("input.lms-StandardLogin_Username", username, timeout=5000)
        await page.fill("input.lms-StandardLogin_Password", password, timeout=5000)
    except Exception:
        # Click container to focus if needed, then retry
        try:
            await page.click(".lms-StandardLogin_InputsContainer")
        except Exception:
            pass
        await page.fill("input.lms-StandardLogin_Username", username, timeout=5000)
        await page.fill("input.lms-StandardLogin_Password", password, timeout=5000)

    # The login button is a <div>
    await page.click("div.lms-LoginButton", timeout=5000)

    # Wait for a "logged-in" indicator
    post_login_candidates = [
        ".hm-MainHeaderRHSLoggedIn_UserName",
        '[data-bet365-test="header-account"]',
        'button[aria-label*="Account"]',
        'text=Saldo',
    ]
    for _ in range(40):  # ~20s
        for sel in post_login_candidates:
            try:
                if await page.locator(sel).first.is_visible():
                    return True
            except Exception:
                pass
        await page.wait_for_timeout(500)

    return False


# ---------- Core async flow ----------
async def _ensure_context_and_login(p: Playwright,
                                    storage_path: Path,
                                    username: Optional[str],
                                    password: Optional[str],
                                    headless: bool):
    args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
        "--no-sandbox",
        "--disable-dev-shm-usage",
    ]
    browser = await p.chromium.launch(channel="chrome", headless=headless, args=args)

    if storage_path.exists():
        context = await browser.new_context(storage_state=str(storage_path))
        page = await context.new_page()
        return browser, context, page, False  # reused session, no fresh login
    else:
        context = await browser.new_context()
        page = await context.new_page()
        if not username or not password:
            await browser.close()
            raise RuntimeError(
                f"No storage at {storage_path} and no credentials provided."
            )
        ok = await _login(page, username, password)
        if not ok:
            await browser.close()
            raise RuntimeError("Login failed — check credentials or adjust selectors.")
        await context.storage_state(path=str(storage_path))
        return browser, context, page, True  # fresh login happened


async def _scrape_odds_async(url: str,
                             username: Optional[str],
                             password: Optional[str],
                             storage_path: str,
                             force_login: bool,
                             headless: bool,
                             timeout_sec: int) -> Dict:
    storage = Path(storage_path)

    async with async_playwright() as p:
        browser = context = page = None
        try:
            browser, context, page, did_login = await _ensure_context_and_login(
                p, storage, username, password, headless
            )

            # If forced login requested, ignore stored session and re-login
            if not did_login and force_login:
                await context.close()
                context = await browser.new_context()
                page = await context.new_page()
                if not username or not password:
                    raise RuntimeError("force_login=True but no credentials provided.")
                ok = await _login(page, username, password)
                if not ok:
                    raise RuntimeError("Forced login failed.")
                await context.storage_state(path=str(storage))

            # Capture first matching markets payload
            response_queue: asyncio.Queue[str] = asyncio.Queue()

            async def on_response(response):
                try:
                    if "matchmarketscontentapi/markets?" in response.url:
                        text = await response.text()
                        if response_queue.empty():
                            response_queue.put_nowait(text)
                except Exception as e:
                    print(f"Error while handling response: {e}")

            page.on("response", on_response)

            # Go to competition page
            await page.goto(url, wait_until="domcontentloaded")

            # Best-effort: wait for odds UI
            try:
                await page.wait_for_selector(".sgl-ParticipantOddsOnly80_Odds", timeout=60_000)
            except asyncio.TimeoutError:
                # UI selector may differ; this is non-fatal
                pass

            # Wait for markets payload
            page_content = None
            try:
                page_content = await asyncio.wait_for(response_queue.get(), timeout=timeout_sec)
            except asyncio.TimeoutError:
                print("No markets payload received within timeout.")

            if not page_content:
                return {}

            parser = ParseBet365(page_content)
            return parser.get_full_time_results(url)

        finally:
            # Clean up
            try:
                if context:
                    await context.close()
            except Exception:
                pass
            try:
                if browser:
                    await browser.close()
            except Exception:
                pass


# ---------- Public API (sync wrapper) ----------
def get_bet365_odds(url: str,
                    username: Optional[str] = None,
                    password: Optional[str] = None,
                    storage_path: str = "bet365_state.json",
                    force_login: bool = False,
                    headless: bool = False,
                    timeout_sec: int = 60) -> Dict:
    """
    Fetch full-time odds from a Bet365 competition page.

    Args:
        url: Bet365 competition URL.
        username/password: Optional. Required only if no storage exists or force_login is True.
        storage_path: JSON file to store/reuse session.
        force_login: If True, ignores existing storage and logs in again.
        headless: Run browser headless or visible.
        timeout_sec: Max seconds to wait for the markets payload.

    Returns:
        dict of odds (or {} if nothing captured).
    """
    async_coro = _scrape_odds_async(
        url=url,
        username=username,
        password=password,
        storage_path=storage_path,
        force_login=force_login,
        headless=headless,
        timeout_sec=timeout_sec,
    )

    # If there is already a running event loop (Spyder/Jupyter), run in a worker thread on a Proactor loop.
    try:
        asyncio.get_running_loop()
        has_running_loop = True
    except RuntimeError:
        has_running_loop = False

    if not has_running_loop:
        return asyncio.run(async_coro)

    # Worker thread with a fresh Proactor loop
    result_box = {}
    err_box = {}

    def worker():
        try:
            loop = asyncio.ProactorEventLoop() if os.name == "nt" else asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result_box["data"] = loop.run_until_complete(async_coro)
        except Exception as e:
            err_box["e"] = e
        finally:
            try:
                loop.close()
            except Exception:
                pass

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join()

    if "e" in err_box:
        raise err_box["e"]
    return result_box.get("data", {})

if __name__ == "__main__":
    # Example competition URL
    URL = "https://www.bet365.nl/#/AC/B1/C1/D1002/E91422157/G40/"

    # For first run you must give username & password so the session can be saved.
    # After that, you can comment them out (storage_state.json will be reused).
    odds = get_bet365_odds(
        url=URL,
        username="YOUR_USERNAME",
        password="YOUR_PASSWORD",
        storage_path="bet365_state.json",
        force_login=False,
        headless=False,
        timeout_sec=60,
    )

    print("Full-time odds:", odds)
