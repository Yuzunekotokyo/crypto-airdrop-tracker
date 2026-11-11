import os
from dotenv import load_dotenv

load_dotenv()

GMAIL_SENDER = os.getenv("GMAIL_SENDER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
GMAIL_RECIPIENT = os.getenv("GMAIL_RECIPIENT", "tsukamoto.kei@gmail.com")
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")
UPDATE_HOUR = int(os.getenv("UPDATE_HOUR", "8"))
UPDATE_MINUTE = int(os.getenv("UPDATE_MINUTE", "0"))

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
AIRDROPS_FILE = os.path.join(DATA_DIR, "airdrops.json")
UPDATES_FILE = os.path.join(DATA_DIR, "updates.json")
SIGNAL_STATE_FILE = os.getenv("SIGNAL_STATE_FILE", os.path.join(DATA_DIR, "signal_state.json"))


def _opt_float(name: str):
    v = os.getenv(name, "").strip()
    return float(v) if v else None


# --- 週足コンフルエンス・シグナル ---
SIGNAL_SYMBOLS = [s.strip().upper() for s in os.getenv("SIGNAL_SYMBOLS", "BTC").split(",") if s.strip()]
SIGNAL_INTERVAL_MIN = int(os.getenv("SIGNAL_INTERVAL_MIN", "15"))
SIGNAL_CONFLUENCE_PCT = float(os.getenv("SIGNAL_CONFLUENCE_PCT", "4")) / 100
SIGNAL_MIN_LEVELS = int(os.getenv("SIGNAL_MIN_LEVELS", "3"))
SIGNAL_WATCH_PCT = float(os.getenv("SIGNAL_WATCH_PCT", "3")) / 100
SIGNAL_TOUCH_PCT = float(os.getenv("SIGNAL_TOUCH_PCT", "0.5")) / 100
SIGNAL_BREAK_PCT = float(os.getenv("SIGNAL_BREAK_PCT", "2")) / 100
SIGNAL_COOLDOWN_HOURS = float(os.getenv("SIGNAL_COOLDOWN_HOURS", "24"))
# フィボの起点・終点を手動で固定したい場合 (最初の銘柄にのみ適用。空なら自動検出)
SIGNAL_SWING_LOW = _opt_float("SIGNAL_SWING_LOW")
SIGNAL_SWING_HIGH = _opt_float("SIGNAL_SWING_HIGH")
