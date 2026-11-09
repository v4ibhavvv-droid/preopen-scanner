#!/bin/bash
# ================================================
#  PRE-OPEN GAP-UP SCANNER — ONE-CLICK LAUNCHER
#  Double-click karo =>
#    1. Purana server PROPERLY band (bar-bar restart 100% safe)
#    2. Fresh server start (6-sec NSE pre-open poller)
#    3. Dashboard READY hone par browser me khud khulta he
#
#  Band karne ke liye: is window me Ctrl+C, ya window close
# ================================================

PORT=8787
DIR="$(cd "$(dirname "$0")" && pwd)"

# 0) .venv mojood hai? (galti se folder hata diye to clean error)
if [ ! -x "$DIR/.venv/bin/python" ]; then
  echo "ERROR: .venv nahi mila -> $DIR/.venv"
  echo "Project folder wahi rakho aur dobara double-click karo."
  read -n 1 -s -r -p "Window band karne ke liye koi bhi key dabao..."
  exit 1
fi

# sirf LISTENER pakdo — dashboard tab/browser jaise client connections ko nahi
listener_pids() { lsof -nP -tiTCP:$PORT -sTCP:LISTEN 2>/dev/null; }

# 1) PURANA SERVER ROBUSTLY BAND:
#    TERM -> 5s tak port free hone ka intezaar -> fir bhi zinda? kill -9
PIDS=$(listener_pids)
if [ -n "$PIDS" ]; then
  echo "Purana server chal raha tha (pid: $PIDS) — properly band kar raha hu..."
  echo "$PIDS" | xargs kill 2>/dev/null
  # 10 x 0.5s = 5 sec tak bina busy-loop poll
  for i in 1 2 3 4 5 6 7 8 9 10; do
    [ -z "$(listener_pids)" ] && break
    sleep 0.5
  done
  # ab bhi zinda he? force
  if [ -n "$(listener_pids)" ]; then
    echo "   Zidd kar raha tha... force-kill (kill -9)"
    listener_pids | xargs kill -9 2>/dev/null
    sleep 0.5
  fi
fi

# 2) PORT FREE VERIFY — na hua to clean error, koi traceback nahi
if [ -n "$(listener_pids)" ]; then
  echo ""
  echo "ERROR: port $PORT ab tak busy he (koi aur process pakad ke baitha he)."
  echo "       STOP_SCANNER.command dobara double-click karo, ya Terminal me:"
  echo "         lsof -nP -tiTCP:$PORT -sTCP:LISTEN | xargs kill -9"
  read -n 1 -s -r -p "Window band karne ke liye koi bhi key dabao..."
  exit 1
fi

clear
echo "🚀 PRE-OPEN GAP-UP SCANNER start ho raha hai..."
echo "──────────────────────────────────────────────"
echo "   Dashboard : http://127.0.0.1:$PORT"
echo "   Poll      : har 6 second (live NSE pre-open)"
echo "   Band      : Ctrl+C ya window close"
echo "──────────────────────────────────────────────"
echo ""

# 3) Cache-less start (project folder hamesha clean — __pycache__ generate na ho)
export PYTHONDONTWRITEBYTECODE=1

# 4) Server start
"$DIR/.venv/bin/python" "$DIR/run.py" &
SRV_PID=$!

# 5) SERVER READY hone par hi browser kholo (/health max 10s tak poll)
#    (agar run.py port-busy wala friendly-error pe band ho jaye, browser kholega hi nahi)
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  if curl -s -m 1 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
    open "http://127.0.0.1:$PORT" 2>/dev/null
    break
  fi
  if ! kill -0 "$SRV_PID" 2>/dev/null; then
    break   # run.py pehle hi band — niche uska message print hoga
  fi
  sleep 0.5
done

# 6) Server zinda rehta he to window waise hi khuli rahti he
wait $SRV_PID

# Crash/Ctrl+C hua to window turant band na ho — reason dikhe
echo ""
echo "Server band ho gaya (Ctrl+C ya crash)."
read -n 1 -s -r -p "Window band karne ke liye koi bhi key dabao..."
