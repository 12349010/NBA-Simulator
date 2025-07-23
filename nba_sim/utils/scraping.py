from pathlib import Path
import time, random, requests
from bs4 import BeautifulSoup

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": "nba-sim/0.8.1 (+https://github.com/you)"}

def fetch_url(url: str, ttl_hours: int = 24) -> str:
    """
    Return page HTML (cached). If HTTP error, fall back to cache;
    if no cache, return empty string.
    """
    fname = CACHE_DIR / f"{abs(hash(url))}.html"
    # use fresh cache if valid
    if fname.exists() and (time.time() - fname.stat().st_mtime) < ttl_hours * 3600:
        return fname.read_text(encoding="utf-8")

    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        html = r.content.decode("utf-8", errors="replace")
        fname.write_text(html, encoding="utf-8")
        time.sleep(random.uniform(1, 2.5))
        return html
    except requests.exceptions.RequestException:
        if fname.exists():
            return fname.read_text(encoding="utf-8")
        return ""   # graceful fallback

def soup(url: str, ttl_hours: int = 24) -> BeautifulSoup:
    return BeautifulSoup(fetch_url(url, ttl_hours), "lxml")
