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
    """手動管理の注目エアドロップ (毎日の更新ルーチンで Web 検索結果をもとに書き換え)。
    日付は固定値。公式発表を必ず確認すること (集約サイトの情報は不一致あり)。"""
    def item(id_, name, symbol, category, type_, status, difficulty, value, desc, tasks, end, url, hot, added, source):
        return {
            "id": id_, "name": name, "symbol": symbol, "category": category, "type": type_,
            "status": status, "difficulty": difficulty, "estimated_value_usd": value,
            "description": desc, "tasks": tasks, "end_date": end, "logo": "",
            "url": url, "is_hot": hot, "added_date": added, "source": source,
        }

    return [
        item("aster-stage6", "Aster (Stage 6)", "ASTER", "DeFi/DEX", "ポイント配布", "active", "medium", 500,
             "Perp DEX。Stage 6 のクレーム期間。ソースにより開始日が異なる (10/28 12:00 UTC〜11/28 説 / 11/4 開始説)。",
             ["チェッカーで割当を確認", "公式サイトからクレーム", "ベスティング条件を確認"],
             "2026-11-28", "https://www.asterdex.com/", True, "2026-11-02", "cryptoticker / web"),
        item("standx-dusd", "StandX (DUSD)", "DUSD", "DeFi/DEX", "ポイント配布", "active", "easy", 300,
             "StandX のエアドロップ。11/1〜12/31 がクレーム期間 (公式発表ベース)。",
             ["チェッカーページでポイント確認", "クレーム期間内に請求"],
             "2026-12-31", "https://standx.com/", True, "2026-11-02", "cryptoticker / web"),
        item("variational-var", "Variational (VAR)", "VAR", "DeFi/DEX", "ポイント → TGE", "upcoming", "medium", 1000,
             "VARトークン総供給の32%をポイント保有者のジェネシスエアドロップに配分。TGEは2026年Q4目標 (正確な日付は未確認)。",
             ["ポイントプログラムで取引", "TGE告知を監視"],
             "未定 (Q4 2026目標)", "https://variational.io/", True, "2026-11-02", "web"),
        item("metamask-rewards", "MetaMask Rewards", "", "ウォレット", "リワード", "active", "easy", 200,
             "MetaMask のリワード。オプトイン期限が 2026-11-12。スワップ/ブリッジ利用が対象。",
             ["オプトインを完了 (期限 11/12)", "スワップ・ブリッジを利用"],
             "2026-11-12", "https://metamask.io/", True, "2026-11-02", "web"),
        item("bulk-season1", "BULK (Season 1)", "", "DeFi/DEX", "シーズン制ポイント", "active", "medium", 300,
             "Season 1 は 10/10〜12/05。ステーキングや Discord ロール等の追加ルートあり。",
             ["取引でポイント獲得", "ステーキング", "Discordロール取得"],
             "2026-12-05", "https://bulk.trade/", False, "2026-11-02", "web"),
        item("xdp-genesis", "XDP Genesis Airdrop", "XDP", "その他", "クレーム", "active", "easy", 100,
             "Genesis エアドロップのクレームが 11/28 12:00 UTC まで。",
             ["資格を確認", "期限内にクレーム"],
             "2026-11-28", "", False, "2026-11-02", "web"),
        item("sophon-sunset", "Sophon (メインネット終了)", "SOPH", "Layer2", "終了注意", "active", "easy", 0,
             "Sophon メインネットが 11/30 に完全停止。資産の引き出し期限は 11/25。資金を残さないよう注意。",
             ["資産を 11/25 までに引き出し"],
             "2026-11-25", "", False, "2026-11-02", "web"),
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
