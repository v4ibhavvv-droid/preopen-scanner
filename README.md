# 🎯 Pre-Open Gap-Up Scanner (phase 1)

NSE ke **poore pre-open session** (9:00–9:15) ko monitor karta hai, har stock ka
**gap-up %** nikaal ke ranked live table me dikhata hai. **Bina broker, 100% free.**

Aapka use-case: bade gap-up stocks short-selling ke liye pehle se dikhna.

## Setup (ek baar)

```bash
cd preopen-scanner
python3 -m venv .venv
source .venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

## Run

```bash
python run.py          # LIVE — market 9:00–9:15 me table live update hoga
python run.py --dev    # aaj snapshot (fixture) se test — network nahi lagta
python run.py --once   # ek baar top-10 print karke band
```

Browser me khologa: **http://127.0.0.1:8787**

## Dashboard features

- Ranked live table (gap % desc) — NSE pre-open auction data
- **Single click on any symbol → opens that stock's chart on Zerodha Kite** (in new tab)
- Min gap %, min matched qty, symbol search, sort (gap/qty/symbol)
- Sticky header, color-coded gappers (green/red)

| Column | Matlab |
|---|---|
| Prev Close | 2 din ki close price |
| **IEP** | Indicative Equilibrium Price (pre-open auction ka "opening price") |
| **Gap %** | IEP vs prev close (ye aapka ranking metric hai) |
| Δ IEP | Pichhe poll ke muqable IEP kitna badla (auction me momentum — ▲ badhe, ▼ gire) |
| Matched Qty | IEP par jo equiti matched hui (finalQuantity) — real interest check |
| Buy Pend / Sell Pend | Auction order book me pending buy/sell qty (rebalance risk ka hint) |
| Turnover (L) | Pre-open traded turnover (lakh ₹) |
| Auction Update | NSE ke paas ye stock ka aakhri auction timestamp |

## Kahan se data?

- `https://www.nseindia.com/api/market-data-pre-open?key=ALL` — official,
  ek request me ~2,200+ symbols ka auction data (order book samet).
- `curl_cffi` (Chrome TLS impersonation) se fetch — Akamai block safe.
- 9:15 ke baad poll karte rehna chalega — lekin data wahi morning
  9:15 ka final snapshot rahega, rule data `data/scan_YYYYMMDD.jsonl` me.

## Project stages

1. **Phase 1 ✅ — pre-open scanner + live dashboard (broker-free, NSE only)** — you are here

Personal research tool. Market data aapki hi sampling hai, rate gentle rakha gaya hai.
