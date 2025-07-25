#!/usr/bin/env bash
set -euo pipefail

# ← Your actual release URL here:
URL="https://github.com/12349010/NBA-Simulator/releases/download/db-sql-v1/nba_dump.zip"

OUT_DIR="data"
ZIP_PATH="${OUT_DIR}/nba_dump.zip"
DUMP_SQL="${OUT_DIR}/dump.sql"
SQL_PATH="${OUT_DIR}/nba.sqlite"

echo "💾 Downloading SQL dump…"
mkdir -p "${OUT_DIR}"
curl -L "$URL" -o "${ZIP_PATH}"

echo "📦 Unzipping dump.sql…"
unzip -o "${ZIP_PATH}" -d "${OUT_DIR}"

echo "🗜️ Importing into sqlite…"
# Create a fresh DB and run the SQL script
sqlite3 "${SQL_PATH}" < "${DUMP_SQL}"

echo "📂 Final check: $(ls -lh "${SQL_PATH}")"