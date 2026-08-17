#!/bin/sh
# Jalankan apa pun di atas SALINAN data.db, tidak pernah yang asli.
#   uji.sh ./.venv/bin/python -c "..."
set -e
SB="$(dirname "$0")"
ASLI=/Users/vio/fingerprint/app/data.db
cp "$ASLI" "$SB/kerja.db"
DATABASE_URL="sqlite:///$SB/kerja.db"
export DATABASE_URL
echo "[uji] memakai $DATABASE_URL" >&2
exec "$@"
