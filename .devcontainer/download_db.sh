#!/usr/bin/env bash
set -euo pipefail

# 1) URL of your newly uploaded dump ZIP
URL="https://github.com/12349010/NBA-Simulator/releases/download/db-sql-v1/nba_dump.zip"

OUT_DIR="data"
ZIP_PATH="${OUT_DIR}/nba_dump.zip"
SQL_PATH="${OUT_DIR}/nba.sqlite"

echo "💾 Downloading SQL dump…"
mkdir -p "${OUT_DIR}"
curl -L "$URL" -o "${ZIP_PATH}"

echo "📦 Unzipping…"
python3 - <<PYCODE
import zipfile, os
from pathlib import Path

zip_path = Path(r"${ZIP_PATH}")
out_dir  = Path(r"${OUT_DIR}")
out_sql  = out_dir / "dump.sql"

with zipfile.ZipFile(zip_path, 'r') as z:
    z.extractall(path=out_dir)

# Rename extracted dump.sql → nba.sqlite
os.rename(out_dir / "dump.sql", out_dir / "nba.sqlite")
print("✅ Created", out_dir / "nba.sqlite")
PYCODE

echo "📂 Final check: $(ls -lh "${SQL_PATH}")"
