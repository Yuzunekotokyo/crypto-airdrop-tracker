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
            "id": "aster-aster", "name": "Aster (ASTER)", "symbol": "ASTER", "category": "DeFi/DEX", "type": "ステージ報酬",
            "status": "active", "difficulty": "easy", "estimated_value_usd": 300,
            "description": "Stage 6 の請求受付中。全配分の請求は10/28から開放。請求期限 2026-11-28 12:00 UTC。",
            "tasks": ['公式サイトで資格確認・請求', '請求前に公式URLを必ず確認'],
            "end_date": "2026-11-28", "logo": "", "url": "https://www.asterdex.com/", "is_hot": True,
            "added_date": "2026-11-05", "source": "curated",
        },
        {
            "id": "standx-dusd", "name": "StandX (DUSD)", "symbol": "DUSD", "category": "DeFi/DEX", "type": "ポイント報酬",
            "status": "active", "difficulty": "easy", "estimated_value_usd": 200,
            "description": "請求が2026-11-02に開始(11/1から延期)。期限 2026-12-31 08:00 UTC。",
            "tasks": ['公式サイトで資格確認・請求'],
            "end_date": "2026-12-31", "logo": "", "url": "https://standx.com/", "is_hot": True,
            "added_date": "2026-11-05", "source": "curated",
        },
        {
            "id": "doppler-xdp", "name": "Doppler Finance (XDP)", "symbol": "XDP", "category": "DeFi", "type": "ジェネシス",
            "status": "active", "difficulty": "easy", "estimated_value_usd": 150,
            "description": "Genesis Airdrop の請求受付中(登録は終了済み)。請求期限 2026-11-28 12:00 UTC。",
            "tasks": ['公式サイトで資格確認・請求'],
            "end_date": "2026-11-28", "logo": "", "url": "https://www.doppler.finance/", "is_hot": False,
            "added_date": "2026-11-05", "source": "curated",
        },
        {
            "id": "variational-var", "name": "Variational (VAR)", "symbol": "VAR", "category": "DeFi/DEX", "type": "ポイント報酬",
            "status": "upcoming", "difficulty": "medium", "estimated_value_usd": 500,
            "description": "公式トークノミクスで供給の32%をポイント保有者へのジェネシスエアドロップに配分。TGEは2026年Q4目標(日付未確定)。",
            "tasks": ['Variationalでポイントを貯める(取引・流動性)'],
            "end_date": "未定", "logo": "", "url": "https://variational.io/", "is_hot": True,
            "added_date": "2026-11-05", "source": "curated",
        },
        {
            "id": "ink-ink", "name": "Ink (INK)", "symbol": "INK", "category": "Layer2", "type": "レトロアクティブ",
            "status": "upcoming", "difficulty": "medium", "estimated_value_usd": 300,
            "description": "エアドロップは発表済みだが対象条件は未確定。",
            "tasks": ['Ink上でのブリッジ・DeFi利用で実績を作る'],
            "end_date": "未定", "logo": "", "url": "https://inkonchain.com/", "is_hot": False,
            "added_date": "2026-11-05", "source": "curated",
        },
        {
            "id": "apyx", "name": "Apyx", "symbol": "", "category": "DeFi", "type": "シーズン制",
            "status": "upcoming", "difficulty": "medium", "estimated_value_usd": 200,
            "description": "Season1/2の配分は確定、TGEは延期中。",
            "tasks": ['シーズンポイントを貯める'],
            "end_date": "未定", "logo": "", "url": "https://apyx.fi/", "is_hot": False,
            "added_date": "2026-11-05", "source": "curated",
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
