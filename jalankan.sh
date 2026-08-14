#!/bin/bash
# Jalankan aplikasi: ./jalankan.sh  lalu buka http://127.0.0.1:5057
set -e
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "Menyiapkan lingkungan Python (sekali saja)..."
  python3 -m venv .venv
  ./.venv/bin/pip install -q --upgrade pip
  ./.venv/bin/pip install -q -r requirements.txt
fi

if [ ! -d web/node_modules ]; then
  echo "Memasang dependensi antarmuka (sekali saja)..."
  (cd web && npm install --no-audit --no-fund)
fi

if [ ! -d web/dist ] || [ -n "$(find web/src -newer web/dist -type f 2>/dev/null | head -1)" ]; then
  echo "Membangun antarmuka..."
  (cd web && npm run build)
fi

echo "Aplikasi berjalan di http://127.0.0.1:5057  (Ctrl+C untuk berhenti)"
exec ./.venv/bin/python app.py
