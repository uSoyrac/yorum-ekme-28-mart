#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📱 Play Reviewer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! command -v python3 &>/dev/null; then
  osascript -e 'display alert "Python bulunamadı" message "python.org/downloads adresinden Python 3 kurun." as critical'
  exit 1
fi

VENV="$DIR/.venv"
MARKER="$VENV/.installed_v6"

if [ ! -f "$MARKER" ]; then
  echo "→ İlk kurulum (~2 dk, yalnızca bir kez)…"
  rm -rf "$VENV"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --upgrade pip -q
  "$VENV/bin/pip" install flask google-play-scraper pandas openpyxl xlsxwriter -q
  touch "$MARKER"
  echo "✅ Kurulum tamamlandı."
else
  echo "✅ Hazır."
fi

# Chrome güvenli portlar: 8080, 8888, 9000 vb.
# 5055-5099 Chrome tarafından engelleniyor!
PORT=8080
while lsof -i :"$PORT" &>/dev/null 2>&1; do
  PORT=$((PORT+1))
done

export PORT=$PORT
echo "→ http://localhost:$PORT"
echo "→ Kapatmak için bu pencereyi kapatın"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

(sleep 1.5 && open "http://localhost:$PORT") &
"$VENV/bin/python3" "$DIR/server.py"
