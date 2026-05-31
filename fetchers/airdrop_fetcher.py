"""
Airdrop情報をWeb/APIから収集するモジュール。
airdrops.ioのパブリックページ + CoinMarketCap + キュレーションデータを組み合わせ。
"""

import requests
import logging
from datetime import datetime
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


def _scrape_coinmarketcap_airdrops() -> list[dict]:
    """CoinMarketCapのエアドロップページから取得"""
    try:
        r = requests.get(
            "https://coinmarketcap.com/airdrop/",
            headers=HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        for row in soup.select("table tbody tr")[:20]:
            cells = row.find_all("td")
            if len(cells) < 3:
                continue
            name_el = cells[1].select_one("a") or cells[1]
            link_el = cells[1].select_one("a[href]")
            name = name_el.get_text(strip=True)
            if not name:
                continue
            items.append({
                "name": name,
                "url": f"https://coinmarketcap.com{link_el['href']}" if link_el and link_el.get("href","").startswith("/") else "https://coinmarketcap.com/airdrop/",
                "estimated_value": cells[2].get_text(strip=True) if len(cells) > 2 else "不明",
                "end_date": cells[3].get_text(strip=True) if len(cells) > 3 else "未定",
                "logo": "",
                "source": "coinmarketcap",
            })
        return items
    except Exception as e:
        logger.warning(f"CoinMarketCap scrape failed: {e}")
        return []


def _build_seed_airdrops() -> list[dict]:
    """キュレーション済みの注目エアドロップ (2025-2026年版)"""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return [
        {
            "id": "monad-mon",
            "name": "Monad (MON)",
            "symbol": "MON",
            "category": "Layer1",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 2000,
            "description": "EVM互換の超高速L1ブロックチェーン。TPS10,000+。テストネット/メインネット初期ユーザー向けエアドロップ。",
            "tasks": ["テストネットトランザクション実行", "Monad対応dApps利用", "コミュニティタスク完了", "DiscordのOGロール取得"],
            "end_date": "2026-08-31",
            "logo": "https://assets.coingecko.com/coins/images/53534/small/monad.jpg",
            "url": "https://monad.xyz/",
            "is_hot": True,
            "added_date": today,
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
            "estimated_value_usd": 1500,
            "description": "高速オンチェーン永久先物DEX。独自L1上で動作。取引量・流動性提供でポイント報酬獲得可能。",
            "tasks": ["Hyperliquid上での先物取引", "流動性提供 (HLP Vault)", "紹介プログラム参加", "早期ユーザーボーナス"],
            "end_date": "2026-07-31",
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today,
            "source": "curated",
        },
        {
            "id": "story-protocol-ip",
            "name": "Story Protocol (IP)",
            "symbol": "IP",
            "category": "インフラ",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 800,
            "description": "IPをオンチェーン化するL1ブロックチェーン。クリエイターとAIエージェント向けライセンス管理。",
            "tasks": ["IPAsset登録", "ライセンス付与/取得", "PIL利用", "Story上でdApps利用"],
            "end_date": "2026-09-30",
            "logo": "https://assets.coingecko.com/coins/images/37000/small/story.jpg",
            "url": "https://story.foundation/",
            "is_hot": True,
            "added_date": today,
            "source": "curated",
        },
        {
            "id": "kaito-kaito",
            "name": "Kaito (KAITO)",
            "symbol": "KAITO",
            "category": "AI/インフラ",
            "type": "Yapper報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 600,
            "description": "AI駆動のクリプト情報集約プラットフォーム。X上での発信量・質でYapper報酬を獲得。",
            "tasks": ["X (Twitter) でクリプトコンテンツ投稿", "Kaito Connectウォレット連携", "Yapperランキング上位を目指す"],
            "end_date": "2026-08-15",
            "logo": "https://assets.coingecko.com/coins/images/37012/small/kaito.jpg",
            "url": "https://kaito.ai/",
            "is_hot": True,
            "added_date": today,
            "source": "curated",
        },
        {
            "id": "megaeth-meth",
            "name": "MegaETH",
            "symbol": "METH",
            "category": "Layer2",
            "type": "テストネット報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 500,
            "description": "リアルタイムEVM。100,000TPS対応のEthereumL2。テストネット参加者向けエアドロップ予定。",
            "tasks": ["テストネット参加・トランザクション", "MegaMafia NFT保有", "エコシステムdApps利用", "Discordタスク完了"],
            "end_date": "2026-07-15",
            "logo": "https://assets.coingecko.com/coins/images/52100/small/megaeth.jpg",
            "url": "https://megaeth.systems/",
            "is_hot": True,
            "added_date": today,
            "source": "curated",
        },
        {
            "id": "initia-init",
            "name": "Initia (INIT)",
            "symbol": "INIT",
            "category": "Layer1",
            "type": "エコシステム報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 700,
            "description": "Interwoven L1/L2アーキテクチャ。複数Minichain上のDeFi活動でINIT報酬獲得。",
            "tasks": ["Initiaポータルでタスク完了", "MiniChain上のDeFi利用", "Enshrined Liquidityに参加", "早期ユーザーとして登録"],
            "end_date": "2026-08-31",
            "logo": "https://assets.coingecko.com/coins/images/37903/small/initia.png",
            "url": "https://initia.xyz/",
            "is_hot": True,
            "added_date": today,
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
            "end_date": "2026-09-30",
            "logo": "https://assets.coingecko.com/coins/images/25734/small/scroll.png",
            "url": "https://scroll.io/",
            "is_hot": False,
            "added_date": today,
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
            "tasks": ["Stargate経由でブリッジ実行", "複数チェーンでのトランザクション", "LayerZero対応dApps利用"],
            "end_date": "2026-07-31",
            "logo": "https://assets.coingecko.com/coins/images/28206/small/ftxG9_TJ_400x400.jpeg",
            "url": "https://layerzero.network/",
            "is_hot": False,
            "added_date": today,
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
            "end_date": "2026-10-31",
            "logo": "https://assets.coingecko.com/coins/images/33751/small/eigen.png",
            "url": "https://eigenlayer.xyz/",
            "is_hot": False,
            "added_date": today,
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
            "estimated_value_usd": 400,
            "description": "Igloo/Pudgy Penguinsが開発するコンシューマー向けZK L2。NFT・ゲーム・ソーシャルに特化。",
            "tasks": ["Abstract上でNFTミント", "AbstractウォレットのAGW作成", "エコシステムdApps利用", "ポイントプログラム参加"],
            "end_date": "2026-08-31",
            "logo": "https://assets.coingecko.com/coins/images/52500/small/abstract.jpg",
            "url": "https://abs.xyz/",
            "is_hot": False,
            "added_date": today,
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
            "estimated_value_usd": 350,
            "description": "Fantomチームが開発した高速EVM L1。10,000TPS以上。DeFi利用でSポイント報酬獲得。",
            "tasks": ["Sonic上でのDeFi利用", "流動性提供", "Sonic Gemsプログラム参加"],
            "end_date": "2026-09-15",
            "logo": "https://assets.coingecko.com/coins/images/37057/small/sonic.png",
            "url": "https://soniclabs.com/",
            "is_hot": False,
            "added_date": today,
            "source": "curated",
        },
        {
            "id": "zksync-era",
            "name": "zkSync Era (ZK)",
            "symbol": "ZK",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 200,
            "description": "Matter Labsが開発するZK-Rollup。エコシステムが急拡大中。",
            "tasks": ["Era上でのスワップ", "Syncswap/Mute利用", "zkSync公式ブリッジ利用"],
            "end_date": "2026-07-31",
            "logo": "https://assets.coingecko.com/coins/images/38043/small/ZKTokenBlack.png",
            "url": "https://zksync.io/",
            "is_hot": False,
            "added_date": today,
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
            "estimated_value_usd": 400,
            "description": "Move VMを使用するEthereum L2。高速・低コストトランザクション。テストネット参加者向けエアドロップ予定。",
            "tasks": ["テストネット参加", "Discordコミュニティ参加", "テストトランザクション実行"],
            "end_date": "2026-07-01",
            "logo": "https://assets.coingecko.com/coins/images/39619/small/MOVE_color.png",
            "url": "https://movementlabs.xyz/",
            "is_hot": False,
            "added_date": today,
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
    scraped += _scrape_coinmarketcap_airdrops()

    seen_names = {a["name"].lower() for a in curated}
    new_items = []
    today = datetime.utcnow().strftime("%Y-%m-%d")

    for s in scraped:
        name = s["name"].strip()
        if not name or name.lower() in seen_names:
            continue
        curated.append({
            "id": name.lower().replace(" ", "-").replace("(", "").replace(")", ""),
            "name": name,
            "symbol": "",
            "category": "その他",
            "type": "エアドロップ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": f"{s.get('source','外部')}より取得: {s.get('estimated_value', '')}",
            "tasks": [],
            "end_date": s.get("end_date", "未定"),
            "logo": s.get("logo", ""),
            "url": s.get("url", ""),
            "is_hot": False,
            "added_date": today,
            "source": s.get("source", "scraped"),
        })
        new_items.append(name)
        seen_names.add(name.lower())

    # 注目度でソート: is_hot → estimated_value_usd
    curated.sort(key=lambda x: (not x.get("is_hot"), -x.get("estimated_value_usd", 0)))

    return curated, new_items
