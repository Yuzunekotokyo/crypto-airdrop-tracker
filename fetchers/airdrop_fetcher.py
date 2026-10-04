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
    """手動管理の注目エアドロップシードデータ (定期的に更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "トレーディング報酬",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 1000,
            "description": "CMOがPOLYトークンとエアドロップを公式に確認。米国再ローンチ後にトークン発行予定。取引量・継続的な取引活動が配分に影響(推定額は未確定)。",
            "tasks": ["予測市場で継続的に取引", "取引量と市場の多様性を確保", "スナップショット告知を監視"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "backpack-back",
            "name": "Backpack (BACK)",
            "symbol": "BACK",
            "category": "取引所",
            "type": "ポイントプログラム",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "TGE確定済み。ポイント保有者に供給量の約24%を配分。Season 4が進行中で、毎週の継続的な取引が評価される。",
            "tasks": ["Backpackで毎週取引", "ポイントを継続的に獲得", "紹介プログラム参加"],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://backpack.exchange/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "ウォレット",
            "type": "ポイントプログラム",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 500,
            "description": "MetaMask Rewardsのポイントが将来のトークン配分に連動。Consensys CEOがMASKトークン発行を示唆。",
            "tasks": ["MetaMask Rewardsに参加", "スワップ・ブリッジ・パープ取引を利用", "ポイントを継続獲得"],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://metamask.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "opensea-sea",
            "name": "OpenSea Foundation (SEA)",
            "symbol": "SEA",
            "category": "NFT",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "OpenSea関連の非営利団体OpenSea Foundationがトークンを発行予定と公式に確認。",
            "tasks": ["OpenSeaで取引・購入", "NFTの保有・出品", "公式発表を監視"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://opensea.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "kraken-ink",
            "name": "Kraken Ink (INK)",
            "symbol": "INK",
            "category": "L2",
            "type": "Krakenドロップ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "INKはKraken Drops経由で配布予定とKrakenが発表。",
            "tasks": ["Krakenアカウント作成", "Kraken Dropsに参加", "Ink上のdAppを利用"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://www.inkonchain.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "ekiden",
            "name": "Ekiden",
            "symbol": "EKIDEN",
            "category": "DeFi/DEX",
            "type": "ポイントプログラム",
            "status": "upcoming",
            "difficulty": "hard",
            "estimated_value_usd": 600,
            "description": "メインネットローンチに合わせた報酬プログラムを確認。取引でポイントを獲得。テストネット上位トレーダーは招待制でアーリーアクセス。",
            "tasks": ["テストネットで取引", "招待コードを入手", "メインネットで取引ポイントを獲得"],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://ekiden.fi/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "concrete",
            "name": "Concrete",
            "symbol": "CONCRETE",
            "category": "DeFi/利回り",
            "type": "ポイントプログラム",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 250,
            "description": "キャンペーンが延長され、2026年10月までブースト報酬を提供中。",
            "tasks": ["Concreteにデポジット", "ブースト期間中に参加"],
            "end_date": (today + timedelta(days=27)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://concrete.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "lisk",
            "name": "Lisk (LSK)",
            "symbol": "LSK",
            "category": "Layer2",
            "type": "ポイントキャンペーン",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 150,
            "description": "約1,500万ドル相当のLSK報酬プール。タスク完了で獲得したポイントがLSKに変換される。",
            "tasks": ["Lisk上のタスクを完了", "ポイントを獲得"],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://lisk.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-token",
            "name": "Base (未確定)",
            "symbol": "BASE",
            "category": "Layer2",
            "type": "投機的",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 1000,
            "description": "Coinbase L2。トークンの公式発表はまだないが、2026年の注目候補。エアドロップがあれば大型の可能性(投機的)。",
            "tasks": ["Base上でdAppを利用", "複数アプリで継続的に取引", "公式発表を監視"],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://base.org/",
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
