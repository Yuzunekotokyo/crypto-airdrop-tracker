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
