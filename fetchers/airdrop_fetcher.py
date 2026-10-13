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
    """手動管理の注目エアドロップシードデータ (毎日の調査で更新)。最終調査: 2026-10-13"""
    added = "2026-10-13"

    def a(id, name, symbol, category, type_, status, difficulty, value, desc, tasks, end, url, hot):
        return {
            "id": id, "name": name, "symbol": symbol, "category": category, "type": type_,
            "status": status, "difficulty": difficulty, "estimated_value_usd": value,
            "description": desc, "tasks": tasks, "end_date": end, "logo": "", "url": url,
            "is_hot": hot, "added_date": added, "source": "curated",
        }

    return [
        a("mint-mntd", "MINT (MNTD)", "MNTD", "GameFi/ベット", "ポイント/リーダーボード", "upcoming", "easy", 0,
          "Season 1: 125,000 MNTD をXPリーダーボード上位に配布。TGEは2026/10/20 (Robinhood Chain)。スナップショットはTGE直前。",
          ["MINTのカジノ/スポーツブックで合計$50以上ベット", "XPを貯めてリーダーボード入り", "公式発表のスナップショット日を確認"],
          "2026-10-20", "https://usethebitcoin.com/airdrop/mint-airdrop-guide", True),
        a("variational-var", "Variational (VAR)", "VAR", "DeFi/Perp DEX", "ポイント", "active", "medium", 0,
          "総供給の32%をポイント比例で配布予定。TGEは2026年Q4予定。",
          ["Variationalで取引・ポイント獲得", "公式のポイント条件を確認"],
          "2026-12-31", "https://variational.io/", True),
        a("perptools-perp", "PERPTools (PERP)", "PERP", "DeFi/ツール", "ポイント", "active", "easy", 0,
          "Season 2は10/2開始。Season 1ポイントはアーカイブ済みでTGE時に反映の可能性。TGEは2026年Q4後半予定。",
          ["Season 2でポイントを獲得"],
          "2026-12-31", "https://usethebitcoin.com/airdrop/perptools/", False),
        a("backpack", "Backpack Exchange", "", "取引所", "ポイント", "active", "medium", 0,
          "コミュニティに総供給の25% (ポイント保有者24%、Mad Lads NFT 1%)。Season 4ポイントを獲得中。TGE日は未確認。",
          ["Backpackで取引・ポイント獲得"],
          "未定", "https://backpack.exchange/", False),
        a("brownian-bro", "Brownian (BRO)", "BRO", "その他", "ポイント", "active", "easy", 0,
          "ポイントはTGEで変換。TGEは遅くとも2026年Q4目標 (市況次第)。変換方式は未公開。",
          ["公式でポイントを獲得"], "2026-12-31", "https://airdrops.io/latest/", False),
        a("dawn-network", "Dawn Network", "", "インフラ", "ポイント", "active", "easy", 0,
          "Season 1「Bytes」キャンペーンは2026/9/22〜12/22。トークン発行日は未確認。",
          ["Bytesを貯める"], "2026-12-22", "https://www.coingabbar.com/en/dawn-airdrop-season-1-ending-soon-tge-date-token-launch-2027", False),
        a("ink-kraken", "Ink (Kraken L2)", "", "Layer2", "ポイント", "active", "medium", 0,
          "KrakenのL2。Kraken Pro利用でInk Pointsを獲得。TGEは2026年中の見込み。",
          ["Kraken Proで取引", "Ink上でDeFi利用"], "未定", "https://inkonchain.com/", False),
        a("sonic-s-claim", "Sonic (S) 未請求分", "S", "Layer1", "請求期限", "active", "easy", 0,
          "約3,269万Sが未請求。10/15までに請求しないとバーン。対象者は急ぎ請求を。",
          ["Sonic公式ポータルで請求"], "2026-10-15", "https://airdrops.io/latest/", True),
        a("meteora-met-claim", "Meteora (MET) Season 2 LP", "MET", "DeFi/DEX", "請求期限", "active", "easy", 0,
          "Season 2 LP報酬の請求は10/21まで。",
          ["Meteora公式で請求"], "2026-10-21", "https://airdrops.io/latest/", False),
        a("pharos-pros-claim", "Pharos (PROS) 請求", "PROS", "Layer1", "請求期限", "active", "easy", 0,
          "請求ポータルは10/25に閉鎖。未請求分は財団に戻り猶予なし。",
          ["Pharos公式ポータルで請求"], "2026-10-25", "https://cryptoticker.io/en/pharos-airdrop-claim-deadline", False),
        a("usdai-flatiron", "USD.AI Flatiron Season 2", "", "DeFi", "ポイント", "active", "easy", 0,
          "Flatiron Season 2は10/14終了。",
          ["USD.AIにデポジット"], "2026-10-14", "https://airdrops.io/latest/", False),
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
