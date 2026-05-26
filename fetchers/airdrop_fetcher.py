"""
Airdrop情報をWeb/APIから収集するモジュール。
airdrops.io スクレイピング + キュレーテッドシードデータ (2025年版)。
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
    """airdrops.io のトップページからアクティブエアドロップを取得"""
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
        logger.info(f"airdrops.io から {len(items)} 件取得")
        return items
    except Exception as e:
        logger.warning(f"airdrops.io scrape failed: {e}")
        return []


def _scrape_earndrop_io() -> list[dict]:
    """earndrop.io からアクティブエアドロップを取得 (補助ソース)"""
    try:
        r = requests.get("https://earndrop.io/", headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        for card in soup.select(".airdrop-card, .card")[:20]:
            name_el = card.select_one("h3, h4, .title, .name")
            link_el = card.select_one("a[href]")
            if not name_el:
                continue
            items.append({
                "name": name_el.get_text(strip=True),
                "url": link_el["href"] if link_el else "https://earndrop.io/",
                "estimated_value": "不明",
                "end_date": "未定",
                "logo": "",
                "source": "earndrop.io",
            })
        logger.info(f"earndrop.io から {len(items)} 件取得")
        return items
    except Exception as e:
        logger.debug(f"earndrop.io scrape failed: {e}")
        return []


def _build_seed_airdrops() -> list[dict]:
    """2025年注目エアドロップのキュレーテッドシードデータ"""
    today = datetime.utcnow()
    return [
        {
            "id": "monad-mon",
            "name": "Monad (MON)",
            "symbol": "MON",
            "category": "Layer1",
            "type": "テストネット報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 2000,
            "description": "EVM互換高性能L1。毎秒10,000トランザクション処理可能。テストネット参加者向けエアドロップ期待度No.1。",
            "tasks": ["Monadテストネットへの参加", "Monadウォレット作成・使用", "テストネットDeFiプロトコル利用", "Discordコミュニティ参加"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/36972/small/monad.png",
            "url": "https://www.monad.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "megaeth-meth",
            "name": "MegaETH",
            "symbol": "METH",
            "category": "Layer1/EVM",
            "type": "テストネット報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 1500,
            "description": "リアルタイムEVM L1。1ms未満のブロック時間を実現。テストネット「Fluffle」参加中。",
            "tasks": ["MegaETHテストネット参加", "テストトランザクション実行", "エコシステムdApps利用", "Twitterフォロー・Discord参加"],
            "end_date": (today + timedelta(days=75)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/38516/small/megaeth.jpg",
            "url": "https://megaeth.systems/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "story-ip",
            "name": "Story Protocol (IP)",
            "symbol": "IP",
            "category": "インフラ/IP",
            "type": "エコシステム参加",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "IPブロックチェーン。知的財産権のオンチェーン管理。NFT・クリエイター向け新しいエアドロップ機会。",
            "tasks": ["Story Protocolでのアセット登録", "PIL（プログラマブルIPライセンス）の利用", "エコシステムアプリ参加"],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/41055/small/story.jpg",
            "url": "https://www.story.foundation/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "abstract-abs",
            "name": "Abstract (ABS)",
            "symbol": "ABS",
            "category": "Layer2/Consumer",
            "type": "エコシステム参加",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 600,
            "description": "Pudgy Penguins運営のConsumer向けL2。Abstract Global Wallet搭載。ゲーム・NFT・DeFi統合。",
            "tasks": ["Abstract Walletの作成", "Abstract上でのNFTミント", "Abstract対応dApps利用", "AGW（Global Wallet）使用"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/55056/small/abstract.png",
            "url": "https://abs.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "unichain-uni2",
            "name": "Unichain",
            "symbol": "UNI2",
            "category": "Layer2/DeFi",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1000,
            "description": "Uniswap公式L2チェーン（OP Stack）。Uniswap V4の本拠地。1秒ブロック確定。DEX取引でエアドロップ対象。",
            "tasks": ["Unichain上でのスワップ", "流動性提供（LP）", "Unichain bridgeの利用", "Uniswap V4ポジション作成"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/51/small/uniswap.png",
            "url": "https://unichain.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "berachain-bera",
            "name": "Berachain (BERA)",
            "symbol": "BERA",
            "category": "Layer1/DeFi",
            "type": "PoL報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 500,
            "description": "Proof of Liquidity（PoL）搭載EVM L1。BGT報酬システム。エコシステムが急速に拡大中。",
            "tasks": ["BEXでの流動性提供", "BeraBorrow・HoneySwap利用", "BGT委任・バリデータ参加", "エコシステムNFT保有"],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/35088/small/berachain.png",
            "url": "https://www.berachain.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "sonic-s",
            "name": "Sonic (S)",
            "symbol": "S",
            "category": "Layer1/DeFi",
            "type": "エコシステム参加",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "旧Fantom。Sonic rebranding後、10,000TPS以上を誇る高速EVM。Fee Monetizationプログラム参加可能。",
            "tasks": ["Sonic上でのDeFi参加", "SpookySwap・Beets等でのLP", "Fee Monetization申請", "ブリッジ利用"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/4001/small/Fantom_round.png",
            "url": "https://soniclabs.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "initia-init",
            "name": "Initia (INIT)",
            "symbol": "INIT",
            "category": "Layer1/Modular",
            "type": "テストネット報酬",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 700,
            "description": "モジュラーL1 + L2エコシステム。Cosmos SDK + MoveVM + EVM対応。テストネット「Whirlwind」フェーズ中。",
            "tasks": ["Initiaテストネット参加", "Mininitia（L2）デプロイ", "Enshrined Liquidityの利用", "ガバナンス参加"],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/37173/small/initia.jpg",
            "url": "https://initia.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-hype",
            "name": "Hyperliquid (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/Perps DEX",
            "type": "取引高報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1200,
            "description": "最速オンチェーン先物DEX。HyperEVM搭載で独自L1上のDeFiエコシステムが急拡大。Points継続中。",
            "tasks": ["Hyperliquid上での先物取引", "Vault（金庫）への流動性提供", "紹介プログラム参加", "HIP-1トークン取引"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "eigenlayer-eigen",
            "name": "EigenLayer (EIGEN)",
            "symbol": "EIGEN",
            "category": "インフラ/Restaking",
            "type": "リステーキング報酬",
            "status": "active",
            "difficulty": "hard",
            "estimated_value_usd": 900,
            "description": "Ethereumリステーキングの最大手。AVS（Actively Validated Services）参加でEIGEN報酬継続中。",
            "tasks": ["ETH/LST（stETH等）をリステーキング", "AVSへの参加・委任", "EigenDA利用プロトコル使用"],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/33751/small/eigen.png",
            "url": "https://eigenlayer.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "fuel-fuel",
            "name": "Fuel Network (FUEL)",
            "symbol": "FUEL",
            "category": "Layer2/モジュラー",
            "type": "テストネット報酬",
            "status": "active",
            "difficulty": "hard",
            "estimated_value_usd": 500,
            "description": "並列実行EVM L2。FuelVM + Sway言語。高スループットDeFi特化ロールアップ。",
            "tasks": ["Fuel Ignitionテストネット参加", "Swayで簡単なコントラクト作成", "エコシステムDeFi利用"],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/55244/small/fuel.png",
            "url": "https://fuel.network/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "movement-move",
            "name": "Movement (MOVE)",
            "symbol": "MOVE",
            "category": "Layer2/MoveVM",
            "type": "エコシステム参加",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 600,
            "description": "Move VMベースのEthereum L2。高速・低コスト・安全なスマートコントラクト。メインネット稼働中。",
            "tasks": ["MovementブリッジでETH入金", "Move上でのDeFi利用", "Move Nameサービス取得", "Discordロール取得"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
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
    scraped += _scrape_earndrop_io()

    seen_names = {a["name"].lower() for a in curated}
    new_items = []

    for s in scraped:
        name_lower = s["name"].lower().strip()
        if not name_lower or name_lower in seen_names:
            continue
        curated.append({
            "id": name_lower.replace(" ", "-")[:50],
            "name": s["name"].strip(),
            "symbol": "",
            "category": "その他",
            "type": "エアドロップ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": f"airdrops.ioより取得 — 推定報酬: {s.get('estimated_value', '不明')}",
            "tasks": [],
            "end_date": s.get("end_date", "未定"),
            "logo": s.get("logo", ""),
            "url": s.get("url", ""),
            "is_hot": False,
            "added_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "source": s.get("source", "scraped"),
        })
        new_items.append(s["name"].strip())
        seen_names.add(name_lower)

    # 注目度でソート: is_hot → estimated_value_usd
    curated.sort(key=lambda x: (not x.get("is_hot"), -x.get("estimated_value_usd", 0)))

    return curated, new_items
