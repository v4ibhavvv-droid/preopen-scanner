"""Zerodha Kite chart links for Zerodha MIS symbols.

Kite ka chart URL instrument_token mangta hai:
  https://kite.zerodha.com/markets/chart/web/ciq/{EXCHANGE}/{SYMBOL}/{TOKEN}

Token hum public instruments list (https://api.kite.trade/instruments) se
laate hain, cache karte hain (1 din). Supports NSE & BSE symbols, plus
series suffixes (-BE, -SM, etc.). Fallback: zerodha public stock page.
"""
import csv
import io
import json
import threading
import time
import urllib.request

from config import DATA_DIR

INSTRUMENTS_URL = "https://api.kite.trade/instruments"
CACHE_PATH = DATA_DIR / "kite_instruments.json"
CACHE_MAX_AGE = 86400  # 1 day

_lock = threading.Lock()
_tokens = None


def _load() -> dict:
    global _tokens
    with _lock:
        if _tokens is not None:
            return _tokens
        # try fresh cache
        if CACHE_PATH.exists() and (time.time() - CACHE_PATH.stat().st_mtime) < CACHE_MAX_AGE:
            try:
                _tokens = json.loads(CACHE_PATH.read_text())
                return _tokens
            except Exception:
                _tokens = None
        # fetch (sync, with timeout)
        _fetch_locked()
        return _tokens or {}


def _fetch_locked():
    global _tokens
    try:
        with urllib.request.urlopen(INSTRUMENTS_URL, timeout=25) as r:
            raw = r.read().decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(raw))
        toks = {}
        for row in reader:
            if row.get("instrument_type") not in ("EQ", ""):
                continue
            ts = (row.get("tradingsymbol") or "").strip().upper()
            tok = (row.get("instrument_token") or "").strip()
            ex = (row.get("exchange") or "NSE").strip().upper()
            if not ts or not tok:
                continue
            # Prefer NSE if already present from BSE
            if ts not in toks or ex == "NSE":
                toks[ts] = {"token": tok, "exchange": ex}
        _tokens = toks
        try:
            CACHE_PATH.write_text(json.dumps(toks))
        except Exception:
            pass
        print(f"[kite] instruments loaded: {len(toks)} equity tokens", flush=True)
    except Exception as e:
        print(f"[kite] instruments fetch fail: {repr(e)[:120]} (fallback links use honge)", flush=True)
        _tokens = _tokens or {}


def _parse_info(info) -> tuple[str, str] | None:
    if not info:
        return None
    if isinstance(info, dict):
        tok = str(info.get("token") or "")
        ex = str(info.get("exchange") or "NSE")
        return (tok, ex) if tok else None
    s = str(info).strip()
    return (s, "NSE") if s else None


def token_for(symbol: str, series: str = "EQ") -> tuple[str, str] | None:
    """Returns (token, exchange) or None."""
    toks = _load()
    s = (symbol or "").strip().upper()
    if not s:
        return None

    # direct check
    if s in toks:
        return _parse_info(toks[s])

    # series suffix check
    if series and series not in ("EQ", "--", ""):
        key = f"{s}-{series}"
        if key in toks:
            return _parse_info(toks[key])

    # prefix match (e.g. 3IINFOLTD-BE)
    prefix = s + "-"
    for k, v in toks.items():
        if k.startswith(prefix):
            return _parse_info(v)

    return None


def chart_url(symbol: str, series: str = "EQ") -> str:
    res = token_for(symbol, series)
    if res:
        tok, ex = res
        return f"https://kite.zerodha.com/markets/chart/web/ciq/{ex}/{symbol}/{tok}"
    # fallback: zerodha public stock page
    return f"https://zerodha.com/markets/stocks/NSE/{symbol}/"
