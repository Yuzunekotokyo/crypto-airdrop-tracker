"""
Airdrop情報をWeb/APIから収集するモジュール。
現在はairdrops.ioのパブリックページとCoinGeckoトレンドを組み合わせて使用。
"""

import requests
import logging
from datetime import datetime
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


def _item(id, name, symbol, category, type_, status, difficulty, value, desc, tasks, end, url, hot, added):
    return {
        "id": id, "name": name, "symbol": symbol, "category": category, "type": type_,
        "status": status, "difficulty": difficulty, "estimated_value_usd": value,
        "description": desc, "tasks": tasks, "end_date": end, "logo": "", "url": url,
        "is_hot": hot, "added_date": added, "source": "curated",
    }


def _build_seed_airdrops() -> list[dict]:
    """手動キュレーションの注目エアドロップ (毎日の調査結果で更新)。
    情報は各種アグリゲータの報道ベース。参加前に必ず公式サイトで確認すること。"""
    return [
        _item("aster-stage6", "Aster (ASTER) Stage 6", "ASTER", "DeFi/DEX", "ポイント配布", "active", "easy", 0,
              "Stage 6で6,400万ASTER(供給量の0.8%)を配布。10,000ポイント以上の参加者が対象。請求期間は11/4〜12/4(11/28とする情報もあり)。",
              ["10,000ポイント以上を保有", "公式サイトでクレーム"], "2026-12-04", "https://www.asterdex.com/", True, "2026-11-07"),
        _item("standx-dusd", "StandX (DUSD)", "DUSD", "DeFi/DEX", "ポイント配布", "active", "easy", 0,
              "2026-11-02にクレーム開始。12/31まで請求可能。",
              ["公式サイトでクレーム確認"], "2026-12-31", "https://standx.com/", True, "2026-11-07"),
        _item("variational-var", "Variational (VAR)", "VAR", "DeFi/DEX", "ポイント→TGE", "upcoming", "medium", 0,
              "VARの供給量32%をポイント保有者にジェネシスエアドロップ(TGEで全量アンロック)。TGEは2026年Q4目標。",
              ["Variationalでの取引・ポイント獲得"], "未定(Q4 TGE予定)", "https://variational.io/", True, "2026-11-07"),
        _item("ink-kraken", "Ink (Kraken L2)", "INK", "Layer2", "レトロアクティブ", "upcoming", "medium", 0,
              "KrakenのL2 Inkのエアドロップが発表済み。対象条件は未確定。",
              ["Ink上でのDeFi・ブリッジ利用"], "未定", "https://inkonchain.com/", False, "2026-11-07"),
        _item("apyx", "Apyx", "", "DeFi", "シーズン制", "upcoming", "easy", 0,
              "Season1で5%、Season2で9%を配分予定だがTGEは延期中。",
              ["Apyxのポイントプログラム参加"], "未定(TGE延期)", "https://apyx.fi/", False, "2026-11-07"),
        _item("points-perps", "ポイント系Perp DEX (Extended / RISEx / Ekiden)", "", "DeFi/DEX", "ポイントプログラム", "active", "medium", 0,
              "いずれもポイント制でトークン配布は未保証。取引・流動性提供でポイント獲得。",
              ["各DEXで取引", "流動性提供"], "未定", "https://cryptorank.io/drophunting", False, "2026-11-07"),
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
