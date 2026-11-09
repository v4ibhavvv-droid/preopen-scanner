"""Dashboard — stdlib HTTP server (dependency-free).

  GET /            -> single-page HTML (auto-refresh table)
  GET /api/board   -> JSON {meta, rows}
"""
import json
import threading

from config import POLL_INTERVAL_SEC

HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<meta name="theme-color" content="#0a0e1a">
<title>Pre-Open Gap-Up Scanner</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><rect width='24' height='24' rx='6' fill='%230ea5e9'/><path d='M7 5v14M12 9v10M17 5v10' stroke='white' stroke-width='2.4' stroke-linecap='round'/></svg>">
<style>
:root{
  --bg:#070a12;--panel:rgba(13,17,28,.72);--txt:#e7edf7;--mut:#8b95a8;
  --grn:#34d399;--grn-soft:#4ade80;--red:#fb7185;--gold:#fbbf24;
  --acc:#38bdf8;--vio:#a78bfa;--brd:rgba(255,255,255,.07);--brd2:rgba(255,255,255,.10);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
::selection{background:rgba(56,189,248,.30);color:#fff}
::-webkit-scrollbar{width:10px;height:10px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(148,163,184,.25);border-radius:8px;border:2px solid transparent;background-clip:content-box}
::-webkit-scrollbar-thumb:hover{background:rgba(148,163,184,.45);background-clip:content-box;border:2px solid transparent}
html{scrollbar-width:thin;scrollbar-color:rgba(148,163,184,.3) transparent}
body{margin:0;color:var(--txt);font:13.5px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif;background:var(--bg);opacity:0;transition:opacity .3s ease}
body.ready{opacity:1}
body::before{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;background:
  radial-gradient(1100px 520px at 85% -10%, rgba(34,211,238,.09), transparent 60%),
  radial-gradient(900px 480px at -10% 110%, rgba(167,139,250,.08), transparent 60%),
  radial-gradient(700px 400px at 50% 35%, rgba(56,189,248,.04), transparent 65%),
  linear-gradient(180deg,#0a0e1a 0%,#070a12 100%)}

/* ---------------- header ---------------- */
header{position:sticky;top:0;z-index:50;background:var(--panel);backdrop-filter:blur(18px) saturate(1.5);-webkit-backdrop-filter:blur(18px) saturate(1.5);border-bottom:1px solid var(--brd);padding:13px 22px 12px;box-shadow:0 10px 34px rgba(0,0,0,.35);animation:hdrIn .5s ease both}
header::after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:2px;pointer-events:none;opacity:.55;filter:blur(.5px);background:linear-gradient(90deg,transparent 4%,rgba(56,189,248,.50) 30%,rgba(167,139,250,.55) 55%,transparent 96%);background-size:220% 100%;background-position:200% 0;animation:hdrBeam 7s ease-in-out infinite alternate}
@keyframes hdrBeam{0%{background-position:200% 0;opacity:.22}50%{opacity:.75}100%{background-position:-120% 0;opacity:.22}}
header::after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:1.5px;background:linear-gradient(90deg,transparent 0%,rgba(56,189,248,.55) 30%,rgba(167,139,250,.55) 70%,transparent 100%);background-size:220% 100%;background-position:-120% 0;opacity:.5;animation:hdrLine 6.5s linear infinite}
@keyframes hdrLine{0%{background-position:-120% 0}100%{background-position:120% 0}}
@keyframes hdrIn{from{opacity:0;transform:translateY(-8px)}}
.top{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:11px}
.logo{width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,#0ea5e9,#8b5cf6);display:inline-flex;align-items:center;justify-content:center;color:#fff;box-shadow:0 4px 18px rgba(14,165,233,.40),inset 0 1px 0 rgba(255,255,255,.30);flex:none}
.logo svg{width:18px;height:18px}
h1{margin:0;font-size:20px;font-weight:800;letter-spacing:.5px;display:flex;align-items:center;gap:7px;white-space:nowrap}
h1 .grad{position:relative;background:linear-gradient(120deg, rgba(255,255,255,0) 30%, rgba(255,255,255,.85) 46%, rgba(255,255,255,.85) 54%, rgba(255,255,255,0) 70%) no-repeat, linear-gradient(92deg,#38bdf8 15%,#a78bfa 85%);-webkit-background-clip:text;background-clip:text;color:transparent;font-size:21px;background-size:220% 100%,100% 100%;background-position:-160% 0,0 0;animation:spSheen 3.4s ease-in-out 1s infinite}
h1 .sep{color:#3b4457;font-weight:300;font-size:17px}
h1 .mk{font-weight:800;letter-spacing:2.5px;font-size:18.5px;color:var(--txt)}
.live{position:relative;display:inline-flex;align-items:center;gap:7px;background:rgba(52,211,153,.10);border:1px solid rgba(52,211,153,.35);color:#34d399;font-size:9.5px;font-weight:800;letter-spacing:1.6px;border-radius:999px;padding:3.5px 11px 3.5px 9px;vertical-align:middle}
.ping{width:7px;height:7px;border-radius:50%;background:var(--grn);position:relative;flex:none}
.ping::after{content:"";position:absolute;inset:0;border-radius:50%;border:1.6px solid #34d399;animation:ping 1.7s cubic-bezier(0,0,.2,1) infinite}
@keyframes ping{0%{transform:scale(1);opacity:.9}75%,100%{transform:scale(2.6);opacity:0}}
.right{display:flex;align-items:center;gap:9px;flex-wrap:wrap}
.clockpill{display:inline-flex;align-items:center;gap:9px;background:rgba(255,255,255,.05);border:1px solid var(--brd);border-radius:999px;padding:4px 14px 4px 11px;transition:border-color .2s;box-shadow:0 0 26px rgba(56,189,248,.10),inset 0 1px 0 rgba(255,255,255,.06)}
.clockpill:hover{border-color:var(--brd2)}
.cic{width:13px;height:13px;color:var(--mut);flex:none}
#fetched{font-size:18px;font-weight:800;letter-spacing:.4px;color:var(--txt);font-variant-numeric:tabular-nums;white-space:nowrap}
.dot{width:9px;height:9px;border-radius:50%;background:var(--grn);display:inline-block;flex:none;box-shadow:0 0 10px rgba(52,211,153,.55);transition:background .3s,box-shadow .3s;animation:breathe 2.6s ease-in-out infinite}
@keyframes breathe{50%{box-shadow:0 0 4px rgba(52,211,153,.25)}}
.dot.stale{background:var(--red);box-shadow:0 0 12px rgba(251,113,133,.60);animation:none}
#mode{display:none;font-size:10.5px;font-weight:700;letter-spacing:.6px;color:var(--gold);background:rgba(251,191,36,.10);border:1px solid rgba(251,191,36,.35);border-radius:8px;padding:4px 10px}
#mode.on{display:inline-block}
#err{display:none;font-size:10.5px;font-weight:700;letter-spacing:.5px;color:#ffe4e6;background:linear-gradient(135deg,#e11d48,#be123c);border:1px solid rgba(255,255,255,.14);border-radius:8px;padding:4px 10px;white-space:nowrap;animation:blink 2.1s ease-in-out infinite}
#err.on{display:inline-block}
@keyframes blink{50%{opacity:.72}}

/* ---------------- controls ---------------- */
.controls{display:flex;align-items:center;gap:9px;margin-top:11px;flex-wrap:wrap}
.pill{display:inline-flex;align-items:center;gap:7px;background:rgba(255,255,255,.04);border:1px solid var(--brd);border-radius:10px;padding:5.5px 11px;font-size:12px;color:var(--mut);transition:border-color .2s,box-shadow .2s}
.fic{width:12px;height:12px;color:var(--mut);flex:none}
#minGap{width:56px;background:transparent;border:0;color:var(--txt);font-weight:700;font-size:13px;padding:0;font-variant-numeric:tabular-nums;outline:none}
.pill:focus-within{border-color:rgba(56,189,248,.55);box-shadow:0 0 0 3px rgba(56,189,248,.12),0 4px 14px rgba(56,189,248,.10)}
.seg{display:inline-flex;align-items:center;gap:3px;background:rgba(255,255,255,.04);border:1px solid var(--brd);border-radius:11px;padding:3px}
.sortBtn{display:inline-flex;align-items:center;gap:6px;border:0;background:transparent;color:var(--mut);border-radius:8px;padding:5.5px 13px;font-size:12px;font-weight:600;letter-spacing:.2px;cursor:pointer;transition:color .18s,background .18s,box-shadow .18s;font-family:inherit}
.sic{width:11px;height:11px;flex:none;opacity:.85}
.sortBtn:hover{color:var(--txt);background:rgba(255,255,255,.06)}
.sortBtn.active{background:linear-gradient(135deg,#0ea5e9,#8b5cf6);color:#fff;box-shadow:0 3px 14px rgba(14,165,233,.38)}

/* ---------------- table ---------------- */
main{max-width:1440px;margin:17px auto 10px;padding:0 20px}
.card{position:relative;background:linear-gradient(180deg,rgba(21,27,41,.60),rgba(14,18,29,.60));border:1px solid var(--brd);border-radius:16px;box-shadow:0 24px 70px rgba(0,0,0,.45),inset 0 1px 0 rgba(255,255,255,.045);overflow:clip;animation:cardIn .55s cubic-bezier(.2,.7,.3,1) both, cardAura 7s ease-in-out 2s infinite}
@keyframes cardAura{50%{box-shadow:0 24px 70px rgba(0,0,0,.45),0 0 100px rgba(56,189,248,.14),0 0 160px rgba(167,139,250,.10),inset 0 1px 0 rgba(255,255,255,.045)}}
.card::before{content:"";position:absolute;top:0;left:0;width:34%;height:1.6px;border-radius:999px;background:linear-gradient(90deg,transparent,#38bdf8,#a78bfa,transparent);filter:blur(.4px);transform:translateX(-120%);opacity:0;animation:cardEdge 7.5s ease-in-out 1.5s infinite;pointer-events:none}
@keyframes cardEdge{0%{transform:translateX(-120%);opacity:.85}12%{opacity:.95}48%{transform:translateX(310%);opacity:.9}60%,100%{transform:translateX(310%);opacity:0}}
@keyframes cardIn{from{opacity:0;transform:translateY(12px)}}
@media (max-width:1240px){.card{overflow-x:auto}}
table{width:100%;border-collapse:collapse;font-size:12.5px;font-variant-numeric:tabular-nums}
thead th{position:sticky;top:var(--thead-top,120px);z-index:10;background:rgba(10,14,24,.82);backdrop-filter:blur(14px) saturate(1.4);-webkit-backdrop-filter:blur(14px) saturate(1.4);color:#7d8798;font-size:10px;font-weight:700;letter-spacing:1.3px;text-transform:uppercase;text-align:left;padding:9px 12px;border-bottom:1px solid var(--brd2);white-space:nowrap}
thead th.num{text-align:right}
tbody td{padding:7px 12px;border-bottom:1px solid rgba(255,255,255,.045);white-space:nowrap;color:var(--txt);transition:background .18s,box-shadow .18s}
tbody td.num{text-align:right}
tbody tr:hover td{background:rgba(56,189,248,.055)}
tbody tr:hover td:first-child{box-shadow:inset 3px 0 0 var(--acc)}
tbody tr.r1 td{background:linear-gradient(90deg,rgba(251,191,36,.075),rgba(251,191,36,.015) 55%,transparent)}
tbody tr.r1:hover td{background:linear-gradient(90deg,rgba(251,191,36,.11),rgba(251,191,36,.03) 55%,rgba(56,189,248,.05))}
tbody tr:last-child td{border-bottom:0}

.rank .rk{display:inline-flex;align-items:center;justify-content:center;min-width:25px;height:25px;border-radius:8px;font-weight:700;font-size:11.5px;color:var(--mut);background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.05);transition:transform .18s}
tbody tr:hover .rk{transform:scale(1.08)}
.rk.m1{background:linear-gradient(135deg,#fcd34d,#f59e0b);color:#241a02;border:0;box-shadow:0 3px 12px rgba(245,158,11,.35)}
.rk.m2{background:linear-gradient(135deg,#e2e8f0,#94a3b8);color:#101522;border:0;box-shadow:0 3px 12px rgba(203,213,225,.28)}
.rk.m3{background:linear-gradient(135deg,#e29a5a,#b46b3a);color:#1c0e03;border:0;box-shadow:0 3px 12px rgba(200,128,64,.30)}
.rk.mtop{color:var(--gold);background:rgba(251,191,36,.09);border-color:rgba(251,191,36,.28)}

.sym{color:#7dd3fc;font-weight:700;text-decoration:none;display:inline-flex;align-items:center;gap:4px;transition:color .15s,text-shadow .15s}
.sym::after{content:"\\2197";font-size:10px;color:var(--acc);opacity:0;transform:translate(-3px,3px);transition:opacity .15s,transform .15s}
.sym:hover{color:#c2ecff;text-shadow:0 0 14px rgba(56,189,248,.55)}
.sym:hover::after{opacity:1;transform:translate(0,0)}
.sme{font-size:9px;font-weight:700;letter-spacing:.5px;background:rgba(255,255,255,.06);border:1px solid var(--brd);border-radius:5px;padding:1.5px 5px;margin-left:6px;color:var(--mut);vertical-align:1.5px}

.chip{display:inline-flex;align-items:center;gap:5px;padding:2.5px 10px;border-radius:999px;font-weight:700;font-size:11.5px;letter-spacing:.2px}
.chip i{font-style:normal;font-size:8.5px;opacity:.9}
.chip.c-hi{color:#4ade80;background:rgba(74,222,128,.12);box-shadow:inset 0 0 0 1px rgba(74,222,128,.30)}
.chip.c-md{color:#86efac;background:rgba(134,239,172,.09);box-shadow:inset 0 0 0 1px rgba(134,239,172,.18)}
.chip.c-dn{color:#fda4af;background:rgba(253,164,175,.11);box-shadow:inset 0 0 0 1px rgba(253,164,175,.26)}
.chip.c-flat{color:#aab3c5;background:rgba(255,255,255,.05);box-shadow:inset 0 0 0 1px rgba(255,255,255,.07)}
.tup{color:var(--grn-soft);font-weight:600}
.tdn{color:var(--red);font-weight:600}
.bn{color:#94a0b4}
.au{font-size:11.5px;color:var(--mut);font-variant-numeric:tabular-nums}

tbody tr.anim{animation:rise .34s cubic-bezier(.2,.7,.3,1) both}
@keyframes rise{from{opacity:0;transform:translateY(7px)}}
.skl td{padding:11px 12px;background:transparent!important;box-shadow:none!important}
.skl i{display:block;height:10px;border-radius:6px;background:linear-gradient(90deg,rgba(255,255,255,.05) 25%,rgba(255,255,255,.12) 37%,rgba(255,255,255,.05) 63%);background-size:400% 100%;animation:shk 1.35s ease-in-out infinite}
.skl td:first-child i{color:transparent}
@keyframes shk{0%{background-position:100% 0}100%{background-position:-100% 0}}
.emptyrow td{padding:0!important;background:transparent!important;box-shadow:none!important}
.empty{display:flex;flex-direction:column;align-items:center;gap:9px;padding:52px 20px;color:var(--mut)}
.empty svg{width:34px;height:34px;opacity:.4}
.empty div:first-of-type+.esub{font-size:11.5px;color:#5d6678}
.empty div{font-weight:700;letter-spacing:1px;font-size:12px}

footer{position:relative;max-width:1440px;margin:4px auto 16px;padding:0 22px;text-align:center;color:#576070;font-size:11px;letter-spacing:.25px}
footer::before{content:"";position:absolute;top:-8px;left:18%;right:18%;height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,.13) 35%,rgba(125,211,252,.18) 50%,rgba(255,255,255,.13) 65%,transparent)}
footer b{color:#7d8798;font-weight:600}

/* ---------------- splash (launch animation — full-screen) ---------------- */
#splash{position:fixed;inset:0;z-index:300;display:flex;align-items:center;justify-content:center;overflow:hidden;background:
  radial-gradient(1100px 560px at 50% 28%, rgba(14,165,233,.14), transparent 62%),
  radial-gradient(900px 480px at 58% 78%, rgba(167,139,250,.11), transparent 62%),
  linear-gradient(180deg,#0a0e1a,#06080f)}
#splash::before{content:"";position:absolute;inset:-40%;pointer-events:none;background:conic-gradient(from 0deg at 50% 42%, transparent 0deg, rgba(56,189,248,.07) 40deg, transparent 95deg, rgba(167,139,250,.06) 150deg, transparent 210deg);animation:spSpin 11s linear infinite}
@keyframes spSpin{to{transform:rotate(360deg)}}
#splash::after{content:"";position:absolute;inset:0;pointer-events:none;background:radial-gradient(closest-side at 50% 46%, transparent 55%, rgba(3,5,10,.55) 100%)}
.sp-scale{transform:scale(1);will-change:transform}
.sp-box{position:relative;display:flex;flex-direction:column;align-items:center;gap:15px;animation:spIn .6s cubic-bezier(.2,.7,.3,1) both, spZoom 2.5s ease-in-out infinite}
@keyframes spIn{from{opacity:0;transform:scale(.93) translateY(12px)}}
@keyframes spZoom{0%{scale:.96}50%{scale:1.09}100%{scale:.96}}
.sp-logo{width:76px;height:76px;border-radius:22px;background:linear-gradient(135deg,#0ea5e9,#8b5cf6);display:flex;align-items:center;justify-content:center;color:#fff;box-shadow:0 14px 60px rgba(14,165,233,.5),0 0 120px rgba(139,92,246,.25),inset 0 1px 0 rgba(255,255,255,.35);animation:spPulse 2.1s ease-in-out infinite;position:relative}
.sp-logo svg{width:38px;height:38px}
.sp-logo::before,.sp-logo::after{content:"";position:absolute;inset:-14px;border-radius:26px;border:1.5px solid rgba(56,189,248,.35);animation:spRing 2.8s cubic-bezier(0,0,.2,1) infinite}
.sp-logo::after{animation-delay:1.4s;border-color:rgba(167,139,250,.30)}
@keyframes spRing{0%{transform:scale(.72);opacity:.9}75%,100%{transform:scale(2.05);opacity:0}}
@keyframes spPulse{50%{box-shadow:0 14px 76px rgba(139,92,246,.60),0 0 130px rgba(56,189,248,.30),inset 0 1px 0 rgba(255,255,255,.35)}}
.sp-chart{position:relative;width:320px;height:130px;margin-top:2px}
.sp-line{position:absolute;inset:0;width:100%;height:100%;overflow:visible}
.sp-line path{stroke-dasharray:420;stroke-dashoffset:420;animation:spDraw 1.3s cubic-bezier(.4,0,.2,1) 1.0s forwards;filter:drop-shadow(0 0 10px rgba(56,189,248,.60))}
@keyframes spDraw{to{stroke-dashoffset:0}}
.sp-candles{position:absolute;left:18px;bottom:0;display:flex;gap:22px;align-items:flex-end;height:100px}
.cnd{width:30px;position:relative;height:100%;display:flex;align-items:flex-end;justify-content:center}
.cnd::before{content:"";position:absolute;bottom:calc(var(--h)/2);left:50%;width:3px;transform:translateX(-50%);height:calc(var(--h) + 30px);background:linear-gradient(180deg,rgba(255,255,255,.42),rgba(255,255,255,.12));border-radius:3px;opacity:0;animation:spCnd .68s cubic-bezier(.2,.7,.3,1) var(--d) forwards}
.cnd i{display:block;width:20px;height:0;border-radius:4px;transform-origin:bottom;animation:spCnd .68s cubic-bezier(.2,.7,.3,1) var(--d) forwards}
.c-grn i{background:linear-gradient(180deg,#5df08f,#16a34a);box-shadow:0 0 26px rgba(74,222,128,.50)}
.c-red i{background:linear-gradient(180deg,#fb7185,#e11d48);box-shadow:0 0 26px rgba(251,113,133,.50)}
@keyframes spCnd{from{height:0;opacity:0}30%{opacity:1}to{height:var(--h);opacity:1}}
.sp-title{position:relative;display:flex;align-items:center;gap:14px;font-size:38px;font-weight:800;opacity:0;animation:spUp .55s ease .45s both;filter:drop-shadow(0 8px 26px rgba(14,165,233,.28)) drop-shadow(0 0 40px rgba(139,92,246,.18))}
.sp-title::before{content:"";position:absolute;inset:-16% -34%;z-index:-1;border-radius:50%;background:radial-gradient(closest-side, rgba(56,189,248,.13), rgba(167,139,250,.07) 55%, transparent 72%);transform:scale(.55);opacity:0;animation:spWave 2.8s ease-out 1s infinite}
@keyframes spWave{0%{transform:scale(.55);opacity:.6}70%{opacity:.14}100%{transform:scale(1.5);opacity:0}}
.sp-title{animation:spUp .55s ease .45s both, spBloom 3s ease-in-out 1.4s infinite}
@keyframes spBloom{0%,100%{filter:drop-shadow(0 8px 26px rgba(14,165,233,.28)) drop-shadow(0 0 40px rgba(139,92,246,.18))}50%{filter:drop-shadow(0 8px 44px rgba(14,165,233,.50)) drop-shadow(0 0 66px rgba(167,139,250,.35))}}
.sp-grad{position:relative;background:linear-gradient(120deg, rgba(255,255,255,0) 30%, rgba(255,255,255,.92) 46%, rgba(255,255,255,.92) 54%, rgba(255,255,255,0) 70%) no-repeat, linear-gradient(92deg,#38bdf8 15%,#a78bfa 85%);-webkit-background-clip:text;background-clip:text;color:transparent;background-size:220% 100%,100% 100%;background-position:-160% 0,0 0;animation:spSheen 2.7s ease-in-out 1.15s infinite}
@keyframes spSheen{0%,55%{background-position:-160% 0,0 0}100%{background-position:160% 0,0 0}}
.sp-sep{color:#3b4457;font-weight:300}
.sp-mk{letter-spacing:6px;color:#eaf1fb;text-shadow:0 0 26px rgba(125,211,252,.25)}
@keyframes spUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
.sp-bar{width:min(460px,52vw);height:4px;border-radius:999px;background:rgba(255,255,255,.08);overflow:hidden;margin-top:4px;box-shadow:0 0 18px rgba(56,189,248,.15)}
.sp-bar i{display:block;height:100%;width:100%;border-radius:inherit;background:linear-gradient(90deg,#38bdf8,#a78bfa);transform-origin:left;transform:scaleX(0);animation:spFill 6.15s linear .1s forwards;box-shadow:0 0 12px rgba(56,189,248,.60)}
@keyframes spFill{to{transform:scaleX(1)}}

/* ---------------- animated background glows (ambient aurora) ---------------- */
.bgfx{position:fixed;inset:0;z-index:-2;pointer-events:none;overflow:hidden}
.bgfx i{position:absolute;border-radius:50%;will-change:transform}
.bgfx .b1{width:840px;height:640px;top:-190px;right:-170px;background:radial-gradient(closest-side, rgba(34,211,238,.30), rgba(34,211,238,.11) 45%, transparent 72%);animation:bg1 21s ease-in-out infinite alternate}
.bgfx .b2{width:780px;height:580px;bottom:-210px;left:-190px;background:radial-gradient(closest-side, rgba(167,139,250,.30), rgba(167,139,250,.11) 45%, transparent 72%);animation:bg2 27s ease-in-out infinite alternate}
.bgfx .b3{width:660px;height:500px;top:36%;left:32%;background:radial-gradient(closest-side, rgba(56,189,248,.20), transparent 74%);animation:bg3 17s ease-in-out infinite alternate}
@keyframes bg1{50%{transform:translate3d(-130px,95px,0) scale(1.15)}100%{transform:translate3d(-45px,150px,0) scale(1.06)}}
@keyframes bg2{50%{transform:translate3d(145px,-115px,0) scale(1.18)}100%{transform:translate3d(55px,-60px,0) scale(1.1)}}
@keyframes bg3{50%{transform:translate3d(95px,-75px,0) scale(1.22)}100%{transform:translate3d(-75px,45px,0) scale(1.05)}}
.bgfx .b4{width:56vw;height:150vh;top:-20%;left:16%;transform-origin:50% 100%;mix-blend-mode:screen;background:conic-gradient(from 208deg at 50% 125%, transparent 0%, rgba(94,234,212,.40) 16%, rgba(56,189,248,.27) 28%, rgba(167,139,250,.19) 40%, transparent 54%);-webkit-mask-image:linear-gradient(180deg,#000 0%,rgba(0,0,0,.48) 52%,transparent 86%);mask-image:linear-gradient(180deg,#000 0%,rgba(0,0,0,.48) 52%,transparent 86%);filter:blur(42px);opacity:.72;will-change:transform,opacity;animation:bg4 14s ease-in-out infinite alternate, bg4Pulse 9s ease-in-out infinite alternate}
@keyframes bg4{0%{transform:translateX(-16vw) rotate(-8deg) skewX(-4deg)}100%{transform:translateX(38vw) rotate(-2deg) skewX(4deg)}}
@keyframes bg4Pulse{from{opacity:.75}to{opacity:1}}

/* ---------------- full-screen continuous premium aura ---------------- */
.bgfx .a1{inset:-25%;width:150%;height:150%;border-radius:0;mix-blend-mode:screen;
background:
 radial-gradient(46% 42% at 22% 28%, rgba(56,189,248,.30), transparent 70%),
 radial-gradient(42% 40% at 78% 24%, rgba(94,234,212,.26), transparent 70%),
 radial-gradient(50% 46% at 70% 76%, rgba(167,139,250,.30), transparent 72%),
 radial-gradient(44% 42% at 26% 78%, rgba(14,165,233,.24), transparent 72%);
filter:blur(46px);opacity:.85;will-change:transform;
animation:a1Flow 26s ease-in-out infinite alternate, a1Pulse 7s ease-in-out infinite alternate}
@keyframes a1Pulse{from{opacity:.75}to{opacity:1}}
@keyframes a1Flow{0%{transform:scale(1) rotate(0deg) translateX(0)}50%{transform:scale(1.14) rotate(4deg) translateX(2.5vw)}100%{transform:scale(1.05) rotate(-3deg) translateX(-2.5vw)}}
.bgfx .a2{inset:0;width:200%;height:100%;border-radius:0;mix-blend-mode:screen;
background:linear-gradient(105deg, transparent 28%, rgba(56,189,248,.14) 42%, rgba(167,139,250,.19) 50%, rgba(94,234,212,.14) 58%, transparent 72%);
filter:blur(28px);opacity:.9;will-change:transform;
animation:a2Sweep 11s ease-in-out infinite alternate;opacity:1
@keyframes a2Sweep{from{transform:translateX(-30%)}to{transform:translateX(-5%)}}
.bgfx .a3{position:absolute;inset:-15%;width:130%;height:130%;border-radius:50%;mix-blend-mode:screen;
background:conic-gradient(from 200deg, transparent 0%, rgba(129,140,248,.14) 20%, rgba(56,189,248,.12) 42%, rgba(167,139,250,.15) 62%, rgba(94,234,212,.11) 82%, transparent 100%);
filter:blur(60px);will-change:transform,opacity;
animation:a3Spin 26s linear infinite, a3Breath 8s ease-in-out infinite alternate}
@keyframes a3Spin{to{rotate:360deg}}
@keyframes a3Breath{from{opacity:.6}to{opacity:1}}

@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>
</head>
<body>
<div class="bgfx" aria-hidden="true"><i class="a1"></i><i class="a2"></i><i class="a3"></i><i class="b1"></i><i class="b2"></i><i class="b3"></i><i class="b4"></i></div>
<div id="splash" aria-hidden="true">
  <div class="sp-scale">
    <div class="sp-box">
      <div class="sp-logo"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round"><path d="M6 5v5M6 14v5M12 8v6M12 17v2M18 4v9M18 16v4"/></svg></div>
      <div class="sp-chart">
        <svg class="sp-line" viewBox="0 0 320 130" fill="none" aria-hidden="true">
          <path d="M6 112 L40 92 L76 100 L112 60 L150 70 L196 34 L238 44 L312 10" stroke="url(#sgrad)" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/>
          <defs><linearGradient id="sgrad" x1="0" y1="0" x2="320" y2="0" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#38bdf8"/><stop offset="1" stop-color="#a78bfa"/></linearGradient></defs>
        </svg>
        <div class="sp-candles" aria-hidden="true">
          <span class="cnd c-red" style="--d:0s;--h:30px"><i></i></span>
          <span class="cnd c-grn" style="--d:.22s;--h:50px"><i></i></span>
          <span class="cnd c-grn" style="--d:.44s;--h:42px"><i></i></span>
          <span class="cnd c-red" style="--d:.66s;--h:26px"><i></i></span>
          <span class="cnd c-grn" style="--d:.88s;--h:62px"><i></i></span>
          <span class="cnd c-red" style="--d:1.10s;--h:22px"><i></i></span>
          <span class="cnd c-grn" style="--d:1.32s;--h:84px"><i></i></span>
        </div>
      </div>
      <div class="sp-title"><span class="sp-grad">Pre-Open</span><span class="sp-sep">&#9475;</span><span class="sp-mk">MARKET</span></div>
      <div class="sp-bar"><i></i></div>
    </div>
  </div>
</div>
<header id="hdr">
  <div class="top">
    <div class="brand">
      <span class="logo" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round"><path d="M6 5v5M6 14v5M12 8v6M12 8h0M12 17v2M18 4v9M18 16v4"/></svg></span>
      <h1><span class="grad">Pre-Open</span><span class="sep">&nbsp;&#9475;&nbsp;</span><span class="mk">MARKET</span></h1>
      <span class="live"><span class="ping"></span>LIVE</span>
    </div>
    <div class="right">
      <span id="mode"></span>
      <span id="err"></span>
      <span class="clockpill"><span class="dot" id="dot"></span><svg class="cic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg><b id="fetched">--</b></span>
    </div>
  </div>
  <div class="controls">
    <label class="pill"><svg class="fic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16l-6 8v6l-4-2v-4z"/></svg>Min |Gap|%&nbsp;<input id="minGap" type="number" value="0" step="0.5"></label>
    <span class="seg" role="group" aria-label="sort">
      <button id="sortDesc" class="sortBtn active"><svg class="sic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>Gap % desc</button>
      <button id="sortAsc" class="sortBtn"><svg class="sic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 15l6-6 6 6"/></svg>Gap % inc</button>
    </span>
  </div>
</header>
<main><div class="card">
<table><thead><tr>
<th>#</th><th>Symbol</th><th class="num">IEP</th><th class="num">Gap %</th><th class="num">Prev Close</th><th class="num">Buy Pend</th><th class="num">Sell Pend</th><th class="num">Matched Qty</th><th class="num">Turnover (L)</th><th>Auction Update</th>
</tr></thead><tbody id="tb"></tbody></table>
</div></main>
<footer>Gap % = (IEP &#8722; PrevClose) &#247; PrevClose &#215; 100 &nbsp;&#183;&nbsp; <b>All Zerodha MIS intraday stocks</b> &nbsp;&#183;&nbsp; Click symbol to open Kite chart &nbsp;&#183;&nbsp; personal research tool</footer>
<script>
const $ = id => document.getElementById(id);
const inf = n => n == null ? "--" : Number(n).toLocaleString("en-IN");
const f2 = n => n == null ? "--" : Number(n).toFixed(2);

let last = null, currentSort = "gap", first = true, lastTs = null;

/* timestamp "03-Nov-2026 09:00:54" / "03 Nov 2026, 9:00:54 am" -> epoch (no regex, no escapes) */
function parseTs(ts){
  if(!ts) return null;
  const M = {jan:1,feb:2,mar:3,apr:4,may:5,jun:6,jul:7,aug:8,sep:9,oct:10,nov:11,dec:12};
  const p = String(ts).replace(/,/g," ").replace(/-/g," ").trim().toLowerCase().split(" ").filter(Boolean);
  let day=null, mo=null, yr=null, time=null;
  for(const w of p){
    if(!time && w.indexOf(":") > 0){ time = w; continue; }
    if(mo === null && M[w]){ mo = M[w]; continue; }
    if(yr === null && /^[0-9]{4}$/.test(w)){ yr = +w; continue; }
    if(day === null && /^[0-9]{1,2}$/.test(w)){ day = +w; continue; }
  }
  if(day != null && mo && yr && time){
    const t = time.split(":");
    return new Date(yr, mo-1, day, +t[0]||0, +t[1]||0, +t[2]||0).getTime();
  }
  return null;
}

function staleCheck(){
  if(lastTs){
    const ageMin = (Date.now() - lastTs) / 60000;
    if(ageMin > 2){
      $("err").textContent = "STALE DATA (" + Math.round(ageMin) + " min old) - NSE may be down";
      $("err").classList.add("on");
      $("dot").classList.add("stale");
      return;
    }
  }
  $("err").classList.remove("on");
  $("dot").classList.remove("stale");
}

function render(d){
  last = d;
  const m = d.meta || {}, rows = d.rows || [];
  const minGap = Math.abs(parseFloat($("minGap").value) || 0);

  let view = rows.filter(r => Math.abs(r.gap_pct ?? 0) >= minGap);
  if(currentSort === "gap") view.sort((a,b) => (b.gap_pct ?? -1e9) - (a.gap_pct ?? -1e9));
  else view.sort((a,b) => (a.gap_pct ?? 1e9) - (b.gap_pct ?? 1e9));

  if(!view.length){
    $("tb").innerHTML = `<tr class="emptyrow"><td colspan="10"><div class="empty">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16l-6 8v6l-4-2v-4z"/></svg>
      <div>FILTER PE KOI STOCK NAHI MILA</div><div class="esub">Min |Gap|% kam karo ya 0 kar do</div>
    </div></td></tr>`;
  } else {
    $("tb").innerHTML = view.map((r,i) => {
      const badge = (r.series && r.series !== "EQ") ? `<span class="sme">${r.series}</span>` : "";
      const rp = r.rank <= 3 ? `rk m${r.rank}` : (r.rank <= 5 && currentSort === "gap") ? "rk mtop" : "rk";
      const rowc = (currentSort === "gap" && r.rank <= 5) ? " r1" : "";
      const anim = first ? " anim" : "";
      const del = first ? ` style="animation-delay:${Math.min(i*12,360)}ms"` : "";
      const gv = r.gap_pct;
      const cc = gv >= 8 ? "c-hi" : gv >= 3 ? "c-md" : gv <= -3 ? "c-dn" : "c-flat";
      const tri = gv > 0 ? "&#9650;" : gv < 0 ? "&#9660;" : "";
      const gt = gv == null ? "--" : (gv > 0 ? "+" : "") + f2(gv) + "%";
      const num = (v,c) => v == null
        ? `<td class="num"><span class="bn">--</span></td>`
        : v > 0 ? `<td class="num"><span class="${c}">${c==="tup"?"&#9650;":"&#9660;"}&thinsp;${inf(v)}</span></td>`
        : `<td class="num"><span class="bn">${inf(v)}</span></td>`;
      return `<tr class="${rowc}${anim}"${del}>
<td><span class="${rp}">${r.rank}</span></td>
<td><a class="sym" href="${r.url}" target="_blank" rel="noopener">${r.symbol}</a>${badge}</td>
<td class="num">${f2(r.iep)}</td>
<td class="num">${gv == null ? `<span class="bn">--</span>` : `<span class="chip ${cc}">${tri?`<i>${tri}</i>`:""}${gt}</span>`}</td>
<td class="num">${f2(r.prev_close)}</td>
${num(r.buy_pend,"tup")}
${num(r.sell_pend,"tdn")}
<td class="num">${inf(r.matched_qty)}</td>
<td class="num">${inf(r.turnover_l)}</td>
<td class="au">${r.last_update || "--"}</td>
</tr>`;
    }).join("");
  }

  lastTs = parseTs(m.timestamp) || parseTs(m.fetched_at);
  staleCheck();

  $("mode").textContent = m.source === "dev-fixture" ? "DEV MODE (fixture)" : "";
  $("mode").classList.toggle("on", m.source === "dev-fixture");
  first = false;
}

/* skeleton shimmer — jab tak pehla poll nahi aata */
(function(){
  const w = [26,104,66,84,84,96,96,104,104,92];
  $("tb").innerHTML = Array.from({length:12}, () =>
    `<tr class="skl">${w.map(x => `<td><i style="width:${x}px"></i></td>`).join("")}</tr>`).join("");
})();

async function tick(){
  try{
    const r = await fetch("/api/board");
    render(await r.json());
  }catch(e){
    $("dot").classList.add("stale");
  }
}
tick();
setInterval(tick, __REFRESH__);

/* live IST clock (AM/PM) + har second staleness re-check */
(function(){
  function updateClock(){
    const now = new Date();
    const opts = {timeZone:"Asia/Kolkata", day:"2-digit", month:"short", year:"numeric", hour:"numeric", minute:"2-digit", second:"2-digit", hour12:true};
    $("fetched").textContent = now.toLocaleString("en-IN", opts);
    staleCheck();
  }
  updateClock();
  setInterval(updateClock, 1000);
})();

/* sticky thead offset = asli header ki height */
function padThead(){
  const h = document.getElementById("hdr");
  if(!h) return;
  document.documentElement.style.setProperty("--thead-top", (h.offsetHeight - 0.5) + "px");
}
padThead();
window.addEventListener("resize", padThead);
window.addEventListener("load", padThead);

["minGap"].forEach(id => {
  $(id).addEventListener("input", () => last && render(last));
  $(id).addEventListener("change", () => last && render(last));
});
function setSort(mode){
  currentSort = mode;
  $("sortDesc").classList.toggle("active", currentSort === "gap");
  $("sortAsc").classList.toggle("active", currentSort !== "gap");
  last && render(last);
}
$("sortDesc").addEventListener("click", () => setSort("gap"));
$("sortAsc").addEventListener("click", () => setSort("gapasc"));

window.addEventListener("load", () => document.body.classList.add("ready"));
requestAnimationFrame(() => document.body.classList.add("ready"));

/* splash — 3.5s market intro (har load/refresh pe chalega, phir khud gayab) */
(function(){
  const sp = document.getElementById("splash");
  if(!sp) return;
  const sc = sp.querySelector(".sp-scale");
  function fit(){
    if(!sc) return;
    const sc2 = Math.max(1, Math.min(window.innerWidth/760, window.innerHeight/620, 2.6));
    sc.style.transform = "scale(" + sc2 + ")";
  }
  fit();
  window.addEventListener("resize", fit);
  const rm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  setTimeout(() => sp.classList.add("gone"), rm ? 250 : 6450);
  setTimeout(() => sp.remove(), rm ? 800 : 8200);
})();
</script>
</body>
</html>"""


class Board:
    """Poller <-> dashboard share state (thread-safe)."""

    def __init__(self):
        self._lock = threading.Lock()
        self._snap = None
        self.poll_count = 0

    def publish(self, rows, meta, source="live"):
        with self._lock:
            self.poll_count += 1
            meta = {**meta, "source": source, "poll_count": self.poll_count}
            self._snap = {"meta": meta, "rows": rows}

    def snapshot_json(self) -> bytes:
        with self._lock:
            if self._snap is None:
                return json.dumps({"meta": {"total": 0}, "rows": []}).encode()
            return json.dumps(self._snap, separators=(",", ":")).encode()


def serve(board, host="127.0.0.1", port=8787, get_state=None):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    import time as _time

    page = HTML.replace("__REFRESH__", str(int(POLL_INTERVAL_SEC * 1000)))

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            try:
                if self.path.startswith("/health"):
                    state = get_state() if get_state else {}
                    body = json.dumps({
                        "status": "ok",
                        "poller_alive": state.get("alive", False),
                        "last_poll_age_sec": round(_time.time() - state.get("last_success_ts", 0), 1),
                        "total_polls": state.get("total_polls", 0),
                        "consecutive_errors": state.get("consecutive_errors", 0),
                        "total_errors": state.get("total_errors", 0),
                        "last_error": state.get("last_error", ""),
                    }).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                elif self.path.startswith("/api/board"):
                    body = board.snapshot_json()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    body = page.encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass  # client ne tab band/refresh kar di — shant rahe
            except Exception as e:
                print("dashboard http error:", repr(e)[:120], flush=True)

        def log_message(self, *args):
            pass

    return ThreadingHTTPServer((host, port), Handler)
