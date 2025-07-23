# -*- coding: utf-8 -*-
"""
Dynamic NBA rosters pulled from Basketball‑Reference
====================================================

Public helpers
    get_team_list()  ->  list of 30 full team names
    get_roster(team) ->  {"starters": [...5 names...], "bench": [...rest...]}

Data are cached to roster_cache.json for 12 h.
"""
import json
import time
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import pandas as pd

from .utils.scraping import soup

# ---------------- Team → Abbreviation map -----------------
TEAM_ABR: Dict[str, str] = {
    "Atlanta Hawks": "ATL",
    "Boston Celtics": "BOS",
    "Brooklyn Nets": "BRK",
    "Charlotte Hornets": "CHO",
    "Chicago Bulls": "CHI",
    "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL",
    "Denver Nuggets": "DEN",
    "Detroit
