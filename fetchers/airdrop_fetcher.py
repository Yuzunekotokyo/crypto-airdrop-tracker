"""
Airdrop情報をWeb/APIから収集するモジュール。
現在はairdrops.ioのパブリックページとCoinGeckoトレンドを組み合わせて使用。
"""

import requests
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from fetchers.coingecko import get_trending_coins, get_new_coins

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def _scrape_airdrops_io() -> list[dict]:
    """airdrops.ioのトップページからアクティブエアドロップを取得"""
    try:
        r = requests.get("https://airdrops.io/", headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        items = []
        for card in soup.select(".airdrop-item")[:30]:
            name_el = card.select_one(".airdrop-title") or card.select_one("h3")
            link_el = card.select_one("a[href]")
            value_el = card.select_one(".airdrop-value") or card.select_one(".value")
            end_el = card.select_one(".airdrop-end") or card.select_one(".end-date")
            img_el = card.select_one("img")

            if not name_el:
                continue

            items.append({
                "name": name_el.get_text(strip=True),
                "url": link_el["href"] if link_el else "https://airdrops.io/",
                "estimated_value": value_el.get_text(strip=True) if value_el else "不明",
                "end_date": end_el.get_text(strip=True) if end_el else "未定",
                "logo": img_el.get("src", "") if img_el else "",
                "source": "airdrops.io",
            })
        return items
    except Exception as e:
        logger.warning(f"airdrops.io scrape failed: {e}")
        return []


def _build_seed_airdrops() -> list[dict]:
    """手動管理の注目エアドロップシードデータ (定期的に更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "hyperliquid-season2",
            "name": "Hyperliquid (HYPE) シーズン2",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "ポイント/追加配布",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "追加配布は公式未確認（総供給の約42%が将来配布枠）。HyperEVMのDEX・stHYPEでポイント稼ぎが話題。",
            "tasks": ['Hyperliquidで継続的に取引', 'HyperEVM上のDEXで流動性提供', 'stHYPEを保有'],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "jupiter-jup",
            "name": "Jupiter (JUP)",
            "symbol": "JUP",
            "category": "DeFi/DEX",
            "type": "ステーキング/取引",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "トラッカー上で10/28配布予定と掲載（未検証・要公式確認）。公式サイトで資格確認を。",
            "tasks": ['JUPステーキング', 'Jupiter上でスワップ'],
            "end_date": (today + timedelta(days=7)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://jup.ag/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "metric-points",
            "name": "Metric",
            "symbol": "",
            "category": "DeFi",
            "type": "ポイント",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "ポイント制の潜在的エアドロップ（未確認）。メインネット利用・流動性提供でポイント獲得。",
            "tasks": ['メインネット利用', '流動性提供'],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://airdropalert.com/farm/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "predict-fun",
            "name": "predict.fun",
            "symbol": "",
            "category": "予測市場",
            "type": "ポイント",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "潜在的エアドロップ候補（検証中・未確認）。予測市場での取引が対象と推測。",
            "tasks": ['予測市場で取引'],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://predict.fun/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-token",
            "name": "Base",
            "symbol": "",
            "category": "Layer2",
            "type": "投機的",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "トークン未発表のL2。エアドロップは推測のみで公式確認なし。",
            "tasks": ['Base上でdApp利用', '継続的なオンチェーン活動'],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://base.org/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
    ]


def fetch_all_airdrops() -> tuple[list[dict], list[str]]:
    """
    全ソースからエアドロップデータを収集し、変更点リストと共に返す。
    Returns: (airdrops_list, new_items_names)
    """
    curated = _build_seed_airdrops()
    scraped = _scrape_airdrops_io()

    seen_names = {a["name"].lower() for a in curated}
    new_items = []

    for s in scraped:
        if s["name"].lower() not in seen_names:
            curated.append({
                "id": s["name"].lower().replace(" ", "-"),
                "name": s["name"],
                "symbol": "",
                "category": "その他",
                "type": "エアドロップ",
                "status": "active",
                "difficulty": "easy",
                "estimated_value_usd": 0,
                "description": f"airdrops.ioより取得: {s.get('estimated_value', '')}",
                "tasks": [],
                "end_date": s.get("end_date", "未定"),
                "logo": s.get("logo", ""),
                "url": s.get("url", ""),
                "is_hot": False,
                "added_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "source": "airdrops.io",
            })
            new_items.append(s["name"])
            seen_names.add(s["name"].lower())

    # 注目度でソート: is_hot → estimated_value_usd
    curated.sort(key=lambda x: (not x.get("is_hot"), -x.get("estimated_value_usd", 0)))

    return curated, new_items
