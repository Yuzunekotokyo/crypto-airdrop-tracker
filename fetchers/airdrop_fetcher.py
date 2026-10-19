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
    """手動管理の注目エアドロップシードデータ (毎日の更新で見直し)"""
    today = datetime.utcnow().strftime("%Y-%m-%d")

    def item(id_, name, symbol, category, type_, status, difficulty, value, desc, tasks, end, url, hot):
        return {
            "id": id_, "name": name, "symbol": symbol, "category": category, "type": type_,
            "status": status, "difficulty": difficulty, "estimated_value_usd": value,
            "description": desc, "tasks": tasks, "end_date": end, "logo": "", "url": url,
            "is_hot": hot, "added_date": today, "source": "curated",
        }

    return [
        item("meteora-met", "Meteora (MET)", "MET", "DeFi/DEX", "LP報酬クレーム", "active", "easy", 0,
             "LP Stimulus Season 2のクレーム受付中。約2,000万MET(供給量の約2%)。ポイント10万以上かつ10MET以上が対象。"
             "期限は2026-10-21で、まもなく締切。手数料用にSOLが必要。",
             ["対象ウォレットで公式クレームページを確認", "Solanaトランザクションでクレーム実行", "公式URL以外にウォレットを接続しない"],
             "2026-10-21", "https://meteora.ag/", True),
        item("pharos-pros", "Pharos (PROS)", "PROS", "Layer1", "クレーム", "active", "easy", 0,
             "クレームポータルが2026-10-25に閉鎖。未請求分はPharos Foundationに戻る。",
             ["公式ポータルで資格確認", "期限までにクレーム"],
             "2026-10-25", "https://pharos.xyz/", True),
        item("polymarket", "Polymarket", "", "予測市場", "取引量ベース(未確定仕様)", "upcoming", "medium", 0,
             "CMOが「トークンとエアドロップがある」と公言。詳細・スナップショット日は未発表。",
             ["Polymarketでの取引・取引量の積み上げ", "多様な市場への参加"],
             "未定", "https://polymarket.com/", True),
        item("jupiter-jup", "Jupiter (JUP)", "JUP", "DeFi/DEX", "ステーキング/取引", "active", "easy", 0,
             "トラッカー上でconfirmed表示(10/16時点)。ステーキングと取引が対象。詳細は公式で要確認。",
             ["JUPのステーキング", "Jupiterでのスワップ"],
             "未定", "https://jup.ag/", False),
        item("ekiden", "Ekiden", "", "DeFi/DEX", "ポイント", "active", "medium", 0,
             "10/18にconfirmed掲載。取引とメインネット利用でポイント獲得。情報は未検証。",
             ["取引", "メインネットでの利用"],
             "未定", "https://ekiden.fi/", False),
        item("opensea-sea", "OpenSea (SEA)", "SEA", "NFT", "ポイント(未確定)", "upcoming", "easy", 0,
             "SEAトークンは期待されているが公式確定は未確認。ポイントプログラム報告あり。",
             ["OpenSeaでの売買・利用"], "未定", "https://opensea.io/", False),
        item("metamask", "MetaMask", "", "ウォレット", "ポイント(未確定)", "upcoming", "easy", 0,
             "ポイントプログラム稼働中との報告。トークン確定は未確認。",
             ["MetaMaskのスワップ・Perps等を利用"], "未定", "https://metamask.io/", False),
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
