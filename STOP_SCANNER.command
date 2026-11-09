#!/bin/bash
# ================================================
#  PRE-OPEN GAP-UP SCANNER — ONE-CLICK STOPPER
#  Double-click karo =>
#    1. Server process properly band (SIGTERM, fir SIGKILL)
#    2. Port 8787 free confirm
#    3. Clean shutdown report
#
#  Window khud band ho jayegi 2-3 second me.
# ================================================

PORT=8787

echo "🛑 PRE-OPEN GAP-UP SCANNER band ho raha he..."
echo "──────────────────────────────────────────────"

# sirf LISTENER pakdo — dashboard-kholi tabs/browsers ko nahi
listener_pids() { lsof -nP -tiTCP:$PORT -sTCP:LISTEN 2>/dev/null; }

PIDS=$(listener_pids)

if [ -z "$PIDS" ] && ! pgrep -f "preopen-scanner/run.py" >/dev/null 2>&1; then
  echo "   Status: pehle se band he ✔"
else
  echo "$PIDS" | xargs kill 2>/dev/null
  pkill -f "preopen-scanner/run.py" 2>/dev/null

  # 5 sec tak port-free ka intezaar (0.5s poll)
  for i in 1 2 3 4 5 6 7 8 9 10; do
    [ -z "$(listener_pids)" ] && break
    sleep 0.5
  done

  # ab bhi zinda?
  if [ -n "$(listener_pids)" ]; then
    echo "   Force-kill lagaya (process zidd kar raha tha)..."
    listener_pids | xargs kill -9 2>/dev/null
    sleep 0.5
  fi

  echo "   Server: band ✔"
fi

# final verify
if [ -n "$(listener_pids)" ]; then
  echo "   Port $PORT: FIR BHI BUSY ⚠ (1-2 sec me dobara double-click karo)"
else
  echo "   Port $PORT: free ✔"
fi

echo "──────────────────────────────────────────────"
echo "Done. Dashboard ab 127.0.0.1:$PORT pe respond nahi karega."
echo "Wapas start: START_SCANNER.command double-click."
echo ""
sleep 2
