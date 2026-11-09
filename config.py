"""Scanner configuration."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Dashboard
PORT = 8787

# Polling (pre-open session 9:00-9:15 ke dauraan live update)
POLL_INTERVAL_SEC = 6.0

# NSE Akamai cookie warm-up kitni der tak force reh
COOKIE_WARM_MAX_AGE = 900.0
# Paths
DATA_DIR = ROOT / "data"
FIXTURE = ROOT / "fixtures" / "preopen_20261029.json"
