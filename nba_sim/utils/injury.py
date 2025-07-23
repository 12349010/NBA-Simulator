"""
ESPN player‑page scraper that returns detailed injury status.

Categories we recognise:
    - out            -> cap 0 minutes
    - doubtful       -> cap 8 minutes
    - questionable   -> cap 16 minutes
    - probable       -> cap 28 minutes
    - day‑to‑day     -> treated as probable
"""
import re, requests
from bs4 import BeautifulSoup
from unidecode import unidecode

UA = {"User-Agent": "nba-sim/0.5 (+https://github.com/you)"}

def _slug(name: str) -> str:
    return unidecode(name.lower()).replace(".", "").replace(" ", "-")

def get_status(full_name: str) -> str:
    """
    Returns one of: 'out', 'doubtful', 'questionable', 'probable', 'healthy'
    """
    try:
        url = f"https://www.espn.com/nba/player/_/name/{_slug(full_name)}"
        html = requests.get(url, headers=UA, timeout=15).text
        soup = BeautifulSoup(html, "lxml")

        # find injury table row
        cell = soup.find(string=re.compile(r"Status", re.I))
        if not cell:
            return "healthy"
        val_text = cell.find_parent("tr").find_all("td")[-1].get_text(" ", strip=True).lower()

        for key in ("out", "doubtful", "questionable", "probable", "day-to-day"):
            if key in val_text:
                return "probable" if key == "day-to-day" else key
        return "healthy"
    except Exception:
        return "healthy"

def minutes_cap(status: str) -> int:
    return {
        "out":          0,
        "doubtful":     8,
        "questionable": 16,
        "probable":     28,
        "healthy":      34
    }.get(status, 34)
