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
            "id": "monad-mon",
            "name": "Monad (MON)",
            "symbol": "MON",
            "category": "Layer1",
            "type": "テストネット報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 2000,
            "description": "EVM互換の超高速L1ブロックチェーン。10,000 TPS達成。テストネット参加者へのエアドロップ期待大。",
            "tasks": ["テストネットウォレット作成", "テスト用MONを取得(Faucet)", "テストネット上でのDeFi利用", "Discordのアクティブ参加"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/35466/small/monad.jpg",
            "url": "https://monad.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "megaeth-eth",
            "name": "MegaETH",
            "symbol": "ETH",
            "category": "Layer2",
            "type": "テストネット報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 1500,
            "description": "リアルタイムブロックチェーン。100,000 TPS以上のスループットを実現するEthereum L2。テストネット中。",
            "tasks": ["テストネットアクセス取得", "dAppsの利用", "コミュニティタスク完了"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/53756/small/megaeth.jpg",
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
            "type": "取引所トークン",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "高速オンチェーン永久先物DEX。独自L1チェーン上で動作。HLPトークンのステーキング報酬継続中。",
            "tasks": ["Hyperliquid上での先物取引", "流動性提供(HLP Vault)", "紹介プログラム参加"],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "initia-init",
            "name": "Initia (INIT)",
            "symbol": "INIT",
            "category": "Layer1",
            "type": "テストネット報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1200,
            "description": "Cosmos SDKベースのマルチVM L1。EVM・MoveVM・WasmVMをサポート。Xpリポイントプログラムで報酬獲得。",
            "tasks": ["Initia Appチェーンとのインタラクション", "Xpポイントプログラム参加", "ステーキング", "テストネット検証者"],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/38555/small/initia.jpg",
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
            "type": "流動性証明",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 600,
            "description": "Proof-of-Liquidity(PoL)を採用した高性能EVM L1。BGT(Berachain Governance Token)の報酬プログラム継続中。",
            "tasks": ["BERAをステーキング", "DEX/Lending提供でBGT獲得", "BGTをBERAにRedeem", "Honeyミントで利用"],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/35424/small/bera.png",
            "url": "https://berachain.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "fuel-fuel",
            "name": "Fuel Network (FUEL)",
            "symbol": "FUEL",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 700,
            "description": "並列処理に特化したEthereum L2。FuelVM採用で最高性能。テストネット・メインネット参加者向けエアドロップ期待。",
            "tasks": ["Fuel上でのスワップ", "流動性提供", "テストネットでのトランザクション", "Mira DEX利用"],
            "end_date": (today + timedelta(days=75)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/37228/small/fuel.jpg",
            "url": "https://fuel.network/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "eclipse-eth",
            "name": "Eclipse",
            "symbol": "ECL",
            "category": "Layer2",
            "type": "テストネット報酬",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 500,
            "description": "SolanaSVM上で動作するEthereum L2。高速・低コストを実現。メインネット立ち上げ後のエアドロップ期待。",
            "tasks": ["EclipseブリッジでETHをデポジット", "Eclipse上でのDeFi利用", "コミュニティキャンペーン参加"],
            "end_date": (today + timedelta(days=50)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/41001/small/eclipse.jpg",
            "url": "https://eclipse.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "starknet-strk2",
            "name": "Starknet (STRK) Season 2",
            "symbol": "STRK",
            "category": "Layer2",
            "type": "ポイントプログラム",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "ZK-Rollup先駆者。Season 2エアドロッププログラムが継続中。DeFiアクティビティでポイントを蓄積。",
            "tasks": ["Starknet上でのDeFi利用", "JediSwap/Nostra利用", "STRKステーキング", "毎日のオンチェーン活動"],
            "end_date": (today + timedelta(days=40)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/26433/small/starknet.png",
            "url": "https://starknet.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "kaito-kaito",
            "name": "Kaito AI (KAITO)",
            "symbol": "KAITO",
            "category": "AI/Web3",
            "type": "ソーシャル報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 900,
            "description": "Web3向けAI検索エンジン。Yapper Leaderboardでの活動に応じてKAITO報酬を獲得。SNS発信が鍵。",
            "tasks": ["Kaito Connect登録", "X(Twitter)でWeb3コンテンツ投稿", "Yapper Leaderboard上位を目指す", "毎日のエンゲージメント"],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/54456/small/kaito.jpg",
            "url": "https://kaito.ai/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "eigenlayer-s3",
            "name": "EigenLayer Season 3",
            "symbol": "EIGEN",
            "category": "インフラ",
            "type": "リステーキング",
            "status": "active",
            "difficulty": "hard",
            "estimated_value_usd": 1000,
            "description": "Ethereumリステーキングエコシステムの雄。Season 3エアドロップが開始。AVS参加者への追加報酬あり。",
            "tasks": ["ETHをリステーキング", "LST (stETH/rETH等) デポジット", "AVSへの参加・委任", "EigenDA利用"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/33751/small/eigen.png",
            "url": "https://eigenlayer.xyz/",
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
