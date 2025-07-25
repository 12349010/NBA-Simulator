#!/usr/bin/env bash
set -euo pipefail

# File ID from your Google Drive link
FILE_ID="1vvpcwTK6s11d8i5Cpb_sAAKN86AFaKjx"
OUT="data/nba.sqlite"

echo "💾 Downloading nba.sqlite into ${OUT} …"
mkdir -p "$(dirname "${OUT}")"

# Use Python's gdown module to handle the Drive confirm-token for large files
python3 - <<PYCODE
import gdown
url = f"https://drive.google.com/uc?export=download&id={FILE_ID}"
print(f"→ gdown downloading from: {url}")
gdown.download(url, "$OUT", quiet=False)
PYCODE

echo "✅ Download complete: $(ls -lh "${OUT}")"