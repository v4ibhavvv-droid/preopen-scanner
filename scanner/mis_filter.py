"""Zerodha MIS-allowed symbols list (auto-refresh daily).

Zerodha ka public API `https://api.kite.trade/margins/equity` se
MIS-allowed stocks ka list fetch hota hai. mis_multiplier > 0 wale
symbols MIS me trade kar sakte hain.

Cache: data/mis_allowed.json (1 din valid).
"""
import json
import threading
import time
import urllib.request

from config import DATA_DIR

MARGINS_URL = "https://api.kite.trade/margins/equity"
CACHE_PATH = DATA_DIR / "mis_allowed.json"
CACHE_MAX_AGE = 86400  # 1 day

_lock = threading.Lock()
_mis_set = None


def _load() -> set:
    global _mis_set
    with _lock:
        if _mis_set is not None:
            return _mis_set
        if CACHE_PATH.exists() and (time.time() - CACHE_PATH.stat().st_mtime) < CACHE_MAX_AGE:
            try:
                _mis_set = set(json.loads(CACHE_PATH.read_text()))
                return _mis_set
            except Exception:
                _mis_set = None
        _fetch_locked()
        return _mis_set or set()


def _fetch_locked():
    global _mis_set
    try:
        with urllib.request.urlopen(MARGINS_URL, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8", errors="replace"))
        syms = set()
        for x in data:
            sym = (x.get("tradingsymbol") or "").strip()
            mult = x.get("mis_multiplier") or 0
            if sym and mult > 0:
                syms.add(sym)
        _mis_set = syms
        try:
            CACHE_PATH.write_text(json.dumps(sorted(syms)))
        except Exception:
            pass
        print(f"[mis] MIS-allowed list loaded: {len(syms)} symbols", flush=True)
    except Exception as e:
        print(f"[mis] MIS list fetch fail: {repr(e)[:120]} (filter skip)", flush=True)
        _mis_set = _mis_set or set()


def is_mis_allowed(symbol: str) -> bool:
    syms = _load()
    if not syms:
        return True  # fetch fail hua to sab allow (safe fallback)
    return (symbol or "").strip().upper() in syms


def get_all_mis_symbols() -> list:
    """Return all Zerodha MIS allowed trading symbols sorted."""
    syms = _load()
    return sorted(list(syms))
