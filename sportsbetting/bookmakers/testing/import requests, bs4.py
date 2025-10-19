import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime

url = "https://www.oddsportal.com/football/europe/europa-league/"
html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).text
soup = BeautifulSoup(html, "html.parser")

def iter_jsonld():
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        txt = tag.string or tag.get_text()
        if not txt:
            continue
        try:
            data = json.loads(txt)
        except Exception:
            # Some sites put multiple JSON-LDs or comments; skip any that aren't valid
            continue
        # JSON-LD can be a single object or a list
        if isinstance(data, list):
            for item in data:
                yield item
        else:
            yield data

def last_segment(u: str) -> str:
    # Get the last non-empty path segment (e.g., ".../feyenoord-panathinaikos-j7hJsU7j/" -> "j7hJsU7j")
    p = urlparse(u).path.rstrip("/")
    seg = p.split("/")[-1]
    # If they sometimes add slug-id, split on '-' and take last chunk
    return seg.split("-")[-1] if "-" in seg else seg

events = []
seen_urls = set()

for obj in iter_jsonld():
    # We only want football SportsEvents
    types = obj.get("@type", [])
    if isinstance(types, str):
        types = [types]
    if "SportsEvent" not in types:
        continue
    if obj.get("sport") and str(obj["sport"]).lower() != "football":
        continue

    name = obj.get("name")
    start = obj.get("startDate")          # already ISO 8601 with timezone, e.g. "2025-10-23T18:45:00+02:00"
    u = obj.get("url")

    if not (name and start and u):
        continue
    if u in seen_urls:
        continue
    seen_urls.add(u)

    events.append({
        "name": name,
        "startDate": datetime.fromisoformat(start),
        #"url": u,
        "matchId": last_segment(u),
    })

# Example: print a few
for e in events[:12]:
    print(e)
