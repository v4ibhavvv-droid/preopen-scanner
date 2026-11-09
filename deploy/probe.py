"""NSE cloud-probe — 24/7 feasibility test.

Cloud IP se NSE chalega ya nahi — probe 24/7 chala ke statistics banata he:
  GET /          -> status page (browser me live pass-rate + attempts log)
  GET /health    -> JSON: totals, pass-rate, last 60 attempts

ClawCloud me health-check path: /health
Env:
  PORT      (default 8787)
  POLL_SEC  (default 12) — NSE ko gentle rate
"""
import json
import os
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# probe.py deploy/ folder ya container root — dono se chalna chahiye
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scanner.nse_client import NSEClient

PORT = int(os.environ.get("PORT", "8787"))
POLL = float(os.environ.get("POLL_SEC", "12"))
HIST_MAX = 500

_lock = threading.Lock()
_h = []           # history of attempts
_ok = 0
_fail = 0
_started = time.time()


def _rec(ok, detail, ms):
    global _ok, _fail
    with _lock:
        if ok:
            _ok += 1
        else:
            _fail += 1
        _h.append({
            "ts": datetime.now(timezone.utc).strftime("%H:%M:%S") + "Z",
            "ok": ok,
            "ms": round(ms),
            "detail": detail,
        })
        if len(_h) > HIST_MAX:
            del _h[0]


def poll_loop():
    client = NSEClient(warm_max_age=900.0)
    while True:
        t0 = time.time()
        try:
            raw = client.fetch_preopen(timeout=20)
            n = len(raw.get("data") or [])
            t = raw.get("time") or raw.get("timestamp") or ""
            _rec(True, f"HTTP200 symbols={n} nse_time={t}", (time.time() - t0) * 1000)
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] OK symbols={n}", flush=True)
        except Exception as e:
            _rec(False, repr(e)[:160], (time.time() - t0) * 1000)
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] FAIL {repr(e)[:160]}", flush=True)
        time.sleep(POLL)


def stats() -> dict:
    with _lock:
        total = _ok + _fail
        return {
            "ok": _ok,
            "fail": _fail,
            "total": total,
            "pass_rate": round(_ok / total * 100, 1) if total else None,
            "uptime_min": round((time.time() - _started) / 60, 1),
            "poll_sec": POLL,
            "last": _h[-1] if _h else None,
            "history": _h[-60:],
        }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path.startswith("/health"):
                body = json.dumps(stats()).encode()
                ctype = "application/json"
            else:
                s = stats()
                rows = "".join(
                    f"<tr><td>{x['ts']}</td><td class='{'k' if x['ok'] else 'b'}'>"
                    f"{'OK' if x['ok'] else 'FAIL'}</td><td>{x['ms']}ms</td>"
                    f"<td>{x['detail']}</td></tr>"
                    for x in reversed(s["history"][:40])
                )
                body = (
                    "<!doctype html><meta charset=utf-8>"
                    "<meta name=viewport content='width=device-width,initial-scale=1'>"
                    "<title>NSE Cloud Probe</title>"
                    "<style>body{font:13px/1.5 monospace;background:#0b0e17;color:#dfe7f5;margin:24px}"
                    "table{border-collapse:collapse;width:100%}"
                    "td{border-bottom:1px solid #1c2334;padding:4px 8px}"
                    ".k{color:#8be9a1}.b{color:#ff7b8b}</style>"
                    f"<h1>NSE Cloud Probe — pass-rate: {s['pass_rate']}%</h1>"
                    f"<p>ok=<b class=k>{s['ok']}</b> fail=<b class=b>{s['fail']}</b> "
                    f"uptime={s['uptime_min']} min poll={s['poll_sec']}s<br>"
                    f"last={s['last']}</p><table>{rows}</table>"
                ).encode()
                ctype = "text/html; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            print("probe http err:", repr(e)[:120], flush=True)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    threading.Thread(target=poll_loop, daemon=True).start()
    print(f"[probe] POLL={POLL}s PORT={PORT} — serving", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
