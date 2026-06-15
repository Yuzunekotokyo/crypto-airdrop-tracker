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
    """手動管理の注目エアドロップシードデータ (2026年6月 最新版)"""
    today = datetime.utcnow()
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
            "description": "EVM互換の超高速L1ブロックチェーン。毎秒10,000TPS以上を実現。テストネット・メインネット参加者向けに大規模エアドロップ予定。",
            "tasks": ["Monad testnet/mainnetでのトランザクション", "Monad対応DeFi利用 (Kuru, Ambient等)", "Discord/Xでのコミュニティ活動", "複数週継続的なアクティビティ"],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/36000/small/monad.png",
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
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 1500,
            "description": "リアルタイムEthereum L2。100,000 TPS以上のスループットを目指す次世代ロールアップ。テストネットアクティビティで報酬獲得可能。",
            "tasks": ["MegaETH testnetへのブリッジ", "testnet上でのDeFi操作", "エコシステムdApps (MegaSwap等) 利用", "Discordタスク完了"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/52000/small/megaeth.png",
            "url": "https://megaeth.systems/",
            "is_hot": True,
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
            "difficulty": "medium",
            "estimated_value_usd": 1200,
            "description": "Bitcoinのセキュリティを他チェーンに提供するプロトコル。BTC保有者はBabylonを通じてステーキング報酬とBBNトークンを獲得できる。",
            "tasks": ["BTCをBabylonへステーキング", "Phase 2キャップ内での参加", "BabylonポイントプログラムへのBBN変換", "委任先バリデーターの選択"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/43476/small/babylon.png",
            "url": "https://babylonlabs.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "initia",
            "name": "Initia (INIT)",
            "symbol": "INIT",
            "category": "Layer1",
            "type": "新規上場",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "インターチェーンL1エコシステム。コスモスSDK基盤のL1とMove/EVM/WASM対応のL2(Minitia)で構成。Xpアクティビティがトークン配分に影響。",
            "tasks": ["Initia testnet参加・Xp獲得", "Minitia (L2) でのトランザクション", "Initia Wallet使用", "バリデーター委任"],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/44000/small/initia.png",
            "url": "https://initia.xyz/",
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
            "description": "並列実行対応のモジュラー型L2。UTXO型モデルで超高速処理を実現。独自言語Swayで開発されたdAppsのエコシステムが拡大中。",
            "tasks": ["Fuel Ignition mainnetでの取引", "Spark (DEX) での流動性提供", "ブリッジ利用 (ETH→Fuel)", "Swayでのスマートコントラクト開発体験"],
            "end_date": (today + timedelta(days=75)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/33924/small/fuel.jpg",
            "url": "https://fuel.network/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "eclipse-evm-svm",
            "name": "Eclipse",
            "symbol": "ECL",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 700,
            "description": "EthereumにSolana VM(SVM)を持ち込むL2。高速なSolanaの実行環境とEthereumのセキュリティを組み合わせた新世代ロールアップ。",
            "tasks": ["EclipseブリッジでETH/SOLをデポジット", "Eclipse上でのDeFi利用", "Turbo (DEX) のスワップ実行", "複数週のアクティビティ継続"],
            "end_date": (today + timedelta(days=50)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/36800/small/eclipse.png",
            "url": "https://eclipse.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "nillion-nil",
            "name": "Nillion (NIL)",
            "symbol": "NIL",
            "category": "インフラ",
            "type": "新規上場",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "分散型ブラインドコンピューティングネットワーク。AIやプライバシー関連の秘密計算を可能にするインフラ。testnet参加者向けNILトークン配布予定。",
            "tasks": ["Nillion testnetへの参加登録", "Nillion Walletセットアップ", "testnetタスク (Nilチェーントランザクション)", "コミュニティイベント参加"],
            "end_date": (today + timedelta(days=40)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/45000/small/nillion.png",
            "url": "https://nillion.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "particle-network",
            "name": "Particle Network (PARTI)",
            "symbol": "PARTI",
            "category": "インフラ",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 500,
            "description": "チェーン抽象化(Chain Abstraction)レイヤー。マルチチェーンのウォレット・ガス・資産を統合管理。Universal Accountsで全チェーンを単一UIで操作可能。",
            "tasks": ["Particle Universal Account作成", "複数チェーン間のトランザクション", "Particle Wallet Kitを利用したdApps使用", "ポイントプログラムへの参加"],
            "end_date": (today + timedelta(days=55)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39694/small/particle.png",
            "url": "https://particle.network/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "sonic-s",
            "name": "Sonic (S)",
            "symbol": "S",
            "category": "Layer1",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 350,
            "description": "旧Fantom(FTM)が進化したSonicチェーン。10,000 TPS・サブ秒ファイナリティを実現。FTM保有者はS移行エアドロップの対象。DeFi利用でSonicポイント獲得。",
            "tasks": ["Sonic mainnetへのブリッジ (Sonic Gateway使用)", "Beets/Shadow等のDeFi利用", "FTM→S移行完了", "Sonic Arcadeゲーム参加"],
            "end_date": (today + timedelta(days=35)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/36032/small/sonic.png",
            "url": "https://sonic.ooo/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-hype2",
            "name": "Hyperliquid Season 2 (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "取引所トークン",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 3000,
            "description": "高速オンチェーン永久先物DEX。シーズン2報酬プログラムが継続中。HLP Vault参加や取引量でポイント獲得。HYPEステーキングでも追加報酬あり。",
            "tasks": ["Hyperliquid上での先物取引 (最低$1000ボリューム/週)", "HLP Vaultへの流動性提供", "HYPE Staking参加", "紹介コード利用で追加ボーナス"],
            "end_date": (today + timedelta(days=20)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
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
