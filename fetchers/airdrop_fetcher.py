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
    """注目エアドロップシードデータ (2025年最新版)"""
    today = datetime.utcnow()
    return [
        # ===== 最高注目案件 =====
        {
            "id": "hyperliquid-hype",
            "name": "Hyperliquid (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "取引所トークン",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 2000,
            "description": "高速オンチェーン永久先物DEX。独自L1チェーン上で動作。累計$1B超の取引量を誇りトップDEXに成長。ポイント制度でエアドロップ継続中。",
            "tasks": ["Hyperliquid上での先物/スポット取引", "流動性提供 (HLP Vault)", "紹介プログラム参加", "継続的な取引量維持"],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "monad-mon",
            "name": "Monad",
            "symbol": "MON",
            "category": "Layer1",
            "type": "メインネット前エアドロップ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 1500,
            "description": "EVM互換の超高速Layer1チェーン。10,000 TPS・1秒ファイナリティ。テストネット参加者へのエアドロップが期待される2025年最注目プロジェクト。",
            "tasks": ["Monadテストネット参加", "テストネット上でのDeFi利用", "Discordコミュニティ参加 (Monad Pro取得)", "複数週にわたるアクティビティ維持"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/37019/small/monad.jpg",
            "url": "https://monad.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "berachain-bera",
            "name": "Berachain (BERA)",
            "symbol": "BERA",
            "category": "Layer1/DeFi",
            "type": "流動性証明 (PoL)",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1200,
            "description": "独自のProof of Liquidity (PoL) 機構を持つEVM互換L1。DeFiとL1が一体化。BGT・BERA・HNEYの3トークンエコノミー。メインネット稼働中で追加報酬プログラムが継続。",
            "tasks": ["BEX (Berachain DEX) での流動性提供", "BGTステーキング", "Berachain上のDeFiプロトコル利用 (Kodiak, Infrared)", "Berpsでの取引"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/35455/small/BERA.png",
            "url": "https://berachain.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
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
            "estimated_value_usd": 800,
            "description": "リアルタイムEVM。100,000+ TPS・1msレイテンシを目指すEthereum L2。テストネット参加者向けに大型エアドロップが予定。Vitalik Buterinも注目するプロジェクト。",
            "tasks": ["MegaETH テストネット参加 (megaeth.com)", "テストETH取得・送金", "対応dApps利用", "Twitter (@megaeth_labs) フォロー"],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/54543/small/megaeth.jpg",
            "url": "https://megaeth.systems/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "initia-init",
            "name": "Initia (INIT)",
            "symbol": "INIT",
            "category": "Layer1/Cosmos",
            "type": "メインネットローンチ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 600,
            "description": "Cosmos SDK採用のInterwoven Stack L1。複数のアプリチェーン (Minitia) を統合管理。2025年メインネットローンチ直前でエアドロップ参加チャンス。",
            "tasks": ["Initia テストネット (Yulei-1) 参加", "Galxeキャンペーン参加", "Discordコミュニティ参加", "テストネットバリデータまたはユーザー参加"],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/37679/small/initia.png",
            "url": "https://initia.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        # ===== 注目案件 =====
        {
            "id": "sonic-s",
            "name": "Sonic (S)",
            "symbol": "S",
            "category": "Layer1/DeFi",
            "type": "エコシステム報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 500,
            "description": "旧Fantom OperaがSonicとしてリブランド。10,000 TPS・EVM互換。Sonic Gems/Arcade報酬プログラムで継続的なエアドロップが配布されている。",
            "tasks": ["Sonic上でのDeFi活動 (SpookySwap, Shadow)", "Sonic Gemsポイント獲得", "流動性提供", "Sonic Arcadeゲーム参加"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/53842/small/sonic_s.png",
            "url": "https://soniclabs.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "movement-move",
            "name": "Movement (MOVE)",
            "symbol": "MOVE",
            "category": "Layer2",
            "type": "新規上場後エコシステム",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "Move VMを使用するEthereum L2。上場済みだが継続的なエコシステム報酬プログラムが稼働中。Move言語の高いセキュリティが特徴。",
            "tasks": ["Movement Portalでのブリッジ", "Movement上のDeFiプロトコル利用", "コミュニティ参加", "エコシステムキャンペーン参加"],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39619/small/MOVE_color.png",
            "url": "https://movementlabs.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "scroll-scr",
            "name": "Scroll (SCR)",
            "symbol": "SCR",
            "category": "Layer2",
            "type": "エコシステム継続報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "EVM互換ZK-Rollup。既に上場済みだが第2弾エアドロップの可能性あり。継続的なネットワーク利用者への報酬プログラムが継続。",
            "tasks": ["ScrollネットワークへETHブリッジ", "Scroll上でのDeFi利用 (Ambient, Nuri)", "複数週にわたるアクティビティ", "Scroll Sessionポイント獲得"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/25734/small/scroll.png",
            "url": "https://scroll.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "eigenlayer-eigen",
            "name": "EigenLayer (EIGEN)",
            "symbol": "EIGEN",
            "category": "インフラ",
            "type": "リステーキング/AVS報酬",
            "status": "active",
            "difficulty": "hard",
            "estimated_value_usd": 600,
            "description": "Ethereumのリステーキングプロトコル。AVS (Active Validator Service) エコシステムが急拡大。ステーキング量に応じた継続的な報酬配布。",
            "tasks": ["ETHをリステーキング (Native/LST)", "stETH・rETHなどLSTをデポジット", "AVSへの参加・オペレーター登録", "EigenDAアクティビティ"],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/33751/small/eigen.png",
            "url": "https://eigenlayer.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "layerzero-zro",
            "name": "LayerZero (ZRO)",
            "symbol": "ZRO",
            "category": "インフラ",
            "type": "レトロアクティブ/継続",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 300,
            "description": "クロスチェーンメッセージングプロトコル。第1弾配布済み。継続的なエコシステム活動で第2弾の可能性あり。",
            "tasks": ["Stargate経由でのブリッジ", "複数チェーンでのトランザクション", "LayerZero対応dApps利用 (Aptos Bridge, etc.)"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/28206/small/ftxG9_TJ_400x400.jpeg",
            "url": "https://layerzero.network/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "zksync-era",
            "name": "zkSync Era (ZK)",
            "symbol": "ZK",
            "category": "Layer2",
            "type": "エコシステム報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 150,
            "description": "Matter Labsが開発するZK-Rollup。上場済み。継続的なエコシステム利用者へのインセンティブプログラムが継続。",
            "tasks": ["Era上でのスワップ (Syncswap, Mute)", "zkSync公式ブリッジ利用", "zkSync上でのNFTミント"],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/38043/small/ZKTokenBlack.png",
            "url": "https://zksync.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "abstract-abs",
            "name": "Abstract (ABS)",
            "symbol": "ABS",
            "category": "Layer2",
            "type": "コンシューマーチェーン",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 500,
            "description": "Pudgy Penguinsチームが開発するコンシューマー向けLayer2。NFT・ゲーム・エンターテイメントに特化。ロールアップ上でのユーザー体験を革新。",
            "tasks": ["Abstractウォレット作成", "Abstract Portal参加", "Abstract上のdApp利用", "Twitterキャンペーン参加"],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/54191/small/abstract.jpg",
            "url": "https://abs.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "kaito-kaito",
            "name": "Kaito (KAITO)",
            "symbol": "KAITO",
            "category": "AI/データ",
            "type": "InfoFi/ソーシャル報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "AI搭載の暗号通貨情報集約プラットフォーム。Yapperシステムでの高品質ツイートに対してKAITO報酬を配布。情報発信者向け新型エアドロップ。",
            "tasks": ["Kaito Yapper登録", "暗号通貨関連の高品質ツイート投稿", "Mindshareスコア向上", "Kaito AIのMindshareランキング上位維持"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/54165/small/kaito.png",
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
