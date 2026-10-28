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
    """手動管理の注目エアドロップシードデータ (2026-10-28 調査時点)"""
    today = datetime.utcnow().strftime("%Y-%m-%d")

    def mk(id_, name, symbol, cat, typ, status, diff, val, desc, tasks, end, url, hot):
        return {
            "id": id_, "name": name, "symbol": symbol, "category": cat, "type": typ,
            "status": status, "difficulty": diff, "estimated_value_usd": val,
            "description": desc, "tasks": tasks, "end_date": end, "logo": "",
            "url": url, "is_hot": hot, "added_date": today, "source": "curated",
        }

    return [
        mk("aster-stage6", "Aster (Stage 6 Convergence)", "ASTER", "DeFi/DEX", "ポイント報酬", "active", "easy", 0,
           "Stage 6のクレームが2026-10-28 12:00 UTCに開始。2億ASTERを配布。",
           ["クレームページで資格確認", "12:00 UTC以降にクレーム"], "2026-11-28", "https://www.asterdex.com/", True),
        mk("standx-dusd", "StandX (DUSD)", "DUSD", "DeFi/DEX", "ポイント報酬", "upcoming", "easy", 0,
           "チェッカーは10/26公開済み。クレーム期間は11/1〜12/31。",
           ["チェッカーで資格確認", "11/1以降にクレーム"], "2026-12-31", "https://standx.com/", True),
        mk("the-hood", "The Hood (HOOD)", "HOOD", "ミニアプリ", "クレーム", "active", "easy", 0,
           "Mini AppでのHOODクレームは10/31に終了。未請求なら急ぐ。",
           ["Mini Appを開く", "HOODをクレーム"], "2026-10-31", "https://airdrops.io/", True),
        mk("grass-s2", "Grass (Stage 2 / USDC)", "GRASS", "DePIN", "クレーム", "active", "easy", 0,
           "Stage 2はUSDCで支払い。2027-01-22までクレーム可能。",
           ["資格確認", "クレーム"], "2027-01-22", "https://www.grass.io/", False),
        mk("ekiden", "Ekiden", "", "DeFi/DEX", "ポイント報酬", "upcoming", "medium", 0,
           "メインネット連動のポイント制度が確定。取引活動でポイント獲得。",
           ["メインネットで取引", "ポイントを貯める"], "未定", "https://airdrops.io/", False),
        mk("tastyco", "TastyCo ($TASTY)", "TASTY", "その他", "ポイント報酬", "upcoming", "easy", 0,
           "TGE前にポイントを貯めた早期ユーザーへ総額10万ドルの$TASTYを配布予定。",
           ["ポイント収集"], "未定", "https://airdrops.io/", False),
        mk("polymarket", "Polymarket", "", "予測市場", "未確定(確定言及あり)", "upcoming", "medium", 0,
           "CMOがトークンとエアドロップを確認。日付未定、米国再開が優先。",
           ["Polymarketで継続的に取引", "複数市場に参加"], "未定", "https://polymarket.com/", True),
        mk("jumper-jump", "Jumper ($JUMP)", "JUMP", "インフラ", "XP報酬", "upcoming", "medium", 0,
           "TGEを示唆。Perps早期アクセスはXP上位2,500人に拡大。日付未定。",
           ["XPを貯める", "Perps利用"], "未定", "https://jumper.exchange/", False),
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
