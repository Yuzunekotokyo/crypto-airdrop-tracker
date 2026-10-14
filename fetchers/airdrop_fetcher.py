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


def _build_seed_airdrops() -> list[dict]:
    """手動管理の注目エアドロップシードデータ (毎日のWeb調査で更新)。
    estimated_value_usd は公開情報を基にした目安であり、保証ではない。"""
    added = "2026-10-14"

    def item(id_, name, symbol, category, type_, status, difficulty, value, desc, tasks, end, url, hot):
        return {
            "id": id_, "name": name, "symbol": symbol, "category": category,
            "type": type_, "status": status, "difficulty": difficulty,
            "estimated_value_usd": value, "description": desc, "tasks": tasks,
            "end_date": end, "logo": "", "url": url, "is_hot": hot,
            "added_date": added, "source": "curated",
        }

    return [
        item("variational-var", "Variational (VAR)", "VAR", "DeFi/DEX", "ポイント",
             "active", "medium", 1000,
             "Perp DEX。VAR総供給の32%をポイント比例でエアドロップ予定。TGEは2026年Q4予定、FDV評価は約15〜18億ドルと報道。毎週150,000ポイント配布中。",
             ["Variationalで取引しポイント獲得", "週次ポイントを継続的に積み上げ"], "2026年Q4 (TGE予定)",
             "https://variational.io/", True),
        item("polymarket", "Polymarket", "", "予測市場", "未確定(公式言及あり)",
             "upcoming", "easy", 1000,
             "CMOがトークンとエアドロップの計画を公言。まずは米国向け再ローンチを優先中で、詳細は未発表。",
             ["Polymarketで継続的に予測取引", "複数マーケットへ参加", "流動性提供"], "未定",
             "https://polymarket.com/", True),
        item("kraken-ink", "Ink (INK) / Kraken Drops", "INK", "Layer2", "ポイント",
             "upcoming", "easy", 500,
             "KrakenのL2「Ink」。$INKはKraken Dropsで配布予定と公式言及。Ink PointsとKraken Proの利用実績に連動。",
             ["Ink上のdApps利用でInk Points獲得", "Kraken Proで取引"], "未定",
             "https://inkonchain.com/", True),
        item("meteora-s2", "Meteora Season 2 Claim", "MET", "DeFi/DEX", "クレーム",
             "active", "easy", 200,
             "Season 2のクレーム受付中。期限は2026年10月21日。対象ウォレットは期限前に請求が必要。",
             ["公式サイトで対象ウォレットを接続し請求"], "2026-10-21",
             "https://meteora.ag/", True),
        item("extended-ext", "Extended (EXT)", "EXT", "DeFi/DEX", "ポイント",
             "active", "medium", 600,
             "Perp DEX。EXT供給の30%を初期ポイント保有者へ配分。最終ポイント上限7,000万、週最大60万ポイント配布。TGE日未発表。",
             ["Extendedで取引", "ポイント獲得を継続"], "未定",
             "https://extended.exchange/", False),
        item("perptools", "PERPTools (PERP)", "PERP", "ツール", "ポイント",
             "active", "easy", 150,
             "Season 2実施中。ポイントはTGE時にPERPへ比例変換予定。TGE目標は2026年Q4後半。供給量・配分は未発表。",
             ["Season 2のタスクでポイント獲得"], "2026年Q4後半 (TGE目標)",
             "https://usethebitcoin.com/airdrop/perptools/", False),
        item("dawn-network", "Dawn Network", "", "インフラ", "ポイント",
             "active", "easy", 150,
             "Season 1 Bytesは9/22〜12/22。10/12時点でTGE日は未確認(2027年の可能性も報じられている)。",
             ["ノード/拡張機能を稼働しBytesを獲得"], "2026-12-22",
             "https://www.coingabbar.com/en/dawn-airdrop-season-1-ending-soon-tge-date-token-launch-2027", False),
        item("apyx", "Apyx (APYX)", "APYX", "DeFi/DEX", "ポイント",
             "active", "easy", 100,
             "Pipsキャンペーンが2026年10月までブースト延長中。ガバナンストークンAPYXは未ローンチ。",
             ["Pipsを獲得する預入/利用"], "2026年10月 (ブースト期間)",
             "https://airdropalert.com/farm/", False),
        item("tastyco", "TastyCo (TASTY)", "TASTY", "その他", "ポイント",
             "active", "easy", 50,
             "TGE前にポイントを集めた初期ユーザーへ合計10万ドル相当のTASTYをエアドロップ予定(小規模)。",
             ["ポイント獲得タスクを実施"], "未定",
             "https://airdropalert.com/farm/", False),
        item("mint-tge", "MINT", "MINT", "その他", "TGE",
             "upcoming", "easy", 100,
             "一部アグリゲータが2026年10月20日のTGEを掲載(公式未確認のため要確認)。",
             ["公式発表を確認"], "2026-10-20",
             "https://airdropalert.com/farm/", False),
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
