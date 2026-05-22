"""
Airdrop情報をWeb/APIから収集するモジュール。
airdrops.ioスクレイピング + 手動管理シードデータ。
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
    """2025年最新版・注目エアドロップシードデータ"""
    today = datetime.utcnow()
    return [
        {
            "id": "berachain-bera",
            "name": "Berachain (BERA)",
            "symbol": "BERA",
            "category": "Layer1",
            "type": "テストネット報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 2000,
            "description": "独自のPoL(Proof-of-Liquidity)コンセンサスを持つEVM互換L1。テストネットbArtioでの活動でBGT/BERAを獲得可能。DeFi特化設計でTVL急成長中。",
            "tasks": [
                "Berachain bArtioテストネットに参加",
                "Bex DEXで流動性提供",
                "Honeyswapでスワップ実行",
                "BGT (Berachain Governance Token) をステーキング",
                "Discordロールを取得",
            ],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/31921/small/bera.png",
            "url": "https://berachain.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "monad-mon",
            "name": "Monad",
            "symbol": "MON",
            "category": "Layer1",
            "type": "テストネット報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 3000,
            "description": "EVM互換の超高速L1。10,000 TPS達成、並列実行アーキテクチャ。テストネット参加者向け大型エアドロップが期待される。コミュニティが非常に活発。",
            "tasks": [
                "Monad Testnetに参加",
                "テストネットトランザクションを多数実行",
                "Monad公式Discordに参加",
                "Monad対応dAppsを利用",
                "NFTをMint",
            ],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/35572/small/monad.jpg",
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
            "description": "リアルタイムブロックチェーン標榜のEthereum L2。100,000+ TPS目標、1msのサブセコンドレイテンシ。テストネット中でNFT/トランザクション活動が重要。",
            "tasks": [
                "MegaETHテストネットに接続",
                "テストネットETHをBridge",
                "MegaETH上でNFTをMint",
                "公式Discordに参加してロールを取得",
            ],
            "end_date": (today + timedelta(days=40)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/42680/small/megaeth.jpg",
            "url": "https://megaeth.systems/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "story-protocol-ip",
            "name": "Story Protocol (IP)",
            "symbol": "IP",
            "category": "インフラ",
            "type": "エコシステム報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "IPをオンチェーン管理するL1ブロックチェーン。AI×IPの融合で注目。a16z等から大型調達済み。Odysseyキャンペーンに参加でポイント獲得。",
            "tasks": [
                "Story Odysseyキャンペーンに参加",
                "IP (知的財産) をNFTとして登録",
                "PIL (Programmable IP License) を設定",
                "コミュニティ活動に参加",
            ],
            "end_date": (today + timedelta(days=55)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39386/small/story.jpg",
            "url": "https://storyprotocol.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "initia",
            "name": "Initia",
            "symbol": "INIT",
            "category": "Layer1",
            "type": "テストネット報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1200,
            "description": "複数のVM (EVM, MoveVM, WasmVM) をサポートするマルチVM L1。Cosmos SDK上に構築。Binance Labs等から投資受入済。",
            "tasks": [
                "Initiatestnetに参加",
                "Initia上でスワップ・ブリッジ",
                "Minituiaバリデーターに委任",
                "公式クエストを完了",
            ],
            "end_date": (today + timedelta(days=70)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/40152/small/initia.jpg",
            "url": "https://initia.xyz/",
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
            "description": "高速オンチェーン永久先物DEX。独自L1チェーン上で動作。取引量によるポイント報酬。既にトークン上場済みで追加報酬が期待される。",
            "tasks": [
                "Hyperliquid上での先物取引",
                "流動性提供 (HLP Vault)",
                "紹介プログラム参加",
                "Hyperps (Spot DEX) の利用",
            ],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "abstract-abs",
            "name": "Abstract (ABS)",
            "symbol": "ABS",
            "category": "Layer2",
            "type": "ゲーミング/NFT",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 500,
            "description": "ゲーム・NFT特化のEthereum L2。zkSyncエコシステム上に構築。Account Abstraction標準採用でUX優秀。ゲームコミュニティへの展開中。",
            "tasks": [
                "Abstract上でNFTをMint",
                "Abstract対応ゲームをプレイ",
                "Abstractウォレットを作成・利用",
                "公式クエスト完了",
            ],
            "end_date": (today + timedelta(days=35)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/54372/small/abs.jpg",
            "url": "https://abs.xyz/",
            "is_hot": True,
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
            "difficulty": "hard",
            "estimated_value_usd": 600,
            "description": "並列実行UTXOモデルを採用するEthereum L2。Sway言語での開発。testnet v2でのアクティビティが評価基準。",
            "tasks": [
                "Fuel testnet v2に参加",
                "SwayでのSmart Contract操作",
                "Spark DEXでの取引",
                "長期的なアクティビティを継続",
            ],
            "end_date": (today + timedelta(days=80)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/37617/small/fuel.jpg",
            "url": "https://fuel.network/",
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
            "description": "Ethereumのリステーキングプロトコル。ETHをステーキングし追加報酬を獲得。Season 2報酬分配が継続中。AVS参加で追加収益。",
            "tasks": [
                "ETHをリステーキング",
                "LST (stETH等) をデポジット",
                "AVS (Actively Validated Service) への参加",
                "EigenDA利用アプリの使用",
            ],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/33751/small/eigen.png",
            "url": "https://eigenlayer.xyz/",
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
            "description": "EVM互換ZK-Rollup。Ethereum L2でのトランザクション実績でエアドロップ獲得可能。Season 2報酬プログラム継続中。",
            "tasks": [
                "ScrollネットワークへETHブリッジ",
                "Scroll上でのDeFi利用 (Ambient, Nuri等)",
                "複数週にわたるアクティビティ継続",
                "Scroll公式dAppsを利用",
            ],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/25734/small/scroll.png",
            "url": "https://scroll.io/",
            "is_hot": False,
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
            "description": "クロスチェーンメッセージングプロトコル。ブリッジ・DeFi利用者向けエアドロップ。Season 2開始でポイントが積算中。",
            "tasks": [
                "Stargate経由でブリッジを実行",
                "複数チェーンでのトランザクション",
                "LayerZero対応dApps利用",
                "長期・多チェーンでのアクティビティ",
            ],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/28206/small/ftxG9_TJ_400x400.jpeg",
            "url": "https://layerzero.network/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "linea-lin",
            "name": "Linea",
            "symbol": "LIN",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "ConsenSys (MetaMask開発元) が開発するzkEVM L2。大型エアドロップが強く期待されている。Surge, Surge+等のキャンペーン実施済み。",
            "tasks": [
                "Linea Surgeキャンペーンに参加",
                "LineaへのETHブリッジ",
                "Linea DeFiプロトコル利用",
                "MetaMaskとの連携を活用",
            ],
            "end_date": (today + timedelta(days=100)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/37208/small/linea.jpg",
            "url": "https://linea.build/",
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
