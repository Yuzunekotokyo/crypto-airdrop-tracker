"""
Airdrop情報をWeb/APIから収集するモジュール。
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
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
}


def _scrape_defillama_airdrops() -> list[dict]:
    """DeFiLlamaのエアドロップ情報を取得"""
    try:
        r = requests.get(
            "https://defillama.com/airdrops",
            headers=HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        for row in soup.select("tr")[:20]:
            cells = row.select("td")
            if len(cells) >= 2:
                name_el = cells[0].select_one("a") or cells[0]
                name = name_el.get_text(strip=True)
                if name:
                    items.append({
                        "name": name,
                        "url": "https://defillama.com/airdrops",
                        "estimated_value": "未定",
                        "end_date": "未定",
                        "logo": "",
                        "source": "defillama",
                    })
        return items
    except Exception as e:
        logger.warning(f"DeFiLlama scrape failed: {e}")
        return []


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
    """手動管理の注目エアドロップシードデータ (2025-2026年版)"""
    today = datetime.utcnow()
    return [
        {
            "id": "monad-mon",
            "name": "Monad (MON)",
            "symbol": "MON",
            "category": "Layer1",
            "type": "テストネット参加",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 2000,
            "description": "EVM互換の超高速Layer1。10,000 TPS以上を実現。テストネット参加者への大型エアドロップが期待される。",
            "tasks": [
                "Monadテストネットへの参加",
                "テストネットトークンの取得・利用",
                "Discord/コミュニティへの参加",
                "早期採用者バッジの取得",
            ],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/37307/small/monad.png",
            "url": "https://monad.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "megaeth",
            "name": "MegaETH",
            "symbol": "METH",
            "category": "Layer2",
            "type": "テストネット参加",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 1500,
            "description": "1,000,000 TPS目標のEthereum L2。リアルタイムブロックチェーン。テストネット活発中。",
            "tasks": [
                "MegaETHテストネットへの接続",
                "テストネットECO/GIGAトークン取得",
                "TelegraphなどdApps利用",
                "コミュニティ参加",
            ],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "",
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
            "estimated_value_usd": 1000,
            "description": "高速オンチェーン永久先物DEX。独自L1チェーン上で動作。取引量によるポイント報酬継続中。",
            "tasks": [
                "Hyperliquid上での先物取引",
                "流動性提供 (HLP Vault)",
                "紹介プログラム参加",
                "Vaultへのステーキング",
            ],
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
            "type": "エコシステム報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 800,
            "description": "IP（知的財産）のオンチェーン管理プロトコル。NFT・創作物のライセンス管理に特化したL1。",
            "tasks": [
                "Story Networkへの接続",
                "IPAをミント・登録",
                "IPAsset Explorer利用",
                "コミュニティタスク参加",
            ],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://www.storyprotocol.xyz/",
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
            "description": "Proof of Liquidity (PoL) を採用するEVM互換L1。BEX/BerpsなどDeFiアプリ活用でBGTトークン獲得。",
            "tasks": [
                "Berachain上でのDeFi利用",
                "BEX（DEX）での流動性提供",
                "BGTをバリデータに委任",
                "Berpsで永久先物取引",
            ],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/35455/small/bera.png",
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
            "type": "ステーキング報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 700,
            "description": "BitcoinをCosmosチェーンのPoSセキュリティに活用するプロトコル。BTCステーキングで報酬獲得。",
            "tasks": [
                "Babylon Phase-2でBTCをステーキング",
                "BabylonウォレットでのBTC委任",
                "エコシステムパートナーチェーン参加",
            ],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39384/small/babylon.png",
            "url": "https://babylonchain.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "eclipse-eth",
            "name": "Eclipse",
            "symbol": "ECL",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 500,
            "description": "Ethereum上のSolana VM (SVM) L2。高速EclipseメインネットでのDeFi活動でエアドロップ狙い。",
            "tasks": [
                "Turboブリッジ経由でETHをデポジット",
                "Eclipse上のDEXでスワップ",
                "SegementなどdApps利用",
            ],
            "end_date": (today + timedelta(days=75)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://eclipse.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "aztec-network",
            "name": "Aztec Network",
            "symbol": "AZTEC",
            "category": "Layer2",
            "type": "プライバシーL2",
            "status": "upcoming",
            "difficulty": "hard",
            "estimated_value_usd": 1200,
            "description": "ZK技術を使ったプライベートスマートコントラクトL2。大型VC資金調達済み。メインネット前のテストネット参加が重要。",
            "tasks": [
                "Aztec Sandbox参加",
                "プライベートdAppsのテスト",
                "Noirlang開発者向けプログラム参加",
                "GitHubコントリビューション",
            ],
            "end_date": (today + timedelta(days=150)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://aztec.network/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "linea-zkev",
            "name": "Linea (zkEVM)",
            "symbol": "LINEA",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "ConsenSys（MetaMask開発元）によるzkEVM L2。公式エアドロップキャンペーン「Linea Voyage」実施中。",
            "tasks": [
                "Lineaブリッジ経由でETH転送",
                "Voyage NFTのmint",
                "Linea上DEXでのスワップ",
                "週次ミッション達成",
            ],
            "end_date": (today + timedelta(days=40)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/31158/small/linea-logo.png",
            "url": "https://linea.build/",
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
            "description": "Ethereumのリステーキングプロトコル。ETHをステーキングし追加報酬を獲得。AVSエコシステム拡大中。",
            "tasks": [
                "ETHをリステーキング",
                "LST (stETH等) をデポジット",
                "AVS（Actively Validated Services）への参加",
            ],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
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
    # 複数ソースから追加スクレイピングを試みる
    scraped = _scrape_airdrops_io()
    if not scraped:
        scraped = _scrape_defillama_airdrops()

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
                "description": f"外部ソースより取得: {s.get('estimated_value', '')}",
                "tasks": [],
                "end_date": s.get("end_date", "未定"),
                "logo": s.get("logo", ""),
                "url": s.get("url", ""),
                "is_hot": False,
                "added_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "source": s.get("source", "scraped"),
            })
            new_items.append(s["name"])
            seen_names.add(s["name"].lower())

    # 注目度でソート: is_hot → estimated_value_usd
    curated.sort(key=lambda x: (not x.get("is_hot"), -x.get("estimated_value_usd", 0)))

    return curated, new_items
