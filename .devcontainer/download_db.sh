#!/usr/bin/env bash
set -e

FILEID=1vvpcwTK6s11d8i5Cpb_sAAKN86AFaKjx
OUT=data/nba.sqlite

echo "💾 Downloading nba.sqlite into \$OUT …"
mkdir -p data

# 1) Fetch Google Drive confirm token
CONFIRM=$(curl -s -c /tmp/cookie \
  "https://drive.google.com/uc?export=download&id=${FILEID}" \
  | grep -Po 'confirm=\K[^&]+' \
)

# 2) Download the file, handling large‑file interstitial
curl -Lb /tmp/cookie \
  "https://drive.google.com/uc?export=download&confirm=${CONFIRM}&id=${FILEID}" \
  -o "${OUT}"

echo "✅ Download complete: \$(ls -lh ${OUT})"
