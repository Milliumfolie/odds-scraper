# oddsportal_easy.py
# Minimal: give it a listing URL, get back {name: {...}} in your requested shape.

from __future__ import annotations
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import requests, json, re, time, base64

from bs4 import BeautifulSoup
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

# =========================
# Fixed config (edit here)
# =========================
VERSION_ID = 1
SPORT_ID   = 1
XHASH      = "f6dd57f5645fa984264fdf5c5e951772"   # <- keep fresh if site changes it
SCT        = "J*8sQ!p$7aD_fR2yW@gHn*3bVp#sAdLd_k"
ACT        = "5b9a8f2c3e6d1a4b7c8e9d0f1a2b3c4d"

BOOK_KEY         = "bet365"   # outward-facing key in your result
BOOKMAKER_ID     = "16"       # internal id used in the odds payload (Bet365)

LISTING_HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
FEED_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "deflate",
    "content-type": "application/json",
    "referer": "https://www.oddsportal.com/",
    "user-agent": LISTING_HEADERS["user-agent"],
    "x-requested-with": "XMLHttpRequest",
}


def get_listing_odds(
    listing_url: str,
    *,
    per_request_sleep: float = 0.25,
    # Optional overrides (you can ignore these in normal use)
    version_id: int = VERSION_ID,
    sport_id: int = SPORT_ID,
    xhash: str = XHASH,
    sct: str = SCT,
    act: str = ACT,
    book_key: str = BOOK_KEY,
    bookmaker_id: str = BOOKMAKER_ID,
    timeout: int = 20,
    max_events: Optional[int] = None,  # for quick tests
) -> Dict[str, Dict[str, Any]]:
    """
    Return:
      results[name] = {
          "date": <ISO8601 startDate from JSON-LD>,
          "odds": {book_key: [home, draw, away]},
          "id": {book_key: <matchId>},
          "competition": <string>,
      }
    """

    session = requests.Session()

    # --- 1) Grab and parse listing page (JSON-LD blocks) ---
    html = _get_text(session, listing_url, headers=LISTING_HEADERS, timeout=timeout)
    soup = BeautifulSoup(html, "html.parser")

    events: List[Dict[str, Any]] = []
    seen_ids = set()

    for tag in soup.find_all("script", {"type": "application/ld+json"}):
        raw = (tag.string or tag.text or "").strip()
        if not raw:
            continue

        # Be tolerant: content may be a dict, list, or multiple objects smashed together.
        for obj in _jsonish_blocks(raw):
            if not isinstance(obj, dict):
                continue
            types = obj.get("@type")
            types = types if isinstance(types, list) else ([types] if types else [])
            if "SportsEvent" not in types and "Event" not in types:
                continue

            name = obj.get("name")
            start = obj.get("startDate")
            url = obj.get("url")
            if not (name and start and url):
                continue

            mid = _match_id_from_url(url)
            key = mid or url
            if not key or key in seen_ids:
                continue
            seen_ids.add(key)

            events.append({"name": name, "startDate": start, "url": url, "matchId": mid})

            if max_events and len(events) >= max_events:
                break
        if max_events and len(events) >= max_events:
            break

    if not events:
        return {}

    # --- 2) For each event, fetch + decrypt odds feed, then extract 1X2 ---
    name_counts: Dict[str, int] = {}
    results: Dict[str, Dict[str, Any]] = {}

    for ev in events:
        mid = ev.get("matchId")
        if not mid:
            continue

        feed_url = f"https://www.oddsportal.com/match-event/{version_id}-{sport_id}-{mid}-1-2-{xhash}.dat"

        try:
            enc = _get_text(session, feed_url, headers=FEED_HEADERS, timeout=timeout)
            parsed = _decrypt_and_load(enc, sct=sct, act=act)
            odds = _extract_1x2_odds(parsed, bookmaker_id)
            if not odds:
                continue

            competition = (
                parsed.get("d", {}).get("competition")
                or parsed.get("d", {}).get("tournament")
                or ""
            )

            # Avoid duplicate dict keys if two matches have identical names
            name = ev["name"]
            cnt = name_counts.get(name, 0) + 1
            name_counts[name] = cnt
            if cnt > 1:
                name = f"{name} ({cnt})"

            results[name] = {
                "date": ev["startDate"],
                "odds": {book_key: odds},
                "id": {book_key: mid},
                "competition": competition,
            }

        except Exception as e:
            # Swallow per-match errors; skip problematic matches
            # (If you want logs, print(f"[WARN] {mid}: {e}"))
            pass

        if per_request_sleep:
            time.sleep(per_request_sleep)

    return results


# =========================
# Tiny helpers (private)
# =========================

def _get_text(session: requests.Session, url: str, *, headers: dict, timeout: int) -> str:
    # Simple retry: 3 tries, short backoff
    for i in range(3):
        try:
            r = session.get(url, headers=headers, timeout=timeout)
            r.raise_for_status()
            return r.text.strip()
        except requests.RequestException:
            if i == 2:
                raise
            time.sleep(0.6 * (i + 1))
    raise RuntimeError("unreachable")

def _jsonish_blocks(raw: str):
    """Yield JSON objects from raw script content (robust to arrays / multiple objects)."""
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            for x in parsed:
                yield x
        else:
            yield parsed
        return
    except Exception:
        pass

    # Fallback: scan for {...} and attempt to load each
    for m in re.finditer(r"\{.*?\}", raw, flags=re.S):
        try:
            yield json.loads(m.group(0))
        except Exception:
            continue

def _match_id_from_url(u: str) -> Optional[str]:
    """…/feyenoord-panathinaikos-j7hJsU7j/ -> j7hJsU7j"""
    path = urlparse(u).path.rstrip("/")
    last = path.split("/")[-1]
    m = re.search(r"-([A-Za-z0-9]{6,12})$", last)
    return m.group(1) if m else None

def _fix_b64(s: str) -> str:
    return s + "=" * (-len(s) % 4)

def _decrypt_and_load(e_b64: str, *, sct: str, act: str) -> Dict[str, Any]:
    # atob(e) -> "<cipher_b64>:<iv_hex>"
    payload = base64.b64decode(_fix_b64(e_b64)).decode("ascii")
    cipher_b64, iv_hex = payload.split(":", 1)
    ct = base64.b64decode(_fix_b64(cipher_b64))
    iv = bytes.fromhex(iv_hex)

    kdf = PBKDF2HMAC(
        algorithm=SHA256(),
        length=32,
        salt=act.encode("utf-8"),
        iterations=1000,
        backend=default_backend(),
    )
    key = kdf.derive(sct.encode("utf-8"))

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    dec = cipher.decryptor()
    pt = dec.update(ct) + dec.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    pt = unpadder.update(pt) + unpadder.finalize()
    return json.loads(pt.decode("utf-8"))

def _extract_1x2_odds(event_json: Dict[str, Any], bookmaker_id: str) -> Optional[List[float]]:
    """Return [home, draw, away] floats for 1X2, or None."""
    try:
        odds = (
            event_json["d"]["oddsdata"]["back"]["E-1-2-0-0-0"]["odds"][bookmaker_id]
        )
    except Exception:
        return None

    def num(x):
        if isinstance(x, (int, float)): return float(x)
        if isinstance(x, str):
            try: return float(x)
            except ValueError: return None
        if isinstance(x, (list, tuple)) and x:  # sometimes arrays
            return num(x[0])
        return None

    home, draw, away = num(odds.get("0")), num(odds.get("1")), num(odds.get("2"))
    if None in (home, draw, away):
        return None
    return [home, draw, away]

# ---------------- Example CLI ----------------
if __name__ == "__main__":
    url = "https://www.oddsportal.com/football/europe/europa-league/"
    data = get_listing_odds(url, max_events=6)  # limit for a quick peek
    for k, v in data.items():
        print(k, "->", v)
