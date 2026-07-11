import requests
import logging
from config import COINGECKO_API_KEY

logger = logging.getLogger(__name__)

BASE_URL = "https://api.coingecko.com/api/v3"


def _headers():
    h = {"accept": "application/json"}
    if COINGECKO_API_KEY:
        h["x-cg-demo-api-key"] = COINGECKO_API_KEY
    return h


def _fallback_trending():
    """CoinGecko APIに到達できない場合の代替データ (定期的に手動更新)。"""
    names = ["Zano", "Cash Cat", "Pudgy Penguins", "LAB", "Lighter", "Virtuals Protocol", "Uniswap"]
    return [{"id": n.lower().replace(" ", "-"), "name": n, "symbol": "", "rank": None, "thumb": "", "price_btc": 0, "score": i} for i, n in enumerate(names)]


def get_trending_coins():
    try:
        r = requests.get(f"{BASE_URL}/search/trending", headers=_headers(), timeout=10)
        r.raise_for_status()
        coins = r.json().get("coins", [])
        return [
            {
                "id": c["item"]["id"],
                "name": c["item"]["name"],
                "symbol": c["item"]["symbol"].upper(),
                "rank": c["item"].get("market_cap_rank"),
                "thumb": c["item"].get("thumb", ""),
                "price_btc": c["item"].get("price_btc", 0),
                "score": c["item"].get("score", 0),
            }
            for c in coins[:10]
        ]
    except Exception as e:
        logger.warning(f"CoinGecko trending fetch failed: {e}, using fallback")
        return _fallback_trending()


def get_coin_price(coin_ids: list[str]):
    if not coin_ids:
        return {}
    try:
        ids = ",".join(coin_ids)
        r = requests.get(
            f"{BASE_URL}/simple/price",
            params={"ids": ids, "vs_currencies": "usd,jpy", "include_24hr_change": "true"},
            headers=_headers(),
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning(f"CoinGecko price fetch failed: {e}")
        return {}


def get_new_coins():
    """直近7日以内に上場した新着コインを取得"""
    try:
        r = requests.get(
            f"{BASE_URL}/coins/list/new",
            headers=_headers(),
            timeout=10,
        )
        r.raise_for_status()
        return r.json()[:20]
    except Exception as e:
        logger.warning(f"CoinGecko new coins fetch failed: {e}")
        return []
