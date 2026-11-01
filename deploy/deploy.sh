#!/usr/bin/env bash
# Baut die Seite und spielt sie per rsync auf den Hostinger-VPS.
# Zugang über Umgebungsvariablen, nichts davon im Repository:
#   BHT_HOST   z. B. 203.0.113.10 oder vps.example.net
#   BHT_USER   SSH-Nutzer, z. B. deploy
#   BHT_PATH   Zielverzeichnis, Standard /var/www/bundeshaushaltstracker
# Aufruf:  BHT_HOST=... BHT_USER=... ./deploy/deploy.sh
set -euo pipefail

: "${BHT_HOST:?BHT_HOST fehlt}"
: "${BHT_USER:?BHT_USER fehlt}"
BHT_PATH="${BHT_PATH:-/var/www/bundeshaushaltstracker}"

cd "$(dirname "$0")/.."

echo "1/3 Pipeline prüfen (keine Rohdaten laden, nur Build-Dateien bestätigen)"
test -f data/build/index.json || { echo "data/build fehlt: cd pipeline && uv run bht build"; exit 1; }

echo "2/3 Website bauen"
(cd web && npm ci --silent && npm run build)

echo "3/3 Hochladen nach ${BHT_USER}@${BHT_HOST}:${BHT_PATH}"
rsync -az --delete --exclude ".DS_Store" web/dist/ "${BHT_USER}@${BHT_HOST}:${BHT_PATH}/"

echo "Fertig. Stand der Daten: $(python3 -c "import json;print(json.load(open('data/build/index.json'))['erzeugt'])" 2>/dev/null || echo unbekannt)"
