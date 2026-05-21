"""
DeFiLlama・CoinGecko から最新市場情報を取得するモジュール。
エアドロップ有望候補 (トークン未発行の高TVLプロトコル) も検出する。
"""

import requests
import logging

logger = logging.getLogger(__name__)
_LLAMA = "https://api.llama.fi"
_GECKO = "https://api.coingecko.com/api/v3"
HEADERS = {"User-Agent": "AirdropTracker/1.0", "Accept": "application/json"}

# トークン未発行とみなすシンボル値
_NO_TOKEN = {"", "-", "n/a", "none", "–"}


def fetch_major_prices() -> dict:
    """主要コインの現在価格・24h変動を取得"""
    from fetchers.coingecko import get_coin_price

    coin_ids = ["bitcoin", "ethereum", "solana", "bnb", "ripple"]
    raw = get_coin_price(coin_ids)
    labels = {
        "bitcoin":  ("BTC", "ビットコイン"),
        "ethereum": ("ETH", "イーサリアム"),
        "solana":   ("SOL", "ソラナ"),
        "bnb":      ("BNB", "BNB"),
        "ripple":   ("XRP", "リップル"),
    }
    result = {}
    for cid, (sym, name_ja) in labels.items():
        d = raw.get(cid, {})
        if d:
            change = round(d.get("usd_24h_change", 0) or 0, 2)
            result[sym] = {
                "name_ja": name_ja,
                "usd": d.get("usd", 0),
                "jpy": d.get("jpy", 0),
                "change_24h": change,
                "up": change >= 0,
            }
    return result


def fetch_global_market() -> dict:
    """CoinGecko グローバル市場統計を取得"""
    try:
        r = requests.get(f"{_GECKO}/global", headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json().get("data", {})
        change = round(data.get("market_cap_change_percentage_24h_usd", 0) or 0, 2)
        return {
            "total_market_cap_usd": data.get("total_market_cap", {}).get("usd", 0),
            "total_volume_usd": data.get("total_volume", {}).get("usd", 0),
            "market_cap_change_24h": change,
            "btc_dominance": round(data.get("market_cap_percentage", {}).get("btc", 0) or 0, 1),
            "active_cryptos": data.get("active_cryptocurrencies", 0),
        }
    except Exception as e:
        logger.warning(f"CoinGecko global failed: {e}")
        return {}


def fetch_airdrop_candidates(min_tvl: float = 50_000_000, limit: int = 10) -> list[dict]:
    """
    DeFiLlama でトークン未発行かつ高TVLのプロトコルを取得。
    これらはエアドロップ実施の可能性が高い。
    """
    try:
        r = requests.get(f"{_LLAMA}/protocols", headers=HEADERS, timeout=15)
        r.raise_for_status()
        protocols = r.json()

        candidates = [
            p for p in protocols
            if (str(p.get("symbol", "") or "").strip().lower() in _NO_TOKEN)
            and p.get("tvl", 0) >= min_tvl
        ]
        candidates.sort(key=lambda x: x.get("tvl", 0), reverse=True)

        return [
            {
                "name": p.get("name", ""),
                "symbol": p.get("symbol", "") or "",
                "tvl_usd": p.get("tvl", 0),
                "chain": p.get("chain", "") or "",
                "category": p.get("category", "") or "",
                "url": p.get("url", "") or "",
                "logo": p.get("logo", "") or "",
                "description": (p.get("description", "") or "")[:200],
            }
            for p in candidates[:limit]
        ]
    except Exception as e:
        logger.warning(f"DeFiLlama candidates failed: {e}")
        return []


def fetch_top_chains() -> list[dict]:
    """DeFiLlama TVL上位チェーンを取得"""
    try:
        r = requests.get(f"{_LLAMA}/v2/chains", headers=HEADERS, timeout=10)
        r.raise_for_status()
        chains = sorted(r.json(), key=lambda x: x.get("tvl", 0), reverse=True)
        return [
            {"name": c.get("name", ""), "tvl_usd": c.get("tvl", 0)}
            for c in chains[:5]
        ]
    except Exception as e:
        logger.warning(f"DeFiLlama chains failed: {e}")
        return []
