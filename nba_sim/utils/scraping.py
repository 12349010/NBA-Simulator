from pathlib import Path
import time, random, requests
from bs4 import BeautifulSoup

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": "nba-sim/0.1 (+https://github.com/you)"}

def fetch_url(url: str, ttl_hours: int = 24) -> str:
    """
    Download *or* load cached copy of a web page.
    """
    fname = CACHE_DIR / f"{abs(hash(url))}.html"
    if fname.exists() and (time.time() - fname.stat().st_mtime) < ttl_hours * 3600:
        return fname.read_text(encoding="utf-8")

    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    fname.write_text(resp.text, encoding="utf-8")
    time.sleep(random.uniform(1, 2.5))   # polite delay for the host
    return resp.text

def soup(url: str, ttl_hours: int = 24) -> BeautifulSoup:
    """Shortcut that returns a BeautifulSoup object."""
    return BeautifulSoup(fetch_url(url, ttl_hours), "lxml")
