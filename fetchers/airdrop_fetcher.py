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
    """手動管理の注目エアドロップシードデータ (毎日のWeb調査で更新)"""
    today = datetime.utcnow().strftime("%Y-%m-%d")

    def mk(id_, name, symbol, cat, typ, status, diff, val, desc, tasks, end, url, hot):
        return {
            "id": id_, "name": name, "symbol": symbol, "category": cat, "type": typ,
            "status": status, "difficulty": diff, "estimated_value_usd": val,
            "description": desc, "tasks": tasks, "end_date": end, "logo": "",
            "url": url, "is_hot": hot, "added_date": today, "source": "curated",
        }

    return [
        mk("standx-dusd", "StandX (DUSD)", "DUSD", "DeFi/DEX", "クレーム受付中", "active", "easy", 300,
           "クレーム受付が2026-11-02に開始。対象者は期限内に請求が必要。",
           ["公式サイトで対象アドレスを確認", "期限内にクレーム実行"], "2026-12-31", "https://standx.com/", True),
        mk("aster-stage6", "Aster (ASTER) Stage 6", "ASTER", "DeFi/DEX", "ポイント配布", "active", "medium", 500,
           "Stage 6で6,400万ASTERを配布。10,000ポイント以上のユーザーが対象。",
           ["10,000ポイント以上を獲得", "期限内にクレーム"], "2026-12-04", "https://www.asterdex.com/", True),
        mk("doppler-xdp", "Doppler Finance (XDP)", "XDP", "DeFi/DEX", "ジェネシス", "active", "easy", 200,
           "Base上でGenesis Airdropのクレーム受付中。2026-07-30以前にBaseアドレスを登録した人のみ対象。",
           ["対象アドレスか確認", "Base上でクレーム"], "2026-11-28", "https://www.doppler.finance/", False),
        mk("variational", "Variational", "", "DeFi/DEX", "TGE予定", "upcoming", "medium", 500,
           "トークン配分確定済み。ジェネシスエアドロップはTGE(2026年Q4目標)に連動。",
           ["プラットフォームでの取引・ポイント獲得"], "未定", "https://variational.io/", True),
        mk("kraken-ink", "Kraken INK配布", "INK", "Layer2", "発表済み", "upcoming", "medium", 300,
           "Krakenが配布を発表済みだが、対象条件は未確定。続報待ち。",
           ["Ink関連アクティビティ", "公式発表を確認"], "未定", "https://inkonchain.com/", False),
        mk("metric", "Metric", "", "その他", "ポイント(推測)", "upcoming", "easy", 0,
           "ポイント制の推測段階。潜在的な日付は2026-11-07(CryptoRank)。確約なし。",
           ["ポイント獲得タスクの実施"], "未定", "https://cryptorank.io/drophunting", False),
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
