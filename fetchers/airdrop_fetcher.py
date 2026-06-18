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
    """手動管理の注目エアドロップシードデータ (定期的に更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "hyperliquid-hype",
            "name": "Hyperliquid (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "取引所トークン",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 2000,
            "description": "高速オンチェーン永久先物DEX。独自L1チェーン上で動作。取引量によるポイント報酬。現在も継続中。",
            "tasks": ["Hyperliquid上での先物取引", "スポット取引", "流動性提供 (HLP vault)"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "monad-mon",
            "name": "Monad (MON)",
            "symbol": "MON",
            "category": "Layer1",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1500,
            "description": "EVM互換の超高速L1。並列実行により10,000 TPS超を実現。テストネット参加者へのエアドロップが期待される。",
            "tasks": ["テストネットでのトランザクション実行", "Monad対応dApps利用", "Discordコミュニティ参加", "Monadスコア獲得"],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/38028/small/monad.png",
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
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 800,
            "description": "100,000 TPS超を目指すEthereum L2。リアルタイムブロックチェーン。テストネット参加で早期ユーザー特典。",
            "tasks": ["テストネット参加", "Quests (Egg NFT) 収集", "MegaETH上のdApps利用"],
            "end_date": (today + timedelta(days=80)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/54330/small/megaeth.png",
            "url": "https://megaeth.systems/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "berachain-bera",
            "name": "Berachain (BERA)",
            "symbol": "BERA",
            "category": "Layer1",
            "type": "流動性マイニング",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1000,
            "description": "Proof of Liquidity (PoL) コンセンサスを採用したEVM互換L1。BGTトークンを流動性提供で獲得可能。",
            "tasks": ["Bex (DEX) で流動性提供", "Honey (ステーブルコイン) のミント", "BGTをバリデーターに委任"],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/35455/small/berachain.png",
            "url": "https://berachain.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "initia-init",
            "name": "Initia (INIT)",
            "symbol": "INIT",
            "category": "Layer1",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 600,
            "description": "Cosmos SDKベースのインターチェーンL1。Minitia (L2) エコシステムを展開。ガバナンス参加者向け報酬。",
            "tasks": ["Initiaテストネット参加", "Minitia上でのアクティビティ", "Galxeキャンペーン参加"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/37021/small/initia.jpg",
            "url": "https://initia.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "sonic-s",
            "name": "Sonic (S)",
            "symbol": "S",
            "category": "Layer1",
            "type": "流動性マイニング",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "Fantom Foundationが再設計したEVM L1。高速・低コスト。Gems/Pointsプログラムでエアドロップ報酬獲得。",
            "tasks": ["Sonicでのスワップ・DeFi利用", "Gems (ポイント) 積み上げ", "アクティブウォレット維持"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/53148/small/sonic.png",
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
            "estimated_value_usd": 800,
            "description": "Ethereumのリステーキングプロトコル。ETHをステーキングし追加報酬を獲得。AVSへの参加でさらに収益化。",
            "tasks": ["ETHをリステーキング", "LST (stETH/rETH等) をデポジット", "AVSへの参加"],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/33751/small/eigen.png",
            "url": "https://eigenlayer.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "pendle-finance",
            "name": "Pendle Finance (PENDLE)",
            "symbol": "PENDLE",
            "category": "DeFi",
            "type": "利回りトークン化",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 500,
            "description": "利回りトークン化プロトコル。YT/PTに分割してポイント・エアドロップを効率的に獲得。複数エアドロップの倍率向上に最適。",
            "tasks": ["YT購入でポイント倍率向上", "stETH/eETH等のPT保有", "流動性提供 (LP)"],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/15069/small/Pendle_Logo_Normal-03.png",
            "url": "https://pendle.finance/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "corn-btcn",
            "name": "Corn Protocol (BTCN)",
            "symbol": "BTCN",
            "category": "Layer2",
            "type": "BTC利回り",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 600,
            "description": "BTCを基軸通貨とするEthereum L2。Peppered BTCN保有者向けエアドロップ予定。BTC保有者に優しいL2。",
            "tasks": ["BTC/wBTCをCornにブリッジ", "Cornのdepositでポイント獲得", "Discordコミュニティ参加"],
            "end_date": (today + timedelta(days=50)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/52413/small/corn.png",
            "url": "https://usecorn.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "avail-avl",
            "name": "Avail (AVL)",
            "symbol": "AVL",
            "category": "インフラ",
            "type": "データ可用性",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "モジュラーブロックチェーンのデータ可用性レイヤー。Clash of Nodesキャンペーンで早期ユーザー特典あり。",
            "tasks": ["Avail Light Client稼働", "Avail上のdApps利用", "バリデーター/ノミネーター参加"],
            "end_date": (today + timedelta(days=40)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/37228/small/avail.png",
            "url": "https://availproject.org/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "scroll-scr",
            "name": "Scroll (SCR)",
            "symbol": "SCR",
            "category": "Layer2",
            "type": "継続報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "EVM互換ZK-Rollup。Marks (ポイント) プログラムが継続中。継続的なDeFi利用で追加エアドロップの可能性。",
            "tasks": ["ScrollネットワークへETHブリッジ", "Scroll上でのDeFi利用", "複数週にわたるアクティビティ"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/25734/small/scroll.png",
            "url": "https://scroll.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "abstract-chain",
            "name": "Abstract Chain",
            "symbol": "ABS",
            "category": "Layer2",
            "type": "コンシューマーL2",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 350,
            "description": "Pudgy Penguinsチームが構築するコンシューマー向けEthereum L2。NFT・ゲームに特化。AGP (ポイント) 獲得可能。",
            "tasks": ["AbstractウォレットのセットアップとETHブリッジ", "Abstract上のdApps利用", "Abstract Global Wallet使用"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/55189/small/abstract.png",
            "url": "https://abs.xyz/",
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
