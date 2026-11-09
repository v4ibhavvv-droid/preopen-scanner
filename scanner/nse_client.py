"""NSE fetcher — Akamai-safe.

Reality check (Oct 2026): NSE ne plain `requests`/`curl` TLS fingerprint block
kar diya hai (Akamai Bot Manager). Isliye:
  1. `curl_cffi` se Chrome TLS impersonation
  2. Homepage se cookie warm-up
  3. Fail hone par fresh warm-up ke saath ek retry

Endpoint (verified live):  /api/market-data-pre-open?key=ALL
  -> ek request me ~2,200+ symbols ka poora pre-open auction data
"""
import time

from curl_cffi import requests as creq

BASE = "https://www.nseindia.com"
PRE_OPEN_URL = BASE + "/api/market-data-pre-open?key=ALL"


class NSEClient:
    def __init__(self, warm_max_age: float = 900.0, impersonate: str = "chrome"):
        self.warm_max_age = warm_max_age
        self.impersonate = impersonate
        self._session = None
        self._warmed_at = 0.0

    def _warm(self, force: bool = False):
        refresh = force or self._session is None or (
            time.time() - self._warmed_at > self.warm_max_age
        )
        if not refresh:
            return
        if self._session is not None:
            try:
                self._session.close()
            except Exception:
                pass
        s = creq.Session(impersonate=self.impersonate)
        r = s.get(BASE, timeout=25)
        if r.status_code != 200:
            s.close()
            raise RuntimeError(f"NSE warm-up failed: HTTP {r.status_code}")
        self._session = s
        self._warmed_at = time.time()

    def _get(self, url: str, referer: str, timeout: float):
        self._warm()
        r = self._session.get(
            url,
            headers={"accept": "application/json, text/plain, */*", "referer": referer},
            timeout=timeout,
        )
        if r.status_code != 200:
            # stale/missing Akamai cookies -> fresh warm-up, ek retry
            self._warm(force=True)
            r = self._session.get(
                url,
                headers={"accept": "application/json, text/plain, */*", "referer": referer},
                timeout=timeout,
            )
        return r

    def fetch_preopen(self, timeout: float = 25.0) -> dict:
        """Poore market ka pre-open snapshot (dict)."""
        r = self._get(PRE_OPEN_URL, BASE + "/market-data/pre-open-market", timeout)
        if r.status_code != 200:
            raise RuntimeError(f"pre-open fetch failed: HTTP {r.status_code}")
        return r.json()
