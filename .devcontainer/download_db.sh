#!/usr/bin/env bash
set -euo pipefail

# Your GitHub Release asset URL (replace placeholders):
URL="https://github.com/12349010/NBA-Simulator/releases/download/db-sql-v1/nba_dump.zip"

OUT_DIR="data"
ZIP_PATH="${OUT_DIR}/nba_dump.zip"
SQL_PATH="${OUT_DIR}/nba.sqlite"

echo "💾 Downloading SQL dump…"
mkdir -p "${OUT_DIR}"
curl -L "$URL" -o "${ZIP_PATH}"

echo "📦 Unzipping with unzip…"
unzip -o "${ZIP_PATH}" -d "${OUT_DIR}"

# The zip contains dump.sql; rename it:
mv "${OUT_DIR}/dump.sql" "${SQL_PATH}"

echo "📂 Final check: $(ls -lh "${SQL_PATH}")"

