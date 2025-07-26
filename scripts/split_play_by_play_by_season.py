#!/usr/bin/env python3
import pandas as pd
import gzip
from pathlib import Path

# 1) Paths
DATA_DIR = Path("data")
SRC      = DATA_DIR / "play_by_play.csv.gz"
GAME_CSV = DATA_DIR / "game.csv"

# 2) Load game → season mapping (dedupe by game_id)
print("🔍 Loading game→season mapping…")
game_df = pd.read_csv(GAME_CSV, usecols=["game_id","season_id"])
game_df["game_id"]   = game_df["game_id"].astype(int)
game_df["season_id"] = game_df["season_id"].astype(int)

# Drop duplicate game_id rows (keep the first)
game_df = game_df.drop_duplicates(subset="game_id", keep="first")

season_map = game_df.set_index("game_id")["season_id"]

# 3) Prepare writers
writers = {}

print("🗂️  Starting to stream split by season…")
chunksize = 500_000
for chunk in pd.read_csv(SRC, compression="gzip", chunksize=chunksize):
    chunk["game_id"] = chunk["game_id"].astype(int)
    # Map to season; rows with no mapping become NaN
    chunk["season_id"] = chunk["game_id"].map(season_map)
    chunk = chunk.dropna(subset=["season_id"])
    chunk["season_id"] = chunk["season_id"].astype(int)

    # Group and write out per‑season
    for season, sub in chunk.groupby("season_id"):
        out_path = DATA_DIR / f"play_by_play_{season}.csv.gz"
        if season not in writers:
            writers[season] = gzip.open(out_path, "wt", compresslevel=9)
            sub.to_csv(writers[season], index=False, header=True)
        else:
            sub.to_csv(writers[season], index=False, header=False)

# 4) Close files and report
for f in writers.values():
    f.close()

print("✅ Split complete. Files created:")
for season in sorted(writers):
    size_mb = (DATA_DIR / f"play_by_play_{season}.csv.gz").stat().st_size / 1e6
    print(f"  • play_by_play_{season}.csv.gz — {size_mb:.1f} MB")