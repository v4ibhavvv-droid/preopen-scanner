# 🚀 ClawCloud Run — NSE Probe Deploy (Bina Credit Card, ₹0)

> **Lakshya:** Sitare ye verify karna ki NSE API cloud IPs pe chalti he bhi ya nahi.
> **Probe** (12 sec NSE hit) 24/7 chalega aur status page pe **live pass-rate** dikhega.

---

## STEP 0 — Tumhare Mac pe (2 min, ek baar)

Project GitHub pe push karo (code PUBLIC rahega — isme koi secret/API-key nahi, fully safe):

```bash
cd /Users/vaibhav/Desktop/preopen-scanner

git init
git add run.py config.py requirements.txt scanner/ deploy/ .github/
git commit -m "pre-open scanner + cloud probe"
git branch -M main

# Pehle GitHub pe naya EMPTY PUBLIC repo banao: https://github.com/new
#   Name: preopen-scanner → Create repository
git remote add origin https://github.com/<tumhara-username>/preopen-scanner.git
git push -u origin main
```

Push ke turant bad GitHub Actions khud build karke GHCR pe probe-image upload karega:

`ghcr.io/<tumhara-username>/preopen-probe:latest`

(2-4 min me GitHub **Actions** tab me green-check aa jayega ✅

---

## STEP 1 — ClawCloud Login (no credit card)

1. Browser: **https://run.claw.cloud** → **Login with GitHub** → Authorize
2. Region: **Singapore** chuno (agar Mumbai/India dikhe to India hi best)
3. Dashboard → **App Launchpad** → **Create App**

---

## STEP 2 — App Config (UI me yahi bharo)

| Field | Value |
|---|---|
| Application name | `preopen-probe` |
| Image | `ghcr.io/<tumhara-username>/preopen-probe:latest` (Public) |
| Usage | CPU `0.2` · Memory `256M` |
| Network → Container Port | `8787` |
| Network → Enable Internet Access | ✅ ON |
| Env Variables | `PORT=8787` aur `POLL_SEC=12` |
| Health Check | Path `/health` · Port `8787` |

**Deploy** → `Running` status (pehli baar image-pull me ~1 min)

Url site: Network section me **Public Address** → `https://<something>.sealosbhu.site` type ek link milega — yehi duniya-ko-share-wala URL he.

---

## STEP 3 — Pass-Rate Dekhlo (30 sec me)

- `https://<tumhara-url>/` → status page:
  - **pass-rate 90%+** → NSE cloud pe khul gaya, full scanner deploy kar sakte he 🥳
  - **30-70%** → chalta he par tricks chahiye (pricing-rate tuning, backoff) — phir bhi GREEN
  - **0%** (sab FAIL) → Akamai block confirmed, plan-B plan kar dunga
- `/health` → same data JSON format
- **Aaj 9:00-9:15 IST** pre-open window me pass-rate zaroor ghorke dekhna (asli market session)

---

## STEP 4 — 24 Ghante Baad Ka Furze

- Pass-rate 24 h ghante ka average ≥ 60% ⇒ **full scanner deploy** kar dunga (probe ki jagah asli app)
- Cost: probe chaling = ~$0.1-0.2/day → $5/month-credit me khul ke fit
- RAM/CPU jelly: chal-re app isse not-a-problem nahi hai (our code 100-90%) har-rate rakhna-safe

---

## Plan-B (agar probe 0%)

- NSE foreign-cloud block = existential-scenario (Akamai ka gusse ka data humara research agent assumption not deny)
- Options milenge: (a) **free-Indian-IP proxy hack** (risky+na-stable), (b) paid Indian VPS (not-free), (c) **Mac-only-dashboard Windows** ya (d) **app ko cache cache arch mein theek karke** deploy me itna nahi kal-hi-jurmana
- Probe SDK results ke hisaab se best path me 2-min me suggest karunga

---

*Ye deploy guide tilt hai — code files: `deploy/probe.py` aur `deploy/Dockerfile`*
