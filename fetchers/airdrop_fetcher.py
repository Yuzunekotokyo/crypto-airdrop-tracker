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
            "id": "meteora-s2",
            "name": "Meteora (Season 2 Claim)",
            "symbol": "MET",
            "category": "DeFi/DEX",
            "type": "クレーム",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Season 2のクレームが10/21予定。対象ウォレットは公式で確認。(推定価値は未公表)",
            "tasks": ['公式サイトで対象確認', '10/21のクレーム開始に備える'],
            "end_date": "2026-10-21",
            "logo": "",
            "url": "https://meteora.ag/",
            "is_hot": True,
            "added_date": "2026-10-17",
            "source": "curated",
        },
        {
            "id": "pharos-claim",
            "name": "Pharos (Claim Portal)",
            "symbol": "PHAR",
            "category": "Layer1",
            "type": "クレーム",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "クレームポータルが10/25に終了。未請求なら期限前に確認。(推定価値は未公表)",
            "tasks": ['公式クレームポータルで資格確認', '期限(10/25)までに請求'],
            "end_date": "2026-10-25",
            "logo": "",
            "url": "https://pharosnetwork.xyz/",
            "is_hot": True,
            "added_date": "2026-10-17",
            "source": "curated",
        },
        {
            "id": "questflow-arena-s3",
            "name": "Questflow Trader Arena Season 3",
            "symbol": "",
            "category": "AI/DeFi",
            "type": "キャンペーン",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "Base上のトレーディング大会。10/24まで。資金リスクあり。",
            "tasks": ['Base上でArenaに参加', '期間中の取引・ポイント獲得'],
            "end_date": "2026-10-24",
            "logo": "",
            "url": "https://questflow.ai/",
            "is_hot": False,
            "added_date": "2026-10-17",
            "source": "curated",
        },
        {
            "id": "polymarket-token",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "ポイント/未確定",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "トークン・エアドロップ示唆あり。ただし公式の日程は未確認で、米国再開が優先との情報。",
            "tasks": ['Polymarketでの継続的な取引・流動性提供'],
            "end_date": "未定",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": "2026-10-17",
            "source": "curated",
        },
        {
            "id": "ekiden",
            "name": "Ekiden",
            "symbol": "",
            "category": "DeFi/DEX",
            "type": "ポイント",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "メインネット連動のリワードプログラムを確認済み。取引でポイントを獲得。",
            "tasks": ['メインネット開始後に取引', 'ポイント獲得'],
            "end_date": "未定",
            "logo": "",
            "url": "https://ekiden.fi/",
            "is_hot": False,
            "added_date": "2026-10-17",
            "source": "curated",
        },
        {
            "id": "brownian",
            "name": "Brownian",
            "symbol": "",
            "category": "DeFi",
            "type": "TGE予定",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "TGEは遅くとも2026年Q4目標(市況次第)。",
            "tasks": ['公式告知のフォロー'],
            "end_date": "2026-12-31",
            "logo": "",
            "url": "",
            "is_hot": False,
            "added_date": "2026-10-17",
            "source": "curated",
        },
        {
            "id": "apyx-pips",
            "name": "Apyx (Pips Campaign)",
            "symbol": "",
            "category": "DeFi",
            "type": "ポイント",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Pipsキャンペーンのブースト報酬が10月中継続。",
            "tasks": ['Apyxへ入金してPips獲得'],
            "end_date": "2026-10-31",
            "logo": "",
            "url": "https://apyx.fi/",
            "is_hot": False,
            "added_date": "2026-10-17",
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
