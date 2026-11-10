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
    """手動管理の注目エアドロップ (2026-11-10 時点の検索結果に基づく)。
    ポイント制は必ずしもトークン配布を保証しない。公式サイトで必ず確認すること。"""
    d = "2026-11-10"

    def mk(id_, name, symbol, cat, typ, status, diff, val, desc, tasks, end, url, hot):
        return {
            "id": id_, "name": name, "symbol": symbol, "category": cat, "type": typ,
            "status": status, "difficulty": diff, "estimated_value_usd": val,
            "description": desc, "tasks": tasks, "end_date": end, "logo": "",
            "url": url, "is_hot": hot, "added_date": d, "source": "curated",
        }

    return [
        mk("aster-stage6", "Aster (ASTER) Stage 6", "ASTER", "DeFi/DEX", "クレーム受付中", "active", "easy", 0,
           "Stage6で6,400万ASTER(総供給の0.8%)を配布。10,000ポイント以上の参加者が対象。終了日はソースにより11/28〜12/4と不一致。",
           ["10,000ポイント以上を保有", "公式サイトでクレーム"], "2026-11-28", "https://www.asterdex.com/", True),
        mk("fables", "Fables (FABLES)", "FABLES", "その他", "ポイントクレーム", "active", "easy", 0,
           "ポイントのクレーム期限が11/20 23:59 UTC。期限間近。",
           ["公式サイトでポイントをクレーム"], "2026-11-20", "", True),
        mk("doppler-xdp", "Doppler Finance (XDP)", "XDP", "DeFi", "ジェネシスエアドロップ", "active", "easy", 0,
           "Genesis Airdropは11/28終了。2026/7/30以前にBaseアドレスを登録済みのユーザーのみ対象(新規参加不可)。",
           ["対象アドレスでクレーム"], "2026-11-28", "", False),
        mk("standx-dusd", "StandX (DUSD)", "DUSD", "DeFi", "クレーム受付中", "active", "easy", 0,
           "11/2からクレーム開放、12/31まで。",
           ["公式サイトでクレーム"], "2026-12-31", "", False),
        mk("dango-dng", "Dango (DNG)", "DNG", "DeFi", "ポイントプログラム", "upcoming", "medium", 0,
           "ポイントプログラム実施中、TGEは2026年Q4予定(宣伝系ソースのため要注意)。",
           ["ポイントプログラムに参加"], "未定", "", False),
        mk("opensea-sea", "OpenSea (SEA)", "SEA", "NFT", "ポイント/将来配布", "upcoming", "medium", 0,
           "SEAトークンは公式に確認済みで供給の50%をコミュニティへ。ただしローンチは複数回延期され日程未定。",
           ["OpenSeaでの取引・利用"], "未定", "https://opensea.io/", True),
        mk("polymarket", "Polymarket", "", "予測市場", "未発表", "upcoming", "medium", 0,
           "CMOがトークンとエアドロップを確認済みだが、時期・条件は未公開。まず米国再開を優先。",
           ["Polymarketでの取引を継続"], "未定", "https://polymarket.com/", True),
        mk("metamask-mask", "MetaMask (MASK)", "MASK", "ウォレット", "未確定", "upcoming", "medium", 0,
           "トークンは言及済みだがスナップショット・クレーム方法は未確認。",
           ["MetaMaskの利用(Swaps/Perps等)"], "未定", "https://metamask.io/", False),
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
