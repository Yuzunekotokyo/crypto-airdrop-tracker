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
            "id": "variational-var", "name": "Variational (VAR)", "symbol": "VAR", "category": "DeFi/DEX", "type": "ポイント→TGE",
            "status": "upcoming", "difficulty": "medium", "estimated_value_usd": 1000,
            "description": "Perp DEX。供給の32%をポイント保有者へGenesis配布(TGE時100%アンロック)、TGEは2026年Q4目標。具体日未発表。",
            "tasks": ['ポイントプログラムで取引', '公式発表を監視'],
            "end_date": "2026-12-31", "logo": "", "url": "https://variational.io/", "is_hot": True,
            "added_date": "2026-11-01", "source": "curated (web調査 2026-11-01・要公式確認)",
        },
        {
            "id": "aster-aster", "name": "Aster (ASTER) Stage 6", "symbol": "ASTER", "category": "DeFi/DEX", "type": "クレーム",
            "status": "active", "difficulty": "easy", "estimated_value_usd": 300,
            "description": "Stage 6クレーム期間。ソースにより10/28開始〜11/28 12:00 UTC、または11/4開始と情報が割れているため公式で要確認。",
            "tasks": ['公式でクレーム資格を確認'],
            "end_date": "2026-11-28", "logo": "", "url": "https://www.asterdex.com/", "is_hot": True,
            "added_date": "2026-11-01", "source": "curated (web調査 2026-11-01・要公式確認)",
        },
        {
            "id": "standx-dusd", "name": "StandX (DUSD)", "symbol": "DUSD", "category": "DeFi/DEX", "type": "クレーム",
            "status": "active", "difficulty": "easy", "estimated_value_usd": 200,
            "description": "クレーム期間 2026-11-01〜2026-12-31。チェッカーは10/26から公開。",
            "tasks": ['公式チェッカーで資格確認', 'クレーム実行'],
            "end_date": "2026-12-31", "logo": "", "url": "https://standx.com/", "is_hot": True,
            "added_date": "2026-11-01", "source": "curated (web調査 2026-11-01・要公式確認)",
        },
        {
            "id": "xdp-genesis", "name": "XDP Genesis Airdrop", "symbol": "XDP", "category": "その他", "type": "クレーム",
            "status": "active", "difficulty": "easy", "estimated_value_usd": 100,
            "description": "Genesis Airdropのクレームは2026-11-28 12:00 UTCまで。",
            "tasks": ['公式でクレーム確認'],
            "end_date": "2026-11-28", "logo": "", "url": "", "is_hot": False,
            "added_date": "2026-11-01", "source": "curated (web調査 2026-11-01・要公式確認)",
        },
        {
            "id": "bulk-season1", "name": "BULK Season 1", "symbol": "BULK", "category": "DeFi/DEX", "type": "ポイント",
            "status": "active", "difficulty": "medium", "estimated_value_usd": 0,
            "description": "Season 1は2026-10-10〜12-05。ポイントプログラムでありトークン配布は未確定。",
            "tasks": ['ポイント獲得(ステーキング/Discordロール等)'],
            "end_date": "2026-12-05", "logo": "", "url": "", "is_hot": False,
            "added_date": "2026-11-01", "source": "curated (web調査 2026-11-01・要公式確認)",
        },
        {
            "id": "ink-kraken", "name": "Ink (INK) by Kraken", "symbol": "INK", "category": "Layer2", "type": "発表済み",
            "status": "upcoming", "difficulty": "medium", "estimated_value_usd": 500,
            "description": "Kraken発のL2。エアドロ発表済みだが資格・変換式・TGE日は未発表。",
            "tasks": ['Ink上でDeFi利用', '公式発表を監視'],
            "end_date": "未定", "logo": "", "url": "https://inkonchain.com/", "is_hot": False,
            "added_date": "2026-11-01", "source": "curated (web調査 2026-11-01・要公式確認)",
        },
        {
            "id": "predict-token", "name": "Predict (PREDICT)", "symbol": "PREDICT", "category": "予測市場", "type": "Season1",
            "status": "upcoming", "difficulty": "medium", "estimated_value_usd": 0,
            "description": "供給7%(70M)をSeason 1エアドロに割当。10/29にプレセール予定。低品質ソースのみ・詐欺注意。",
            "tasks": ['公式確認を最優先'],
            "end_date": "未定", "logo": "", "url": "", "is_hot": False,
            "added_date": "2026-11-01", "source": "curated (web調査 2026-11-01・要公式確認)",
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
