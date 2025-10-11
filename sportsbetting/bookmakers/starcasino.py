# -*- coding: utf-8 -*-
"""
Created on Sat Sep 13 11:14:30 2025

@author: Jorden
"""

from __future__ import annotations

import datetime
import json
from typing import Any, Dict, List, Optional

import requests


def fetch_json(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """
    GET a JSON payload from `url` with optional headers/params.
    Raises for non-2xx and returns a Python dict.
    """
    headers = headers or {"Accept": "application/json"}
    params = params or {}
    resp = requests.get(url, headers=headers, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _index_by_id(items: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    return {
        item["id"]: item
        for item in items
        if isinstance(item, dict) and "id" in item
    }


def _parse_iso8601_aware(s: Optional[str]) -> Optional[datetime.datetime]:
    """
    Parse ISO 8601 strings like '2025-09-13T14:30:00Z' into tz-aware datetimes.
    Returns None on falsy/invalid input.
    """
    if not s or not isinstance(s, str):
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1]
        return datetime.datetime.fromisoformat(s)
    except Exception:
        return None


def parse_starcasino_payload(
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: float = 10.0,
    book_key: str = "starcasino",
) -> Dict[str, Dict[str, Any]]:
    """
    Parse 1x2 odds from the Starcasino-like endpoint and return a dict:
    {
      "<Match Name>": {
        "date": datetime.datetime,                         # tz-aware if source is UTC 'Z'
        "odds": {"starcasino": [home, draw, away]},        # floats; 1000.0 when missing/closed
        "id": {"starcasino": <event_id>},
        "competition": "<League/Competition Name or None>"
      },
      ...
    }
    """
    payload = fetch_json(url, headers=headers, params=params, timeout=timeout)

    # Indices for fast lookup
    markets_by_id = _index_by_id(payload.get("markets", []))
    odds_by_id = _index_by_id(payload.get("odds", []))
    champs_by_id = _index_by_id(payload.get("champs", []))

    # fallback competition if a single champ exists but events lack champId
    default_competition = None
    try:
        if payload.get("champs"):
            default_competition = payload["champs"][0].get("name")
    except Exception:
        default_competition = None

    results: Dict[str, Dict[str, Any]] = {}

    for ev in payload.get("events", []):
        event_id = ev.get("id")
        name = ev.get("name") or f"event_{event_id}"
        name = name.replace(" vs. ", " - ")
        start = ev.get("startDate")  # e.g. "2025-09-13T14:30:00Z"
        date = _parse_iso8601_aware(start)

        # Competition (league) name
        competition = None
        champ_id = ev.get("champId")
        if champ_id in champs_by_id:
            competition = champs_by_id[champ_id].get("name")
        if not competition:
            competition = default_competition

        # Find first 1x2 market for this event
        market_1x2 = None
        for mid in ev.get("marketIds", []):
            mk = markets_by_id.get(mid)
            if mk and mk.get("typeId") == 1 and str(mk.get("name", "")).lower() == "1x2":
                market_1x2 = mk
                break

        # Collect odds in order [1, X, 2]; default to 1000.0
        match_odds = [1000.0, 1000.0, 1000.0]
        if market_1x2:
            # Build selection index for this market
            sel_by_type: Dict[int, Dict[str, Any]] = {}
            for oid in market_1x2.get("oddIds", []):
                o = odds_by_id.get(oid)
                if o:
                    sel_by_type[o.get("typeId")] = o

            # Map typeId -> slot index in [1, X, 2]
            order = {1: 0, 2: 1, 3: 2}
            for t, idx in order.items():
                o = sel_by_type.get(t)
                if o and o.get("oddStatus") == 0 and o.get("price"):
                    try:
                        match_odds[idx] = float(round(o["price"],2))
                    except (TypeError, ValueError):
                        match_odds[idx] = 1000.0

        results[name] = {
            "date": date,
            "odds": {book_key: match_odds},
            "id": {book_key: event_id},
            "competition": competition,
        }

    return results


# ---------- Example usage ----------
if __name__ == "__main__":
    # Replace with your real endpoint:
    url = (
        "https://sb2frontend-altenar2.biahosted.com/api/widget/GetEvents?culture=nl-NL&timezoneOffset=-120&integration=starcasino.nl&deviceType=1&numFormat=en-GB&countryCode=NL&eventCount=0&sportId=0&champIds=19414"
    )

    # Optional: set request headers/params here
    headers: Dict[str, str] = {"Accept": "application/json"}
    params: Dict[str, Any] = {}

    try:
        parsed = parse_starcasino_payload(
            url,
            headers=headers,
            params=params,
            timeout=15.0,
            book_key="starcasino",
        )
        print(json.dumps(parsed, indent=2, ensure_ascii=False, default=str))
    except requests.HTTPError as e:
        print(f"HTTP error: {getattr(e.response, 'status_code', '?')} {getattr(e.response, 'text', '')[:200]}")
    except requests.Timeout:
        print("Request timed out.")
    except requests.RequestException as e:
        print(f"Network error: {e}")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Response was not valid JSON: {e}")
