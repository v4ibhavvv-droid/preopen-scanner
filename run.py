"""Entry point — NSE pre-open gap-up scanner (personal use, broker-free).

Run:   python run.py            -> live (6s poll, port 8787)
       python run.py --dev      -> fixture se offline dashboard test
       python run.py --once     -> ek baar fetch karke JSON dump

Resilience features:
  - Poller thread never dies (all exceptions caught + logged)
  - Watchdog thread auto-restarts poller if it stalls (>120s no successful poll)
  - Exponential backoff on consecutive NSE failures (6s -> 12s -> 24s -> 60s max)
  - Health endpoint: GET /health -> poller status, last poll, error count
  - Dashboard shows STALE warning if data > 2 min old
"""
import argparse
import json
import os
import threading
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from config import COOKIE_WARM_MAX_AGE, FIXTURE, POLL_INTERVAL_SEC, PORT
from scanner.dashboard import Board, serve
from scanner.engine import Engine
from scanner.kite_links import chart_url as kite_chart_url
from scanner.nse_client import NSEClient

IST = ZoneInfo("Asia/Kolkata")

# ---------- Env overrides (Render/cloud deploy ke liye — local pe default wahi purana) ----------
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", PORT))
POLL_INTERVAL_SEC = float(os.environ.get("POLL_INTERVAL_SEC", POLL_INTERVAL_SEC))

# ---------- Poller state (shared with watchdog + health endpoint) ----------
_poller_state = {
    "alive": False,
    "last_success_ts": 0.0,
    "consecutive_errors": 0,
    "total_errors": 0,
    "total_polls": 0,
    "last_error": "",
}
_state_lock = threading.Lock()

# Poller generation (epoch): watchdog restart pe epoch bump karta he,
# purana (stalled) poller thread agle loop check pe khud exit kar jata he —
# warna 2 pollers NSE ko double-rate hit karte (Akamai block risk).
_epoch = 0
_epoch_lock = threading.Lock()


def _bump_epoch() -> int:
    global _epoch
    with _epoch_lock:
        _epoch += 1
        return _epoch


def _current_epoch() -> int:
    with _epoch_lock:
        return _epoch


def _update_state(**kwargs):
    with _state_lock:
        _poller_state.update(kwargs)


def get_poller_state() -> dict:
    with _state_lock:
        return dict(_poller_state)


def poller(board: Board, engine: Engine, interval: float):
    """NSE pre-open poll (resilient — never dies)."""
    my_epoch = _current_epoch()  # watchdog ne naya poller start kiya to purana khud band
    client = NSEClient(warm_max_age=COOKIE_WARM_MAX_AGE)
    _update_state(alive=True, last_success_ts=time.time())
    while _current_epoch() == my_epoch:
        try:
            raw = client.fetch_preopen()
            rows, meta = engine.process(raw)
            meta["nse_n"] = len(rows)
            meta["total"] = len(rows)
            for r in rows:
                r["url"] = kite_chart_url(r["symbol"], r.get("series", "EQ"))
            board.publish(rows, meta)
            ts = datetime.now(IST).strftime("%H:%M:%S")
            print(f"[{ts}] mis_total={len(rows)} active={meta.get('active_n')}", flush=True)

            with _state_lock:
                _poller_state["last_success_ts"] = time.time()
                _poller_state["consecutive_errors"] = 0
                _poller_state["total_polls"] += 1
                _poller_state["last_error"] = ""
        except Exception as e:
            err = repr(e)[:200]
            with _state_lock:
                _poller_state["consecutive_errors"] += 1
                _poller_state["total_errors"] += 1
                _poller_state["last_error"] = err
            print(f"poll error: {err}", flush=True)

        # Exponential backoff on consecutive failures
        with _state_lock:
            ce = _poller_state["consecutive_errors"]
        if ce == 0:
            sleep_time = interval
        else:
            sleep_time = min(interval * (2 ** min(ce, 4)), 60.0)
            print(f"  -> backoff: sleeping {sleep_time:.0f}s (consecutive errors: {ce})", flush=True)
        time.sleep(sleep_time)


def watchdog(board: Board, engine: Engine, interval: float):
    """Monitor poller health. Auto-restart if stalled (>120s no successful poll)."""
    while True:
        time.sleep(30)
        state = get_poller_state()
        if not state["alive"]:
            continue
        age = time.time() - state["last_success_ts"]
        if age > 120:
            print(f"WATCHDOG: poller stalled ({age:.0f}s since last success). Restarting...", flush=True)
            _bump_epoch()  # purana thread agle iteration pe exit karega (duplicate poller bug fix)
            t = threading.Thread(target=poller, args=(board, engine, interval), daemon=True)
            t.start()
            _update_state(alive=True, last_success_ts=time.time(), consecutive_errors=0)
            print("WATCHDOG: poller restarted.", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", action="store_true", help="fixture se offline")
    ap.add_argument("--once", action="store_true", help="ek baar fetch + dump")
    args = ap.parse_args()

    engine = Engine()
    board = Board()

    if args.dev:
        raw = json.loads(FIXTURE.read_text())
        rows, meta = engine.process(raw)
        for r in rows:
            r["url"] = kite_chart_url(r["symbol"], r.get("series", "EQ"))
        board.publish(rows, meta, "dev-fixture")
        print(f"[dev] {len(rows)} rows loaded from fixture")
        serve(board, HOST, PORT).serve_forever()
        return

    if args.once:
        client = NSEClient(warm_max_age=COOKIE_WARM_MAX_AGE)
        raw = client.fetch_preopen()
        rows, meta = engine.process(raw)
        print(json.dumps({"meta": meta, "count": len(rows), "top20": rows[:20]},
                         indent=2, ensure_ascii=False))
        return

    print(f"[live] NSE poller {POLL_INTERVAL_SEC}s -> http://{HOST}:{PORT} (Ctrl+C = band)")
    print(f"[live] Watchdog enabled (auto-restart if poller stalls >120s)")
    print(f"[live] Health endpoint: http://{HOST}:{PORT}/health")
    # Pehle port bind karo (fail-fast, friendly message) —
    # us ke BAAD hi poller/watchdog threads start (bind-fail par NSE bekaar hit na ho)
    try:
        httpd = serve(board, HOST, PORT, get_poller_state)
    except OSError as e:
        if getattr(e, "errno", None) in (48, 98):  # 48=macOS EADDRINUSE, 98=Linux EADDRINUSE
            print("", flush=True)
            print(f"ERROR: port {PORT} pehle se busy he — koi purana scanner chal raha he.", flush=True)
            print("       Process band karne ke liye (Terminal):", flush=True)
            print(f"         lsof -nP -tiTCP:{PORT} -sTCP:LISTEN | xargs kill -9", flush=True)
            print("       Ya START_SCANNER.command dobara double-click karo —", flush=True)
            print("       wo purana server khud band karke fresh start karta he.", flush=True)
            print("", flush=True)
        else:
            raise
        return
    threading.Thread(target=poller, args=(board, engine, POLL_INTERVAL_SEC), daemon=True).start()
    threading.Thread(target=watchdog, args=(board, engine, POLL_INTERVAL_SEC), daemon=True).start()
    httpd.serve_forever()


if __name__ == "__main__":
    main()
