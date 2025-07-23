"""
Very thin ESPN injury scraper.
If a player is listed as 'Out' or 'Doubtful', we flag them so rotation
minutes drop to zero.
"""
import re, requests
from bs4 import BeautifulSoup
from unidecode import unidecode

USER_AGENT = {"User-Agent": "nba-sim/0.3 (+https://github.com/you)"}

def _slug(name: str) -> str:
    return unidecode(name.lower()).replace(".", "").replace(" ", "-")

def player_is_out(full_name: str) -> bool:
    try:
        url = f"https://www.espn.com/nba/player/_/name/{_slug(full_name)}"
        html = requests.get(url, headers=USER_AGENT, timeout=15).text
        soup = BeautifulSoup(html, "lxml")
        status = soup.find(string=re.compile(r"Status"))
        if not status:
            return False
        row = status.find_parent("tr")
        val = row.find_all("td")[-1].get_text(strip=True)
        return any(tag in val.lower() for tag in ("out", "doubtful", "day-to-day"))
    except Exception:
        return False            # fail open
