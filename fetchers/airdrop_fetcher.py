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


def _entry(id, name, symbol, category, type_, status, difficulty, value, desc, tasks, days, url, hot, today):
    return {
        "id": id, "name": name, "symbol": symbol, "category": category, "type": type_,
        "status": status, "difficulty": difficulty, "estimated_value_usd": value,
        "description": desc, "tasks": tasks,
        "end_date": (today + timedelta(days=days)).strftime("%Y-%m-%d") if days else "未定",
        "logo": "", "url": url, "is_hot": hot,
        "added_date": today.strftime("%Y-%m-%d"), "source": "curated",
    }


def _build_seed_airdrops() -> list[dict]:
    """手動管理の注目エアドロップ (2026-10-08時点の調査結果。公式情報で要確認)"""
    today = datetime.utcnow()
    return [
        _entry("polymarket-poly", "Polymarket (POLY)", "POLY", "予測市場", "トークン確定", "upcoming", "medium", 1000,
               "CMOがトークンとエアドロップを公式に確認済み。米国版の再開を優先中で時期は未定。取引量が基準になると推測されるが未確認。",
               ["Polymarketで継続的に取引", "複数カテゴリのマーケットに参加", "公式発表の確認"], 0, "https://polymarket.com/", True, today),
        _entry("kraken-ink", "Kraken Ink (INK)", "INK", "Layer2", "取引所配布", "upcoming", "easy", 300,
               "KrakenがKraken Drops経由でINK配布を表明。Inkチェーン上の活動も評価対象とされる(詳細は未確認)。",
               ["Kraken Dropsに登録", "Inkチェーン上でのアクティビティ"], 0, "https://inkonchain.com/", True, today),
        _entry("opensea-sea", "OpenSea (SEA)", "SEA", "NFT", "トークン確定", "upcoming", "easy", 500,
               "コミュニティ配分約50%の計画。過去・現在のマーケットプレイス利用実績が対象。ローンチ時期は遅延中で未確定。",
               ["OpenSeaでNFT売買を継続", "OpenSea Rewards等の公式プログラムに参加"], 0, "https://opensea.io/", True, today),
        _entry("metamask-mask", "MetaMask (MASK)", "MASK", "ウォレット", "ポイント", "upcoming", "easy", 500,
               "LINEAで3000万ドル相当の報酬プログラムを実施中。MASKトークンの条件は非公式情報のみ(取引量ベースとの噂)。",
               ["MetaMask内でスワップ/パーペチュアル取引", "Lineaネットワーク利用", "公式Rewardsに参加"], 0, "https://metamask.io/", False, today),
        _entry("apyx-pips", "Apyx (APYX)", "APYX", "DeFi", "ポイント", "active", "medium", 200,
               "トークン未発行。Pipsキャンペーンが10月まで延長され報酬ブースト中。",
               ["Apyxにデポジット", "Pips獲得活動を継続"], 23, "https://apyx.fi/", False, today),
        _entry("tastyco", "TastyCo", "", "その他", "エアドロップ", "active", "easy", 0,
               "airdrops.ioで確認済みと掲載。詳細は公式で要確認。",
               ["公式サイトの手順に従う"], 0, "https://airdrops.io/", False, today),
        _entry("ekiden", "Ekiden / eCash.com", "", "その他", "エアドロップ", "active", "easy", 0,
               "Cryptorankで2026-10-02時点で確認済みと掲載。掲載情報に古い項目あり、公式で要確認。",
               ["公式サイトの手順に従う"], 0, "https://cryptorank.io/drophunting", False, today),
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
