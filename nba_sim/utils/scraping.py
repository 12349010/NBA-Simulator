from pathlib import Path
import time, random, requests
from bs4 import BeautifulSoup

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "nba-sim/0.6.5 (+https://github.com/you)"}

def fetch_url(url: str, ttl_hours: int = 24) -> str:
    """
    Return page HTML (cached). Always decode as UTF‑8 to avoid mojibake.
    """
    fname = CACHE_DIR / f"{abs(hash(url))}.html"
    if fname.exists() and (time.time() - fname.stat().st_mtime) < ttl_hours * 3600:
        return fname.read_text(encoding="utf-8")

    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    html = r.content.decode("utf-8", errors="replace")   # <‑‑ key change
    fname.write_text(html, encoding="utf-8")
    time.sleep(random.uniform(1, 2.5))  # polite delay
    return html

def soup(url: str, ttl_hours: int = 24) -> BeautifulSoup:
    return BeautifulSoup(fetch_url(url, ttl_hours), "lxml")
