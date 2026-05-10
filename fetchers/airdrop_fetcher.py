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
            "description": "EVM互換の高速L1チェーン。並列実行で毎秒10,000トランザクション達成。テストネット参加者へのエアドロップ期待大。",
            "tasks": ["Monadテストネットでトランザクション実行", "testnet上でのDeFi操作", "Discordコミュニティ参加・タスク完了"],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/36096/small/monad.jpg",
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
            "type": "テストネット報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 1500,
            "description": "リアルタイムブロックチェーン。1ms以下のレイテンシを実現するEthereum L2。テストネットが活発に稼働中。",
            "tasks": ["Neoテストネットでの取引", "エコシステムdApps利用", "ウォレット登録＆Discord参加"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/52736/small/megaeth.jpg",
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
            "type": "ポイント報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 3000,
            "description": "高速オンチェーン永久先物DEX。独自L1 HyperEVM上で動作。シーズン2ポイントキャンペーン進行中。",
            "tasks": ["Hyperliquid上での先物・スポット取引", "流動性Vault参加", "HLP (Hyperliquidity Provider) 参加"],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
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
            "category": "インフラ",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1200,
            "description": "IPライセンスをオンチェーン管理するL1チェーン。AI生成コンテンツのIP管理に特化。2025年注目プロジェクト。",
            "tasks": ["Story上でIPアセット登録", "ライセンス設定・取引", "PIL (Programmable IP License) 活用"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/45392/small/story.jpg",
            "url": "https://story.foundation/",
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
            "estimated_value_usd": 800,
            "description": "モジュラーL1+L2エコシステム。CosmosSDKベースで複数のMinitia (L2) を展開。メインネット間近。",
            "tasks": ["Initia testnetでバリデーター参加", "Minilayer上での取引", "エコシステムプロジェクト利用"],
            "end_date": (today + timedelta(days=40)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/46346/small/initia.jpg",
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
            "type": "PoLステーキング",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 600,
            "description": "Proof-of-Liquidity (PoL) を採用したEVM L1。BGTトークンでガバナンス参加・報酬獲得が可能。",
            "tasks": ["BEXで流動性提供", "BGTでバリデーターに委任", "エコシステムdApps (Kodiak, Berodrome) 利用"],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/35049/small/berachain.jpg",
            "url": "https://berachain.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "babylon-bbn",
            "name": "Babylon (BBN)",
            "symbol": "BBN",
            "category": "インフラ",
            "type": "BTCステーキング",
            "status": "active",
            "difficulty": "hard",
            "estimated_value_usd": 1800,
            "description": "BitcoinをPoSチェーンのセキュリティ担保に使用するプロトコル。BTCホルダーが報酬を得られる革新的仕組み。",
            "tasks": ["BTCをBabylonでステーキング", "フェーズ2キャップ枠でのステーキング", "エコシステムパートナー (Lorenzo等) 利用"],
            "end_date": (today + timedelta(days=75)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/41420/small/babylon.jpg",
            "url": "https://babylonchain.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "abstract-chain",
            "name": "Abstract Chain",
            "symbol": "ABS",
            "category": "Layer2",
            "type": "エコシステム報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 700,
            "description": "コンシューマー向けZK L2。ゲーム・NFT・エンタメに特化。Pudgy Penguinsチームが開発。",
            "tasks": ["Abstractウォレット作成・使用", "エコシステムゲーム参加", "NFTミント・取引"],
            "end_date": (today + timedelta(days=50)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/52891/small/abstract.jpg",
            "url": "https://abs.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "sonic-s",
            "name": "Sonic (S)",
            "symbol": "S",
            "category": "Layer1",
            "type": "エコシステム報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "旧Fantom。毎秒10,000tx対応の高速EVM L1に刷新。Sonic Arcadeゲームプラットフォームでポイント獲得可能。",
            "tasks": ["Sonic上でのDeFi操作 (SpookySwap等)", "Sonic Gems獲得", "ブリッジ・流動性提供"],
            "end_date": (today + timedelta(days=35)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/44362/small/sonic.jpg",
            "url": "https://soniclabs.com/",
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
            "estimated_value_usd": 900,
            "description": "Ethereumのリステーキングプロトコル。AVS (Actively Validated Services) でETHセキュリティを共有。",
            "tasks": ["ETHまたはLST (stETH/rETH) をリステーキング", "AVSオペレーターに委任", "EigenDA利用サービスを使用"],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
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
            "type": "エコシステム報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 500,
            "description": "Move VMを採用するEthereum L2。高速・低コストかつMove言語の安全性を持つ。エコシステム報酬進行中。",
            "tasks": ["Movement上でのスワップ", "流動性提供 (Meridian等)", "ブリッジ経由でのETH移動"],
            "end_date": (today + timedelta(days=55)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39619/small/MOVE_color.png",
            "url": "https://movementlabs.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "kaito-kaito",
            "name": "Kaito AI (KAITO)",
            "symbol": "KAITO",
            "category": "AI/DePIN",
            "type": "Yapperポイント",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 600,
            "description": "クリプトインテリジェンスAI。Twitter/Xでのクリプト関連投稿でYapper Scoreを獲得し報酬を得る。",
            "tasks": ["Kaito Connect でウォレット連携", "Cryptoに関するTwitter投稿 (#kaito)", "Mindshare ランキング上位維持"],
            "end_date": (today + timedelta(days=25)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/52900/small/kaito.jpg",
            "url": "https://kaito.ai/",
            "is_hot": True,
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
