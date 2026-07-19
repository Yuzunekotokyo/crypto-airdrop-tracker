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
    """手動管理の注目エアドロップシードデータ (2026年7月時点の最新情報を反映)"""
    today = datetime.utcnow()
    return [
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 1200,
            "description": "最大手の分散型予測市場。CMOが公式にトークン+エアドロップ実施を明言。CFTC登録取引所QCX買収後の米国展開クリアが前提で2026年後半ローンチが濃厚。Hyperliquid同等(供給の約31%)のコミュニティ配分が期待されている。",
            "tasks": ["Polymarketで予測市場に参加・取引", "USDCでのポジション保有", "早期からの継続的な取引実績を積む"],
            "end_date": (today + timedelta(days=150)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/45303/small/polymarket.png",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-season2",
            "name": "Hyperliquid Season 2",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "ポイント制",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 900,
            "description": "高速オンチェーン永久先物DEX。Season 2ポイントが毎週配布されており、UI/API経由のオーガニックな取引が評価対象。第1弾エアドロップは供給の約31%をコミュニティに配分した実績あり。",
            "tasks": ["Hyperliquidで先物取引を継続", "APIを使った取引戦略の実行", "流動性提供・紹介プログラム参加"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "opensea-sea",
            "name": "OpenSea (SEA)",
            "symbol": "SEA",
            "category": "NFT",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 350,
            "description": "最大手NFTマーケットプレイス。SEAトークンの発行は公式発表済みだが正式なローンチ日は未定。過去の取引・出品実績が対象になる可能性。",
            "tasks": ["OpenSeaでのNFT売買実績を作る", "OpenSeaウォレット/アプリの利用", "公式アナウンスを継続的にチェック"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/1211/small/opensea.jpg",
            "url": "https://opensea.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "abstract-abs",
            "name": "Abstract",
            "symbol": "ABS",
            "category": "Layer2",
            "type": "テストネット/メインネット活動",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "コンシューマー・ゲーミング向けEthereum L2。オンチェーンアクティビティ(取引・ブリッジ・アプリ利用)の実績を積むことでエアドロップ対象になる可能性。",
            "tasks": ["Abstractへブリッジ", "エコシステムdApps/ゲームの利用", "継続的なオンチェーン活動"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39169/small/abstract.png",
            "url": "https://abs.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "usd-ai",
            "name": "USD.AI",
            "symbol": "USDAI",
            "category": "DeFi/AI",
            "type": "新興プロジェクト",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 250,
            "description": "AIインフラの実物資産(GPU等)を担保にしたステーブルコイン/DeFiプロトコル。2026年に急浮上した注目案件の一つ。",
            "tasks": ["プロトコルへの入金・ステーキング", "コミュニティ/紹介プログラム参加", "公式Discord・Xでの情報収集"],
            "end_date": (today + timedelta(days=75)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://usd.ai/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "backpack-bp",
            "name": "Backpack Exchange (BP)",
            "symbol": "BP",
            "category": "取引所",
            "type": "終了済み (TGE実施済)",
            "status": "ended",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "2026年3月23日にTGE実施済み。供給の25%をコミュニティに配分(24%ポイント保有者、1%Mad Lads NFT保有者)。新規エアドロップ機会としては終了。",
            "tasks": [],
            "end_date": "2026-03-23",
            "logo": "",
            "url": "https://backpack.exchange/",
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
