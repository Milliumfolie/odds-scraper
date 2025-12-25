"""Shared helpers for bookmaker parsers.

Keep parsers consistent and testable by providing small utilities:
- safe_text: extract text from BeautifulSoup element or return default
- parse_float: robust float parsing (handle commas/dots, empty)
- iso_datetime: normalize datetimes (accept strings, datetime objects or None)
- validate_parser_output: ensure parser returns expected structure
- parse_html_page: helper to construct BeautifulSoup and pass to parser
"""
from __future__ import annotations

from typing import Any, Dict, Optional
import datetime
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def safe_text(element, default: str = "") -> str:
    """Return element.text stripped or default if element is None."""
    try:
        if element is None:
            return default
        return element.get_text(strip=True)
    except Exception:
        return default


def parse_float(text: Any) -> Optional[float]:
    """Parse a string to float, handling comma decimals and stray characters.

    Returns None if parsing fails.
    """
    if text is None:
        return None
    try:
        s = str(text).strip()
        s = s.replace("\u00a0", "")  # non-breaking space
        s = s.replace(",", ".")
        # remove unexpected characters except digits, dot and minus
        cleaned = "".join(ch for ch in s if ch.isdigit() or ch in ".-")
        if not cleaned:
            return None
        return float(cleaned)
    except Exception:
        logger.debug("parse_float failed for %r", text)
        return None


def iso_datetime(dt: Any) -> Optional[datetime.datetime]:
    """Normalize input to a datetime or return None.

    Accepts datetime, date, ISO strings, or None.
    """
    if dt is None:
        return None
    if isinstance(dt, datetime.datetime):
        return dt
    if isinstance(dt, datetime.date):
        return datetime.datetime.combine(dt, datetime.time())
    try:
        # try ISO parse
        return datetime.datetime.fromisoformat(str(dt))
    except Exception:
        try:
            # fallback: parse common formats
            from dateutil.parser import parse as _parse

            return _parse(str(dt))
        except Exception:
            logger.debug("iso_datetime failed to parse %r", dt)
            return None


def validate_parser_output(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure parsed dict uses the standard schema and normalize dates to datetime objects.

    - Keeps only matches where odds are present and in list form with at least 2 values.
    - Converts date fields with iso_datetime.
    - Ensures 'odds', 'id', 'date', 'competition' keys exist per match.
    """
    out = {}
    for match, data in parsed.items():
        try:
            if not isinstance(data, dict):
                logger.debug("Skipping %r: data is not a dict", match)
                continue
            odds = data.get("odds")
            if not isinstance(odds, dict) or not odds:
                logger.debug("Skipping %r: missing or invalid odds", match)
                continue
            # take first bookmaker's odds as sample
            first_odds = next(iter(odds.values()))
            if not isinstance(first_odds, (list, tuple)) or len(first_odds) < 2:
                logger.debug("Skipping %r: odds list invalid (%r)", match, first_odds)
                continue
            date_val = iso_datetime(data.get("date"))
            out[match] = {
                "odds": odds,
                "id": data.get("id", {}),
                "date": date_val,
                "competition": data.get("competition", "")
            }
        except Exception:
            logger.exception("Error validating match %r", match)
    return out


def parse_html_page(html: str):
    """Return BeautifulSoup object from html text.

    Parsers can accept BeautifulSoup instead of relying on Selenium during tests.
    """
    return BeautifulSoup(html, "lxml")
