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
            "id": "extended-ext",
            "name": "Extended (EXT)",
            "symbol": "EXT",
            "category": "DeFi/DEX",
            "type": "ポイント→トークン",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1000,
            "description": "オンチェーン永久先物DEX。EXT供給量の30%をポイント保有者へ配布予定(確定)。Season1は70Mポイント上限に接近中、TGE日は未発表。",
            "tasks": ['Extendedで先物取引', '流動性提供', '紹介プログラム参加'],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://extended.exchange/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "metamask-rewards",
            "name": "MetaMask Rewards (MASK/LINEA)",
            "symbol": "MASK",
            "category": "ウォレット",
            "type": "ポイント報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 800,
            "description": "MetaMask Rewards Season1で$30M相当のLINEA報酬。ポイントは将来のMetaMaskトークンにも紐づく見込み(公式詳細は未発表)。",
            "tasks": ['MetaMask内でスワップ', 'パープ取引', '紹介プログラム'],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://metamask.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "未確定(公式言及あり)",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 1500,
            "description": "CMOがトークンとエアドロップを明言。ただし公式ヘルプは現時点で未発表。米国ローンチ後にトークン着手の方針。",
            "tasks": ['Polymarketで継続的に取引', '複数マーケットに参加', '流動性提供'],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "pheasant-pnt",
            "name": "Pheasant (PNT)",
            "symbol": "PNT",
            "category": "その他",
            "type": "TGE",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 100,
            "description": "10/5 12:00 UTCにTGE予定。Kraken・Uniswap・KuCoinに上場予定。",
            "tasks": ['上場情報の確認', '公式案内に従い請求'],
            "end_date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://www.kucoin.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "nado-ink",
            "name": "Nado (INK)",
            "symbol": "INK",
            "category": "DeFi/DEX",
            "type": "ポイント→トークン",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 500,
            "description": "NadoのポイントはTGEで$INKに転換予定。TGEは2026年Q3想定(遅延の可能性あり)。",
            "tasks": ['Nadoで取引', 'ポイント獲得を継続'],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://www.inkonchain.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "apyx-pips",
            "name": "Apyx Pips Campaign",
            "symbol": "APYX",
            "category": "DeFi",
            "type": "ポイント",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 200,
            "description": "apxUSD保有または流動性提供でPips獲得。ブースト報酬付きで2026年10月まで延長。",
            "tasks": ['apxUSD保有', '流動性提供'],
            "end_date": (today + timedelta(days=28)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://www.apyx.fi/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "sonic-burn",
            "name": "Sonic 未請求トークン(焼却前)",
            "symbol": "S",
            "category": "Layer1",
            "type": "請求期限",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 50,
            "description": "未請求のSonicトークン約3269万枚が10/15以降に焼却対象。対象者は期限前に請求を。",
            "tasks": ['対象ウォレットで請求'],
            "end_date": (today + timedelta(days=12)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://www.soniclabs.com/",
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
