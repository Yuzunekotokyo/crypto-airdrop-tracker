"""
Airdrop情報をWeb/APIから収集するモジュール。
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


def _build_seed_airdrops() -> list[dict]:
    """注目エアドロップシードデータ (2026年版 — 固定日付で変更検知可能)"""
    return [
        {
            "id": "monad-monad",
            "name": "Monad (MONAD)",
            "symbol": "MONAD",
            "category": "Layer1",
            "type": "テストネット/レトロ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 1500,
            "description": "EVM互換の並列処理L1チェーン。10,000 TPS以上の高速処理。テストネット参加者への大型エアドロップが期待される。",
            "tasks": ["テストネットでのトランザクション", "Monad公式Discord参加", "テストネットDeFiプロトコル利用"],
            "end_date": "2026-09-30",
            "logo": "https://assets.coingecko.com/coins/images/35959/small/monad.jpg",
            "url": "https://monad.xyz/",
            "is_hot": True,
            "added_date": "2026-01-01",
            "source": "curated",
        },
        {
            "id": "babylon-baby",
            "name": "Babylon (BABY)",
            "symbol": "BABY",
            "category": "Bitcoin Staking",
            "type": "ステーキング報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "BitcoinをセキュリティソースとしてPoSチェーンを保護するプロトコル。BTCネイティブステーキングで報酬獲得。",
            "tasks": ["BTCをBabylonでステーキング", "フェーズ2参加", "Babylon Points蓄積"],
            "end_date": "2026-08-31",
            "logo": "https://assets.coingecko.com/coins/images/37724/small/babylon_logo.png",
            "url": "https://babylonlabs.io/",
            "is_hot": True,
            "added_date": "2026-01-01",
            "source": "curated",
        },
        {
            "id": "megaeth-meth",
            "name": "MegaETH",
            "symbol": "METH",
            "category": "Layer2",
            "type": "テストネット/レトロ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 1200,
            "description": "リアルタイムブロックチェーン。100,000 TPS目標の高性能EVM L2。メインネット前のテストネット参加でエアドロップ期待。",
            "tasks": ["テストネット参加", "MegaETHコミュニティ参加", "Discordでの活動"],
            "end_date": "2026-10-31",
            "logo": "https://assets.coingecko.com/coins/images/40086/small/megaeth.jpg",
            "url": "https://megaeth.systems/",
            "is_hot": True,
            "added_date": "2026-01-01",
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
            "estimated_value_usd": 600,
            "description": "モジュラーL1+L2アーキテクチャ。Move/Wasm/EVM全対応。エコシステム参加者へのINIT配布を継続中。",
            "tasks": ["Initia上でのDeFi利用", "Validium L2への参加", "Initia Points獲得"],
            "end_date": "2026-07-31",
            "logo": "https://assets.coingecko.com/coins/images/37671/small/initia.jpg",
            "url": "https://initia.xyz/",
            "is_hot": True,
            "added_date": "2026-01-01",
            "source": "curated",
        },
        {
            "id": "hyperevm-hype",
            "name": "Hyperliquid EVM (HyperEVM)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "エコシステム報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 2000,
            "description": "HyperliquidのEVMチェーン拡張。DeFiポジションと取引量に基づくポイント報酬。HYPEステーキングも対応。",
            "tasks": ["HyperEVM上でのDeFi活動", "Hyperliquid永久先物取引", "HYPEトークンのステーキング"],
            "end_date": "2026-12-31",
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": "2026-01-01",
            "source": "curated",
        },
        {
            "id": "plume-plume",
            "name": "Plume Network (PLUME)",
            "symbol": "PLUME",
            "category": "RWA/Layer2",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "RWA(現実世界資産)特化のEVM L2。不動産・クレジット・コモディティのトークン化に特化。エアドロップ実施中。",
            "tasks": ["Plume上でRWA購入", "PLUMEステーキング", "ガバナンス参加"],
            "end_date": "2026-08-31",
            "logo": "https://assets.coingecko.com/coins/images/40203/small/plume.jpg",
            "url": "https://plumenetwork.xyz/",
            "is_hot": False,
            "added_date": "2026-01-01",
            "source": "curated",
        },
        {
            "id": "story-ip",
            "name": "Story Protocol (IP)",
            "symbol": "IP",
            "category": "インフラ/IP",
            "type": "エコシステム報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 500,
            "description": "知的財産(IP)管理に特化したブロックチェーン。AI生成コンテンツのIPライセンス管理で注目を集める。",
            "tasks": ["IPAssetの登録", "Story Protocol上でのライセンス", "コミュニティ参加"],
            "end_date": "2026-09-30",
            "logo": "https://assets.coingecko.com/coins/images/39338/small/story-protocol.jpg",
            "url": "https://story.foundation/",
            "is_hot": False,
            "added_date": "2026-01-01",
            "source": "curated",
        },
        {
            "id": "corn-btcn",
            "name": "Corn Network (BTCN)",
            "symbol": "BTCN",
            "category": "Bitcoin Yield",
            "type": "流動性マイニング",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 350,
            "description": "BitcoinをネイティブガストークンとするL2。BTCBでイールドを獲得しながらエアドロップポイントを蓄積。",
            "tasks": ["BTCBをデポジット", "Corn上でのDeFi利用", "Kernelポイント蓄積"],
            "end_date": "2026-07-31",
            "logo": "https://assets.coingecko.com/coins/images/40987/small/corn.jpg",
            "url": "https://usecorn.com/",
            "is_hot": False,
            "added_date": "2026-01-01",
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
            "estimated_value_usd": 300,
            "description": "Fantomから進化した高速L1。10,000 TPS・1秒以下ファイナリティ。Sonic Gemsプログラムで報酬獲得中。",
            "tasks": ["Sonic上でのDeFi利用", "SpookySwap等のDEX利用", "Sonic Gems獲得"],
            "end_date": "2026-06-30",
            "logo": "https://assets.coingecko.com/coins/images/38004/small/sonic-s.jpg",
            "url": "https://www.soniclabs.com/",
            "is_hot": False,
            "added_date": "2026-01-01",
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
            "estimated_value_usd": 700,
            "description": "Proof of Liquidity(PoL)コンセンサスのEVM L1。流動性提供者がブロック報酬を獲得。BGTトークンの配布継続中。",
            "tasks": ["BEX(DEX)で流動性提供", "BGTトークンを獲得・デリゲート", "Berachain DeFiエコシステム参加"],
            "end_date": "2026-12-31",
            "logo": "https://assets.coingecko.com/coins/images/35455/small/bera.png",
            "url": "https://berachain.com/",
            "is_hot": True,
            "added_date": "2026-01-01",
            "source": "curated",
        },
    ]


def _update_hot_from_trending(airdrops: list[dict], trending_coins: list[dict]) -> list[dict]:
    """CoinGeckoトレンドに基づいてis_hotフラグを動的更新"""
    trending_names = {t["name"].lower() for t in trending_coins}
    trending_symbols = {t["symbol"].lower() for t in trending_coins}

    for airdrop in airdrops:
        name_lower = airdrop.get("name", "").lower()
        symbol_lower = airdrop.get("symbol", "").lower()

        is_trending = any(
            t in name_lower or name_lower in t
            for t in trending_names
        ) or symbol_lower in trending_symbols

        if is_trending and not airdrop.get("is_hot"):
            airdrop["is_hot"] = True
            logger.info(f"トレンド検知 → hot昇格: {airdrop['name']}")

    return airdrops


def fetch_all_airdrops() -> tuple[list[dict], list[str]]:
    """
    全ソースからエアドロップデータを収集し、変更点リストと共に返す。
    Returns: (airdrops_list, new_items_names)
    """
    trending = get_trending_coins()
    curated = _build_seed_airdrops()
    curated = _update_hot_from_trending(curated, trending)

    scraped = _scrape_airdrops_io()

    seen_names = {a["name"].lower() for a in curated}
    seen_ids = {a["id"] for a in curated}
    new_items = []

    for s in scraped:
        s_id = s["name"].lower().replace(" ", "-")
        if s["name"].lower() not in seen_names and s_id not in seen_ids:
            new_entry = {
                "id": s_id,
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
            }
            curated.append(new_entry)
            new_items.append(s["name"])
            seen_names.add(s["name"].lower())

    # 注目度でソート: is_hot → estimated_value_usd
    curated.sort(key=lambda x: (not x.get("is_hot"), -x.get("estimated_value_usd", 0)))

    return curated, new_items
