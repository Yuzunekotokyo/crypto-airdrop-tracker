"""
Airdrop情報をWeb/APIから収集するモジュール。
airdrops.ioのパブリックページ + CoinGeckoトレンド + キュレーションデータを組み合わせて使用。
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
        "Chrome/125.0.0.0 Safari/537.36"
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
        logger.info(f"airdrops.io から {len(items)} 件取得")
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
            "type": "テストネット参加",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1200,
            "description": "EVM互換の超高速Layer1ブロックチェーン。並列処理で毎秒10,000TPS実現。テストネット参加者に大型エアドロップ予定。",
            "tasks": [
                "Monadテストネットに接続",
                "テストトランザクション実行",
                "Discordコミュニティ参加",
                "テストネットDeFiプロトコル利用",
            ],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39730/small/monad.jpg",
            "url": "https://monad.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "megaeth-mega",
            "name": "MegaETH",
            "symbol": "MEGA",
            "category": "Layer2",
            "type": "テストネット参加",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 800,
            "description": "Ethereum L2の中で最速を目指すリアルタイムブロックチェーン。1msブロック時間。テストネット参加でポイント獲得中。",
            "tasks": [
                "MegaETHテストネットに参加",
                "テストETHをブリッジ",
                "テストネットアプリを利用",
                "Twitterフォロー＆リツイート",
            ],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/52957/small/megaeth.jpg",
            "url": "https://megaeth.systems/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "story-ip",
            "name": "Story Protocol (IP)",
            "symbol": "IP",
            "category": "インフラ",
            "type": "エコシステム参加",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 600,
            "description": "知的財産権をブロックチェーン上で管理するプロトコル。IPをNFT化して収益化。エコシステム参加者に配布予定。",
            "tasks": [
                "Story Protocolに資産を登録",
                "IPNFTを作成",
                "コミュニティタスク完了",
                "Discordでロール取得",
            ],
            "end_date": (today + timedelta(days=75)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/36425/small/story.jpg",
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
            "type": "取引所トークン",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 2000,
            "description": "高速オンチェーン永久先物DEX。独自L1チェーン上で動作。取引量によるHYPEポイント報酬継続中。",
            "tasks": [
                "Hyperliquid上での先物取引",
                "流動性提供 (HLP Vault)",
                "紹介プログラム参加",
                "毎日アクティブに取引",
            ],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "kaito-kaito",
            "name": "Kaito AI (KAITO)",
            "symbol": "KAITO",
            "category": "AI/Web3",
            "type": "ソーシャルマイニング",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 500,
            "description": "AI搭載のWeb3情報キュレーションプロトコル。Yap(投稿)でKaitoポイントを獲得し継続的なエアドロップを受け取れる。",
            "tasks": [
                "Kaito AIに登録",
                "Crypto関連をTwitterで投稿 (Yap)",
                "毎日アクティブにYap",
                "質の高いコンテンツで高スコアを狙う",
            ],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/54458/small/kaito.jpg",
            "url": "https://kaito.ai/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "linea-linea",
            "name": "Linea (LINEA)",
            "symbol": "LINEA",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "ConsenSys開発のZK-Rollup L2。MetaMaskと深く統合。Surge(アクティビティ)キャンペーン継続中。",
            "tasks": [
                "LineaネットワークへETHブリッジ",
                "Linea上でDeFi利用",
                "Lineaポイントを蓄積",
                "MetaMask Swapsを利用",
            ],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/31518/small/linea.jpg",
            "url": "https://linea.build/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "symbiotic-sym",
            "name": "Symbiotic (SYM)",
            "symbol": "SYM",
            "category": "インフラ",
            "type": "リステーキング",
            "status": "upcoming",
            "difficulty": "hard",
            "estimated_value_usd": 900,
            "description": "Ethereumリステーキングプロトコル。EigenLayerに対抗するSymbioticにステーキングしてポイント獲得中。",
            "tasks": [
                "ETH/LST をSymbioticにデポジット",
                "対応Vaultに資産を預ける",
                "ポイント蓄積期間中に継続保有",
            ],
            "end_date": (today + timedelta(days=100)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39632/small/symbiotic.jpg",
            "url": "https://symbiotic.fi/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "particle-parti",
            "name": "Particle Network (PARTI)",
            "symbol": "PARTI",
            "category": "インフラ",
            "type": "テストネット参加",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "アカウント抽象化とチェーン抽象化を実現するインフラ。Universal Accountsで全チェーンを一つのウォレットで管理。",
            "tasks": [
                "Particle Networkに登録",
                "Universal Account作成",
                "テストネットタスク完了",
                "Discordコミュニティ参加",
            ],
            "end_date": (today + timedelta(days=50)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/37590/small/particle.jpg",
            "url": "https://particle.network/",
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
                "id": s["name"].lower().replace(" ", "-").replace("/", "-"),
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
    curated.sort(key=lambda x: (not x.get("is_hot"), -(x.get("estimated_value_usd") or 0)))

    return curated, new_items
