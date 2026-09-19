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
    """手動管理の注目エアドロップシードデータ (2026年9月の最新情報を反映して定期的に更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 1200,
            "description": "業界最大級の予測市場プラットフォーム。トークン未発表だが$POLYと将来のエアドロップを示唆する報道が相次ぎ、2026年最注目案件の一つ。",
            "tasks": ["予測市場でのベット取引を実行", "USDC入金でウォレットを稼働", "複数マーケットへの継続的な参加"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "kraken-ink",
            "name": "Kraken Ink (INK)",
            "symbol": "INK",
            "category": "Layer2",
            "type": "ポイントプログラム",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 350,
            "description": "Kraken発のLayer2チェーン。Ink Pointsプログラム シーズン2が進行中で、2026年内のTGEが見込まれる「二重取り」案件。",
            "tasks": ["Ink Points シーズン2に参加", "Kraken Pro でのアクティビティ", "Ink上でのDeFiプロトコル利用"],
            "end_date": (today + timedelta(days=75)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://inkonchain.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "yakkamon-nft",
            "name": "Yakkamon",
            "symbol": "",
            "category": "ゲーム/NFT",
            "type": "NFTエアドロップ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 250,
            "description": "Roninチェーン上のモンスター育成ゲーム。Season 0の上位トレーナー5,000名にNFT付与、さらに10,000体のフリーミントを9月中旬に実施予定。",
            "tasks": ["Roninウォレットを準備", "Season 0でランキング上位を目指す", "9月中旬のフリーミントに参加"],
            "end_date": (today + timedelta(days=10)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://yakkamon.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "startale-fiesta",
            "name": "Startale Summer Fiesta",
            "symbol": "",
            "category": "インフラ",
            "type": "ポイントプログラム",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 200,
            "description": "Astar/Soneiumエコシステムのキャンペーン。サマーフィエスタが9月まで継続中で、オンチェーン活動に応じたポイント獲得が可能。",
            "tasks": ["Soneium上でのdApps利用", "キャンペーンクエストの達成", "コミュニティタスクへの参加"],
            "end_date": (today + timedelta(days=15)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://startale.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "megaeth-mega",
            "name": "MegaETH (MEGA)",
            "symbol": "MEGA",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "completed",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "2026年4月30日にTGE済み。Fluffle NFT保有者にはMEGA供給量の5%以上が配布された。新規の獲得機会は終了。",
            "tasks": ["配布は終了済み"],
            "end_date": "2026-04-30",
            "logo": "",
            "url": "https://megaeth.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "monad-mon",
            "name": "Monad (MON)",
            "symbol": "MON",
            "category": "Layer1",
            "type": "レトロアクティブ",
            "status": "completed",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "1.88億ドル規模のトークンセールに先立ちエアドロップを実施済み。配分の少なさにコミュニティから反発があったが、配布自体は完了。",
            "tasks": ["配布は終了済み"],
            "end_date": "2026-06-01",
            "logo": "",
            "url": "https://monad.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
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
