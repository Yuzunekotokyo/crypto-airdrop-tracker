"""
Airdrop情報をWeb/APIから収集するモジュール。
airdrops.io、DappRadar、CoinGeckoトレンドを組み合わせて使用。
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
        # 複数のセレクタを試みる
        cards = (
            soup.select(".airdrop-item")
            or soup.select(".airdrop-card")
            or soup.select("article.airdrop")
            or soup.select(".post-item")
        )

        for card in cards[:30]:
            name_el = (
                card.select_one(".airdrop-title")
                or card.select_one("h3")
                or card.select_one("h2")
                or card.select_one(".title")
            )
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
        logger.info(f"airdrops.io: {len(items)}件取得")
        return items
    except Exception as e:
        logger.warning(f"airdrops.io scrape failed: {e}")
        return []


def _scrape_coingecko_airdrop_coins() -> list[dict]:
    """CoinGecko新着コインからエアドロップ関連を検出"""
    try:
        new_coins = get_new_coins()
        airdrop_keywords = ["airdrop", "drop", "claim", "genesis", "launch", "community"]
        items = []
        for coin in new_coins[:30]:
            name = coin.get("name", "").lower()
            if any(k in name for k in airdrop_keywords):
                items.append({
                    "name": coin.get("name", ""),
                    "url": f"https://www.coingecko.com/en/coins/{coin.get('id', '')}",
                    "estimated_value": "新規上場",
                    "end_date": "未定",
                    "logo": "",
                    "source": "coingecko-new",
                })
        return items
    except Exception as e:
        logger.warning(f"CoinGecko new coins fetch failed: {e}")
        return []


def _build_seed_airdrops() -> list[dict]:
    """注目エアドロップシードデータ (2025-2026年版)"""
    today = datetime.utcnow()
    return [
        {
            "id": "berachain-bera",
            "name": "Berachain (BERA)",
            "symbol": "BERA",
            "category": "Layer1",
            "type": "メインネット移行",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1200,
            "description": "独自コンセンサス機構PoLを持つEVM互換L1。DeFiネイティブチェーンとして急成長中。テストネット参加者へのエアドロップ実績あり。",
            "tasks": ["BGTをステーキング", "BerachainエコシステムのdApps利用", "流動性プロビジョニング"],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/32638/small/bera.png",
            "url": "https://berachain.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "monad-mon",
            "name": "Monad (MON)",
            "symbol": "MON",
            "category": "Layer1",
            "type": "テストネット",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 2000,
            "description": "EVM互換の超高速L1。10,000 TPS以上を実現。テストネット参加者向けの大型エアドロップが期待されている。",
            "tasks": ["テストネットウォレット登録", "テストトランザクション実行", "Discordコミュニティ参加", "テストネットdApps利用"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/35191/small/monad.jpg",
            "url": "https://monad.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "story-protocol-ip",
            "name": "Story Protocol (IP)",
            "symbol": "IP",
            "category": "インフラ",
            "type": "IPライセンス",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "IPライセンスをオンチェーン化するL1プロトコル。AIとクリエイターエコノミーに特化。",
            "tasks": ["IPアセット登録", "ライセンス設定", "コミュニティ参加"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39551/small/story.jpg",
            "url": "https://story.foundation/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-hype",
            "name": "Hyperliquid (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "取引所トークン",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1000,
            "description": "高速オンチェーン永久先物DEX。独自L1チェーン上で動作。取引量によるポイント報酬。",
            "tasks": ["Hyperliquid上での先物取引", "流動性提供", "紹介プログラム参加"],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "layerzero-zro",
            "name": "LayerZero (ZRO)",
            "symbol": "ZRO",
            "category": "インフラ",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 500,
            "description": "クロスチェーンメッセージングプロトコル。ブリッジ・DeFi利用者向けエアドロップ。",
            "tasks": ["Stargate経由でブリッジを実行", "複数チェーンでのトランザクション", "LayerZero対応dApps利用"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/28206/small/ftxG9_TJ_400x400.jpeg",
            "url": "https://layerzero.network/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "scroll-scr",
            "name": "Scroll (SCR)",
            "symbol": "SCR",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "EVM互換ZK-Rollup。Ethereum L2でのトランザクション実績でエアドロップ獲得可能。",
            "tasks": ["ScrollネットワークへETHブリッジ", "Scroll上でのDeFi利用", "複数週にわたるアクティビティ"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/25734/small/scroll.png",
            "url": "https://scroll.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "eigenlayer-eigen",
            "name": "EigenLayer (EIGEN)",
            "symbol": "EIGEN",
            "category": "インフラ",
            "type": "リステーキング",
            "status": "active",
            "difficulty": "hard",
            "estimated_value_usd": 800,
            "description": "Ethereumのリステーキングプロトコル。ETHをステーキングし追加報酬を獲得。",
            "tasks": ["ETHをリステーキング", "LST (stETH等) をデポジット", "AVSへの参加"],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/33751/small/eigen.png",
            "url": "https://eigenlayer.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "movement-move",
            "name": "Movement (MOVE)",
            "symbol": "MOVE",
            "category": "Layer2",
            "type": "新規上場",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "Move VMを使用するEthereum L2。高速・低コストトランザクション。テストネット参加者向けエアドロップ済み。",
            "tasks": ["エコシステム利用継続", "流動性提供", "Discordコミュニティ参加"],
            "end_date": (today + timedelta(days=20)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39619/small/MOVE_color.png",
            "url": "https://movementlabs.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-ecosystem",
            "name": "Base エコシステム",
            "symbol": "",
            "category": "Layer2",
            "type": "エコシステム",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 600,
            "description": "CoinbaseのL2 Base上の各種dAppsでのエアドロップ。Aerodrome、Virtuals Protocolなど多数のプロジェクトが参加予定。",
            "tasks": ["Base上でのDeFi利用", "Aerodrome流動性提供", "複数のdAppsを利用"],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/asset_platforms/images/131/small/base-network.png",
            "url": "https://base.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "abstract-abs",
            "name": "Abstract (ABS)",
            "symbol": "ABS",
            "category": "Layer2",
            "type": "コンシューマーL2",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 500,
            "description": "ZK技術を用いたコンシューマー向けL2。NFT・ゲームに特化。ウォレット作成だけでエアドロップ対象になる場合あり。",
            "tasks": ["Abstract Global Wallet作成", "コンシューマーdApps利用", "NFT mint参加"],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/35012/small/abstract.jpg",
            "url": "https://abs.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
    ]


def _auto_mark_hot(airdrops: list[dict]) -> list[dict]:
    """推定価値が高い場合や新規追加案件を自動でホット判定"""
    for a in airdrops:
        if a.get("estimated_value_usd", 0) >= 800:
            a["is_hot"] = True
        elif a.get("source") == "airdrops.io" and not a.get("is_hot"):
            pass  # スクレイプ案件はデフォルトでホットにしない
    return airdrops


def fetch_all_airdrops() -> tuple[list[dict], list[str]]:
    """
    全ソースからエアドロップデータを収集し、変更点リストと共に返す。
    Returns: (airdrops_list, new_items_names)
    """
    curated = _build_seed_airdrops()
    scraped = _scrape_airdrops_io()
    cg_new = _scrape_coingecko_airdrop_coins()

    seen_names = {a["name"].lower() for a in curated}
    new_items = []

    for s in scraped + cg_new:
        if s["name"].lower() not in seen_names:
            curated.append({
                "id": s["name"].lower().replace(" ", "-").replace("(", "").replace(")", ""),
                "name": s["name"],
                "symbol": "",
                "category": "その他",
                "type": "エアドロップ",
                "status": "active",
                "difficulty": "easy",
                "estimated_value_usd": 0,
                "description": f"{s['source']}より取得: {s.get('estimated_value', '')}",
                "tasks": [],
                "end_date": s.get("end_date", "未定"),
                "logo": s.get("logo", ""),
                "url": s.get("url", ""),
                "is_hot": False,
                "added_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "source": s["source"],
            })
            new_items.append(s["name"])
            seen_names.add(s["name"].lower())

    curated = _auto_mark_hot(curated)

    # 注目度でソート: is_hot → estimated_value_usd
    curated.sort(key=lambda x: (not x.get("is_hot"), -x.get("estimated_value_usd", 0)))

    return curated, new_items
