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
    """手動管理の注目エアドロップシードデータ (毎日の更新で見直す / 最終見直し 2026-10-06)"""
    today = datetime.utcnow()
    added = "2026-10-06"

    def item(id_, name, symbol, category, type_, status, difficulty, value, desc, tasks, days, url, hot):
        return {
            "id": id_, "name": name, "symbol": symbol, "category": category, "type": type_,
            "status": status, "difficulty": difficulty, "estimated_value_usd": value,
            "description": desc, "tasks": tasks,
            "end_date": (today + timedelta(days=days)).strftime("%Y-%m-%d") if days else "未定",
            "logo": "", "url": url, "is_hot": hot, "added_date": added, "source": "curated",
        }

    return [
        item("polymarket-poly", "Polymarket (POLY)", "POLY", "予測市場", "トークン配布(公式確認済)", "upcoming", "medium", 1500,
             "予測市場最大手。CMOがPOLYトークンとエアドロップを公式に確認済み。取引量が最大のシグナル。",
             ["KYC完了", "複数カテゴリで継続的に取引", "流動性提供", "複数ウォレットは避ける(Sybil検知)"], 0,
             "https://polymarket.com/", True),
        item("opensea-sea", "OpenSea (SEA)", "SEA", "NFT", "トークン配布(公式確認済)", "active", "easy", 800,
             "総供給の50%をコミュニティへ配分。エアドロップ請求にKYC不要。NFT取引・出品・入札が対象。",
             ["NFTの取引", "NFTの出品", "入札"], 0, "https://opensea.io/", True),
        item("metamask-rewards", "MetaMask Rewards", "", "ウォレット", "ポイント/将来トークン", "active", "easy", 500,
             "MetaMask Rewards実施中。スワップ等の利用とタスクでポイント獲得、将来のトークン配分が示唆されている。",
             ["MetaMask内でスワップ", "タスク完了でポイント獲得"], 0, "https://metamask.io/", True),
        item("kraken-ink", "Ink (INK) via Kraken Drops", "INK", "Layer2", "トークン配布", "upcoming", "easy", 300,
             "Kraken発のL2 Ink。KrakenDropsで配布予定。Inkチェーン上の活動が配分に考慮される。",
             ["Kraken Dropsに登録", "Inkチェーン上でアクティビティ"], 0, "https://inkonchain.com/", False),
        item("wlfi-staking", "World Liberty Financial (WLFI) ステーキング", "WLFI", "DeFi", "ステーキング報酬", "active", "medium", 300,
             "10/2開始。解放済みWLFIを180日以上ロックしUSD1を獲得。初期報酬プール$1.25M。90日ごとにSnapshot投票が必要。",
             ["解放済みWLFIをEthereumでステーク", "90日ごとにSnapshot投票"], 180, "https://worldlibertyfinancial.com/", False),
        item("ekiden", "Ekiden (EKI)", "EKI", "DeFi/DEX", "ポイント(TGE前)", "upcoming", "medium", 400,
             "Aptos上の取引所。テストネット/メインネットの取引でXPを獲得、TGEでトークン配分の可能性(公式発表は未確認)。",
             ["取引でXP獲得", "ROI・ドローダウンも評価対象"], 0, "https://ekiden.fi/", False),
        item("kraken-sweepstakes", "Kraken Sweepstakes", "", "取引所", "キャンペーン", "active", "easy", 0,
             "10/3追加の新着キャンペーン(airdropalert掲載)。詳細は公式ページを確認。",
             ["公式ページの条件を確認"], 0, "https://airdropalert.com/farm/", False),
        item("tastyco-tasty", "TastyCo ($TASTY)", "TASTY", "その他", "エアドロップ", "active", "easy", 0,
             "10/2追加の新着エアドロップ(airdropalert掲載)。未検証のため参加前に詐欺でないか要確認。",
             ["公式ページの条件を確認"], 0, "https://airdropalert.com/farm/", False),
        item("joincare-jc", "JoinCare ($JC)", "JC", "その他", "エアドロップ", "active", "easy", 0,
             "10/1追加の新着エアドロップ(airdropalert掲載)。未検証のため要注意。",
             ["公式ページの条件を確認"], 0, "https://airdropalert.com/farm/", False),
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
