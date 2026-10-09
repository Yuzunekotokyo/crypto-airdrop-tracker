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
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "トークン/エアドロップ予告",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 1000,
            "description": "CMOがPOLYトークンとエアドロップを示唆済み(米国再開後に注力)。公式未発表のため偽の請求リンクに注意。",
            "tasks": ['予測市場で継続的に取引', '複数マーケットに参加', '公式発表を確認'],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": "2026-10-09",
            "source": "curated",
        },
        {
            "id": "metamask-token",
            "name": "MetaMask (ポイント)",
            "symbol": "",
            "category": "ウォレット",
            "type": "ポイント制",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 500,
            "description": "MetaMaskのポイントが稼働中。ネイティブトークン発行が見込まれるが配布詳細は未確定。",
            "tasks": ['MetaMaskでスワップ/ブリッジ', 'MUSD/Card等の機能利用', 'ポイントを貯める'],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://metamask.io/",
            "is_hot": True,
            "added_date": "2026-10-09",
            "source": "curated",
        },
        {
            "id": "kraken-ink",
            "name": "Kraken Ink (INK)",
            "symbol": "INK",
            "category": "L2",
            "type": "Kraken Drops",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 400,
            "description": "KrakenのL2 Ink。INKはKraken Dropsで配布予定と報じられ、Ink PointsとKraken Pro利用が対象。",
            "tasks": ['Ink Pointsを獲得', 'Kraken Proで取引', 'Ink上のDeFi利用'],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://inkonchain.com/",
            "is_hot": False,
            "added_date": "2026-10-09",
            "source": "curated",
        },
        {
            "id": "ekiden",
            "name": "Ekiden",
            "symbol": "",
            "category": "DeFi/DEX",
            "type": "ポイント制",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 300,
            "description": "メインネットローンチに合わせたリワード計画を公表。取引でポイント獲得、テストネット上位トレーダーが先行アクセス。",
            "tasks": ['テストネットで取引', 'メインネット後にポイント獲得'],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://ekiden.fi/",
            "is_hot": False,
            "added_date": "2026-10-09",
            "source": "curated",
        },
        {
            "id": "apyx",
            "name": "Apyx (Pips)",
            "symbol": "APYX",
            "category": "DeFi",
            "type": "ポイント制",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 200,
            "description": "Pipsキャンペーンが2026年10月まで延長され、ブースト報酬あり。トークンは未発行。",
            "tasks": ['Apyxに入金/ステーキング', 'Pipsを獲得'],
            "end_date": (today + timedelta(days=21)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://apyx.fi/",
            "is_hot": False,
            "added_date": "2026-10-09",
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
