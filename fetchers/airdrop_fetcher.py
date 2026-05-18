"""
Airdrop情報をWeb/APIから収集するモジュール。
airdrops.ioスクレイピング + 厳選シードデータ + CoinGecko新着コインを統合。
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
    """厳選エアドロップシードデータ (2025-2026年注目案件)"""
    today = datetime.utcnow()
    return [
        {
            "id": "monad-monad",
            "name": "Monad",
            "symbol": "MONAD",
            "category": "Layer1",
            "type": "テストネット/レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 2000,
            "description": "EVM互換の並列処理L1チェーン。超高速・低コストで注目度No.1。テストネット参加者にエアドロップ予定。",
            "tasks": ["テストネットfaucetからトークン取得", "テストネット上でトランザクション実行", "Discordでの認証・ロール取得", "MonadエコシステムdApps利用"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/35618/small/monad.jpg",
            "url": "https://monad.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "megaeth-meth",
            "name": "MegaETH",
            "symbol": "METH",
            "category": "Layer2",
            "type": "テストネット/レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 1500,
            "description": "毎秒100,000トランザクションを目指すEthereum L2。リアルタイムブロックチェーン。テストネット活発中。",
            "tasks": ["テストネット参加・ウォレット接続", "テスト用ETH取得・送金", "MegaETH上のdApps利用", "コミュニティ活動"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/38043/small/ZKTokenBlack.png",
            "url": "https://megaeth.systems/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "story-protocol-ip",
            "name": "Story Protocol (IP)",
            "symbol": "IP",
            "category": "インフラ/IP",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "知的財産をオンチェーンで管理するL1ブロックチェーン。a16zが出資する注目プロジェクト。",
            "tasks": ["Story上にIPAsset登録", "ライセンストークン取得", "IPをリミックス・派生作品作成", "ウォレット接続・Odyssey参加"],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/37452/small/story.png",
            "url": "https://www.story.foundation/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-hype",
            "name": "Hyperliquid (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "取引量報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1200,
            "description": "高速オンチェーン永久先物DEX。独自L1チェーン上で動作。取引量に応じたポイント報酬継続中。",
            "tasks": ["Hyperliquid上での先物取引", "現物取引での流動性提供", "紹介プログラム参加", "HLPへの流動性提供"],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "babylon-baby",
            "name": "Babylon Chain (BABY)",
            "symbol": "BABY",
            "category": "インフラ/Bitcoin",
            "type": "ステーキング報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 900,
            "description": "BitcoinをPoSチェーンのステーキングに活用するプロトコル。BTCホルダー向けの新収益源。",
            "tasks": ["BTCをBabylonでステーキング", "ステーキングポイント蓄積", "パートナーチェーンへの参加", "Babylon Capsule取得"],
            "end_date": (today + timedelta(days=80)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/36181/small/babylon.png",
            "url": "https://babylonchain.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "initia-init",
            "name": "Initia (INIT)",
            "symbol": "INIT",
            "category": "Layer1/L2エコシステム",
            "type": "テストネット/ポイント",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 600,
            "description": "相互接続されたL2群を持つL1ブロックチェーン。Binance Labsが出資。Celestia技術採用。",
            "tasks": ["テストネット参加・DeFi利用", "Initia上でのスワップ・流動性提供", "バリデータ参加またはデリゲート", "Echelon/BlackwingなどエコシステムdApps利用"],
            "end_date": (today + timedelta(days=40)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/38506/small/Initia.png",
            "url": "https://initia.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "symbiotic-restaking",
            "name": "Symbiotic",
            "symbol": "SYM",
            "category": "インフラ/リステーキング",
            "type": "リステーキング報酬",
            "status": "active",
            "difficulty": "hard",
            "estimated_value_usd": 700,
            "description": "Paradigm出資のリステーキングプロトコル。EigenLayerの競合として急成長中。",
            "tasks": ["stETH/wstETHをデポジット", "wBTCまたはETHをステーキング", "ネットワークへの参加", "ポイント蓄積"],
            "end_date": (today + timedelta(days=100)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/38748/small/symbiotic.png",
            "url": "https://symbiotic.fi/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "eigenlayer-eigen",
            "name": "EigenLayer (EIGEN)",
            "symbol": "EIGEN",
            "category": "インフラ/リステーキング",
            "type": "追加リステーキング報酬",
            "status": "active",
            "difficulty": "hard",
            "estimated_value_usd": 500,
            "description": "Ethereumのリステーキングプロトコル。ETHをステーキングし複数プロトコルのセキュリティを担保。",
            "tasks": ["ETHをリステーキング", "LST (stETH等) をデポジット", "AVSへの参加・デリゲート", "EigenDA利用"],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/33751/small/eigen.png",
            "url": "https://eigenlayer.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "ink-network",
            "name": "Ink Network",
            "symbol": "INK",
            "category": "Layer2",
            "type": "テストネット/レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "Krakenが開発するOP StackベースのEthereum L2。DeFi特化チェーン。",
            "tasks": ["Inkブリッジ経由でETH転送", "Ink上でのDeFi活動", "公式dApps利用", "コミュニティポイント取得"],
            "end_date": (today + timedelta(days=50)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39741/small/ink.png",
            "url": "https://inkonchain.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "abstract-chain-abs",
            "name": "Abstract Chain (ABS)",
            "symbol": "ABS",
            "category": "Layer2",
            "type": "コンシューマー向けL2",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 350,
            "description": "ZKsync技術基盤のコンシューマー向けL2。NFT・ゲーム・ソーシャルに特化。",
            "tasks": ["Abstractウォレット作成", "Abstract上でのNFT購入/Mint", "ゲームdApps参加", "Abstractパスポート取得"],
            "end_date": (today + timedelta(days=35)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39783/small/abstract.png",
            "url": "https://abs.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "scroll-scr",
            "name": "Scroll (SCR)",
            "symbol": "SCR",
            "category": "Layer2",
            "type": "レトロアクティブ継続",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "EVM互換ZK-Rollup。Ethereum L2でのトランザクション実績でエアドロップ継続中。",
            "tasks": ["ScrollネットワークへETHブリッジ", "Scroll上でのDeFi利用", "複数週にわたるアクティビティ", "Scroll Canvas NFT取得"],
            "end_date": (today + timedelta(days=70)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/25734/small/scroll.png",
            "url": "https://scroll.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "layerzero-zro",
            "name": "LayerZero (ZRO) S2",
            "symbol": "ZRO",
            "category": "インフラ",
            "type": "シーズン2レトロアクティブ",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 300,
            "description": "クロスチェーンメッセージングプロトコル。シーズン2エアドロップに向けたアクティビティ継続中。",
            "tasks": ["Stargate経由でブリッジを実行", "複数チェーンでのトランザクション", "LayerZero対応dApps (STG, CAKE等) 利用"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/28206/small/ftxG9_TJ_400x400.jpeg",
            "url": "https://layerzero.network/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
    ]


def _detect_hot_new_coins(new_coins: list[dict]) -> list[dict]:
    """CoinGeckoの新着コインからエアドロップ候補を検出"""
    candidates = []
    known_keywords = ["airdrop", "drop", "reward", "points", "testnet"]
    for coin in new_coins[:10]:
        name_lower = coin.get("name", "").lower()
        symbol_lower = coin.get("symbol", "").lower()
        if any(kw in name_lower or kw in symbol_lower for kw in known_keywords):
            candidates.append({
                "id": f"cgecko-{coin.get('id', 'unknown')}",
                "name": coin.get("name", "Unknown"),
                "symbol": coin.get("symbol", "").upper(),
                "category": "新着コイン",
                "type": "CoinGecko新着",
                "status": "active",
                "difficulty": "easy",
                "estimated_value_usd": 0,
                "description": f"CoinGeckoに新規上場。エアドロップの可能性があります。",
                "tasks": ["詳細を調査", "公式サイト確認"],
                "end_date": "未定",
                "logo": "",
                "url": f"https://www.coingecko.com/en/coins/{coin.get('id', '')}",
                "is_hot": False,
                "added_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "source": "coingecko_new",
            })
    return candidates


def fetch_all_airdrops() -> tuple[list[dict], list[str]]:
    """
    全ソースからエアドロップデータを収集し、変更点リストと共に返す。
    Returns: (airdrops_list, new_items_names)
    """
    curated = _build_seed_airdrops()
    scraped = _scrape_airdrops_io()
    new_coins = get_new_coins()

    seen_names = {a["name"].lower() for a in curated}
    new_items = []

    # airdrops.ioスクレイピング結果を統合
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

    # CoinGecko新着コイン候補を統合
    cg_candidates = _detect_hot_new_coins(new_coins)
    for coin in cg_candidates:
        if coin["name"].lower() not in seen_names:
            curated.append(coin)
            new_items.append(f"{coin['name']} (新規上場)")
            seen_names.add(coin["name"].lower())

    # 注目度でソート: is_hot → estimated_value_usd
    curated.sort(key=lambda x: (not x.get("is_hot"), -x.get("estimated_value_usd", 0)))

    return curated, new_items
