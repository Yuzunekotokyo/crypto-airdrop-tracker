"""
Airdrop情報をWeb/APIから収集するモジュール。
airdrops.ioのパブリックページとCoinGeckoトレンドを組み合わせて使用。
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
    """手動管理の注目エアドロップシードデータ (2026年最新版)"""
    today = datetime.utcnow()
    return [
        {
            "id": "monad-mon",
            "name": "Monad (MON)",
            "symbol": "MON",
            "category": "Layer1",
            "type": "テストネット/メインネット",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 2000,
            "description": "EVM互換の超高速L1ブロックチェーン。10,000 TPS以上を実現。テストネット参加者へのエアドロップ期待大。",
            "tasks": ["Monadテストネットでトランザクション実行", "Monad公式Discord参加", "Monad上のdApps利用", "テストネットNFTミント"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/35137/small/monad.png",
            "url": "https://monad.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "megaeth",
            "name": "MegaETH",
            "symbol": "MEGA",
            "category": "Layer2",
            "type": "テストネット",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 1500,
            "description": "Ethereumの超高性能L2。100,000 TPS超のリアルタイムブロックチェーン。テストネット活動でエアドロップ獲得可能。",
            "tasks": ["MegaETHテストネット参加", "テストネットトークン取得・利用", "エコシステムdApps利用", "コミュニティイベント参加"],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39233/small/megaeth.png",
            "url": "https://megaeth.systems/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-hype",
            "name": "Hyperliquid (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "取引高報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1200,
            "description": "高速オンチェーン永久先物DEX。HyperBFT独自L1で動作。ポイントプログラムが継続中。",
            "tasks": ["Hyperliquid上での先物取引", "流動性提供 (HLP Vault)", "紹介プログラム参加", "一定取引量の達成"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "story-protocol-ip",
            "name": "Story Protocol (IP)",
            "symbol": "IP",
            "category": "インフラ/IP",
            "type": "エコシステム報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "IPチェーン。知的財産(IP)をオンチェーンで管理・収益化するL1。エコシステム参加者に報酬。",
            "tasks": ["Story上でIP登録", "IPFi参加", "エコシステムdApps利用", "コミュニティ貢献"],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/35097/small/story.jpg",
            "url": "https://storyprotocol.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "initia",
            "name": "Initia (INIT)",
            "symbol": "INIT",
            "category": "Layer1/マルチチェーン",
            "type": "インセンティブテストネット",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 600,
            "description": "マルチチェーンアプリケーションプラットフォーム。Cosmos SDK + Move/EVM/WASM対応。インセンティブテストネット実施中。",
            "tasks": ["Initiascanでバリデータノード確認", "テストネットトランザクション", "Initia上のアプリ利用", "ミントページでのNFT獲得"],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/37262/small/initia.jpg",
            "url": "https://initia.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "berachain-bera",
            "name": "Berachain (BERA)",
            "symbol": "BERA",
            "category": "Layer1",
            "type": "流動性証明 (PoL)",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 500,
            "description": "Proof of Liquidity (PoL) 独自コンセンサスを持つEVM互換L1。BGTガバナンストークンでエコシステム報酬。",
            "tasks": ["BerachainでBGTステーキング", "BEX (DEX) での流動性提供", "Honey (ステーブルコイン) ミント", "バリデータへの委任"],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/35316/small/bera.png",
            "url": "https://berachain.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "unichain-uni",
            "name": "Unichain",
            "symbol": "UNI",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 700,
            "description": "Uniswapが開発するOptimism SuperchainベースのL2。UNIトークン保有者・利用者向けのエアドロップ期待。",
            "tasks": ["Unichain上でスワップ実行", "Unichain Bridgeで資金移動", "UniswapのL2流動性提供", "UNIトークン保有"],
            "end_date": (today + timedelta(days=75)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/12504/small/uni.jpg",
            "url": "https://unichain.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "linea-linea",
            "name": "Linea",
            "symbol": "LINEA",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "ConsenSys開発のzkEVM L2。MetaMask連携で利用しやすい。トークン未発行でエアドロップ期待。",
            "tasks": ["Linea上でブリッジ", "LineaのDeFiプロトコル利用", "Voyage NFT獲得", "Linea Park参加"],
            "end_date": (today + timedelta(days=50)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/31113/small/linea.jpg",
            "url": "https://linea.build/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "babylon-baby",
            "name": "Babylon (BABY)",
            "symbol": "BABY",
            "category": "インフラ/Bitcoin",
            "type": "BTCステーキング",
            "status": "active",
            "difficulty": "hard",
            "estimated_value_usd": 900,
            "description": "BitcoinをPoSネットワークのセキュリティに活用するプロトコル。BTCステーキングで報酬獲得。",
            "tasks": ["BTCをBabylonにステーキング", "ステーキング期間の維持", "対象Finality Provider選択"],
            "end_date": (today + timedelta(days=200)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/36082/small/babylon.jpg",
            "url": "https://babylonchain.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "eclipse-eth",
            "name": "Eclipse",
            "symbol": "ECL",
            "category": "Layer2/SVM",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 550,
            "description": "EthereumをDA層、SolanaをVM、Celestiaをモジュラーとして使うL2。高スループットEVM互換。",
            "tasks": ["Eclipseへのブリッジ", "Eclipse上のdApps利用", "Turboタップ参加", "コミュニティイベント"],
            "end_date": (today + timedelta(days=40)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/36891/small/eclipse.jpg",
            "url": "https://eclipse.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "abstract-abs",
            "name": "Abstract (ABS)",
            "symbol": "ABS",
            "category": "Layer2/コンシューマー",
            "type": "エコシステム参加",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 350,
            "description": "コンシューマー向けzkSync EVM L2。ゲーム・NFT・ソーシャルに特化。ネイティブアカウント抽象化。",
            "tasks": ["Abstractウォレット作成", "Abstract上でNFTミント", "エコシステムゲーム参加", "AGWアカウント設定"],
            "end_date": (today + timedelta(days=55)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/38841/small/abstract.jpg",
            "url": "https://abs.xyz/",
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
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "Move VMを使用するEthereum L2。高速・低コストトランザクション。継続的なエコシステム報酬。",
            "tasks": ["Movement上でのブリッジ", "MOVEステーキング参加", "Move上のdApps利用", "コミュニティイベント参加"],
            "end_date": (today + timedelta(days=100)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39619/small/MOVE_color.png",
            "url": "https://movementlabs.xyz/",
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
