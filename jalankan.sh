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
echo "Aplikasi berjalan di http://127.0.0.1:5057  (tekan Ctrl+C untuk berhenti)"
exec ./.venv/bin/python app.py
