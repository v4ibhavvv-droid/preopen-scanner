"""Engine — NSE pre-open auction data -> Zerodha MIS scanner rows.

Covers ALL Zerodha MIS allowed symbols (1,672 stocks):
- Pre-open active stocks: live IEP, Gap %, turnover, matched qty, ladder order book.
- Inactive / no pre-open orders: cleanly listed below with '--'.
- Ranked by Gap % descending.
"""
import math

from scanner.mis_filter import get_all_mis_symbols


def _num(v):
    if v is None or v == "":
        return None
    try:
        x = float(v)
        if math.isnan(x) or math.isinf(x):
            return None
        return x
    except (TypeError, ValueError):
        return None


class Engine:
    def process(self, raw):
        """NSE raw payload -> (rows, meta) for all Zerodha MIS stocks."""
        data = raw.get("data") if isinstance(raw, dict) else None

        # 1. Index available pre-open data by symbol
        by_symbol = {}
        if data:
            for d in data:
                md = d.get("metadata") or {}
                detail = d.get("detail") or {}
                pp = detail.get("preOpenMarket") or {}

                sym_orig = md.get("symbol") or ""
                sym_key = sym_orig.strip().upper()
                if not sym_key:
                    continue

                prev = _num(md.get("previousClose"))
                iep = _num(pp.get("IEP")) or _num(pp.get("indicativeEquilibriumPrice")) or _num(md.get("iep"))
                ltp = _num(pp.get("lastPrice")) or _num(md.get("lastPrice"))
                gap = _num(pp.get("perChange")) or _num(pp.get("pChange")) or _num(md.get("pChange"))
                if gap is None and prev and iep is not None:
                    gap = round((iep - prev) / prev * 100, 2)

                matched = _num(pp.get("matchedQuantity")) or _num(md.get("finalQuantity")) or _num(pp.get("finalQuantity"))
                turnover = _num(pp.get("totalTurnover")) or _num(md.get("totalTurnover"))

                # Buy/Sell pending qty from pre-open order book
                # NSE ka preOpenMarket me totalBuyQuantity/totalSellQuantity hota hai
                # (pehle detail.orderBook use karte the jo exist nahi karta)
                buy_pend = _num(pp.get("totalBuyQuantity"))
                sell_pend = _num(pp.get("totalSellQuantity"))
                if buy_pend is None:
                    # fallback: sum of preopen level buyQty
                    preopen_levels = pp.get("preopen") or []
                    if preopen_levels:
                        s = sum(_num(lvl.get("buyQty")) or 0 for lvl in preopen_levels)
                        buy_pend = s if s > 0 else None
                if sell_pend is None:
                    preopen_levels = pp.get("preopen") or []
                    if preopen_levels:
                        s = sum(_num(lvl.get("sellQty")) or 0 for lvl in preopen_levels)
                        sell_pend = s if s > 0 else None

                by_symbol[sym_key] = {
                    "symbol": sym_orig,
                    "series": md.get("series") or "EQ",
                    "source": "NSE",
                    "prev_close": prev,
                    "iep": iep,
                    "ltp": ltp,
                    "gap_pct": gap,
                    "d_iep": _num(pp.get("Change")) or _num(pp.get("change")) or _num(md.get("change")),
                    "nse_pchange": _num(md.get("perChange30d")),
                    "matched_qty": matched,
                    "turnover_l": (turnover / 1e5) if turnover is not None else None,
                    "buy_pend": buy_pend,
                    "sell_pend": sell_pend,
                    "year_high": _num(md.get("yearHigh")),
                    "year_low": _num(md.get("yearLow")),
                    "last_update": str(pp.get("lastUpdateTime") or md.get("lastUpdateTime") or ""),
                    "url": f"https://www.nseindia.com/get-quotes/equity?symbol={sym_orig}",
                }

        # 2. Sirf wahi MIS stocks jo NSE pre-open me actually hain (inactive remove)
        all_mis = get_all_mis_symbols()
        rows = []
        for sym in all_mis:
            sym_key = sym.strip().upper()
            if sym_key in by_symbol:
                rows.append(by_symbol[sym_key])

        # 3. Sort: Gap % descending (None/NA at the end), then symbol A-Z
        rows.sort(key=lambda r: (r["gap_pct"] is None, -(r["gap_pct"] or 0), r["symbol"]))
        for i, r in enumerate(rows, 1):
            r["rank"] = i

        meta = {
            "nse_n": len(rows),
            "total": len(rows),
            "active_n": sum(1 for r in rows if r["gap_pct"] is not None),
            "timestamp": raw.get("time") or raw.get("timestamp") or "",
            "fetched_at": raw.get("time") or raw.get("timestamp") or "",
        }
        return rows, meta

    def merge(self, nse_rows, *args, **kwargs):
        """Direct return (sorted)."""
        rows = [dict(r) for r in (nse_rows or [])]
        rows.sort(key=lambda r: (r["gap_pct"] is None, -(r["gap_pct"] or 0), r["symbol"]))
        for i, r in enumerate(rows, 1):
            r["rank"] = i
        return rows
