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
    """手動管理の注目エアドロップシードデータ (毎日の更新ルーチンで最新情報に書き換え)"""

    def item(id_, name, symbol, category, type_, status, difficulty, value, desc, tasks,
             end_date, url, hot, added):
        return {
            "id": id_, "name": name, "symbol": symbol, "category": category, "type": type_,
            "status": status, "difficulty": difficulty, "estimated_value_usd": value,
            "description": desc, "tasks": tasks, "end_date": end_date, "logo": "",
            "url": url, "is_hot": hot, "added_date": added, "source": "curated",
        }

    return [
        item("variational-var", "Variational (VAR)", "VAR", "DeFi/DEX", "ポイント",
             "upcoming", "medium", 1000,
             "P2P型パープDEX。公式トークノミクスで供給量の32%をポイント保有者へのジェネシスエアドロップに配分。TGEは2026年Q4予定。",
             ["Variationalで取引しポイント獲得", "取引量の継続", "公式発表のTGE日程を確認"],
             "2026-12-31", "https://variational.io/", True, "2026-10-31"),
        item("aster-stage6", "Aster (ASTER) Stage 6", "ASTER", "DeFi/DEX", "クレーム",
             "active", "easy", 300,
             "Stage 6の完全ベスト済み配分のクレーム受付中 (10/28〜11/28)。対象者は期限内に請求を。",
             ["公式クレームページで対象ウォレットを確認", "期限内に請求"],
             "2026-11-28", "https://www.asterdex.com/", True, "2026-10-31"),
        item("standx-dusd", "StandX (DUSD)", "DUSD", "DeFi/DEX", "クレーム",
             "upcoming", "easy", 200,
             "チェッカーページは10/26公開済み。クレームは11/1〜12/31。",
             ["チェッカーで資格確認", "11/1以降にクレーム"],
             "2026-12-31", "https://standx.com/", True, "2026-10-31"),
        item("bulk-trade", "BULK", "", "DeFi/DEX", "トレード大会",
             "active", "medium", 500,
             "エアドロップ確定。Season 1のトレード大会が10/10〜12/5開催中。",
             ["Season 1トレード大会に参加", "取引量・ポイントを積み上げ"],
             "2026-12-05", "https://bulk.trade/", False, "2026-10-31"),
        item("apyx", "Apyx", "", "DeFi", "ポイント",
             "upcoming", "medium", 300,
             "配分確定済み。9月にSeason 2配分を6%→9%へ増加、10/13予定だったTGEは延期。",
             ["Season 2のポイント獲得を継続", "TGE再発表を待つ"],
             "未定", "https://apyx.fi/", False, "2026-10-31"),
        item("lighter-lit", "Lighter (LIT)", "LIT", "DeFi/DEX", "ポイント",
             "upcoming", "medium", 800,
             "オンチェーンパープDEX。ポイントプログラム連動でLITのTGE/エアドロップが年末見込み (報道ベース、要公式確認)。",
             ["Lighterで取引しポイント獲得", "流動性提供"],
             "2026-12-31", "https://lighter.xyz/", True, "2026-10-31"),
        item("polymarket-token", "Polymarket", "", "予測市場", "未確定",
             "upcoming", "easy", 1000,
             "CMOが「トークンとエアドロップはある」と発言。時期は未発表。",
             ["Polymarketで継続的に取引", "複数カテゴリの市場に参加"],
             "未定", "https://polymarket.com/", True, "2026-10-31"),
        item("concrete-ct", "Concrete (CT)", "CT", "DeFi", "TGE予定",
             "upcoming", "easy", 300,
             "9月にネイティブトークンCTとTGE計画を公表。日付は未確認。",
             ["Concreteボールトへ入金", "ポイント獲得"],
             "未定", "https://concrete.xyz/", False, "2026-10-31"),
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
