"""
Airdrop情報をWeb/APIから収集するモジュール。
airdrops.ioのスクレイピングとCoinGeckoトレンドを組み合わせ、
2026年最新のシードデータとマージして返す。
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
        # 複数のセレクタパターンを試みる
        cards = (
            soup.select(".airdrop-item")
            or soup.select(".airdrop-card")
            or soup.select("article.post")
            or soup.select(".entry-content .airdrop")
        )

        for card in cards[:30]:
            name_el = (
                card.select_one(".airdrop-title")
                or card.select_one("h3")
                or card.select_one("h2")
                or card.select_one(".entry-title")
            )
            link_el = card.select_one("a[href]")
            value_el = (
                card.select_one(".airdrop-value")
                or card.select_one(".value")
                or card.select_one(".prize")
            )
            end_el = (
                card.select_one(".airdrop-end")
                or card.select_one(".end-date")
                or card.select_one(".deadline")
            )
            img_el = card.select_one("img")

            if not name_el:
                continue

            name = name_el.get_text(strip=True)
            if len(name) < 2 or len(name) > 100:
                continue

            items.append({
                "name": name,
                "url": link_el["href"] if link_el else "https://airdrops.io/",
                "estimated_value": value_el.get_text(strip=True) if value_el else "不明",
                "end_date": end_el.get_text(strip=True) if end_el else "未定",
                "logo": img_el.get("src", "") if img_el else "",
                "source": "airdrops.io",
            })
        logger.info(f"airdrops.io スクレイプ完了: {len(items)}件")
        return items
    except Exception as e:
        logger.warning(f"airdrops.io scrape failed: {e}")
        return []


def _build_seed_airdrops() -> list[dict]:
    """2026年6月時点の注目エアドロップシードデータ"""
    today = datetime.utcnow()

    return [
        # ===== 超大型・最注目案件 =====
        {
            "id": "base-coinbase",
            "name": "Base (Coinbase L2)",
            "symbol": "BASE",
            "category": "Layer2",
            "type": "エコシステムエアドロップ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 3000,
            "description": "CoinbaseのEthereum L2。JPMorganが時価総額$12〜34Bと試算する最大級の未確認エアドロップ。Base上でのDeFi活動・ブリッジが対象になる見込み。",
            "tasks": [
                "BaseへのETHブリッジ（公式ブリッジ推奨）",
                "Base上でのUniswap/Aerodrome等DeFi利用",
                "複数月にわたるアクティビティ維持",
                "Coinbaseアカウントと連携（可能な場合）",
            ],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/asset_platforms/images/131/small/base-network-logo.png",
            "url": "https://base.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "ウォレット/インフラ",
            "type": "ポイント制エアドロップ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 1500,
            "description": "世界最大のEVMウォレットMetaMaskがMASKトークンをローンチ予定。スワップ・ブリッジ利用でポイントを獲得。Ethereum/Base/Linea/Arbitrumでの利用が対象。",
            "tasks": [
                "MetaMask Swapsでトークンスワップ",
                "MetaMask Bridgeでチェーン間ブリッジ",
                "MetaMask Card利用（対応地域）",
                "Consensysエコシステムアプリ利用",
            ],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/37297/small/metamask.png",
            "url": "https://metamask.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "monad-mon",
            "name": "Monad (MON)",
            "symbol": "MON",
            "category": "Layer1",
            "type": "テストネット参加",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 1200,
            "description": "EVM互換高速L1。10,000TPS・ほぼゼロガス。$240M調達済み。TGEは2026年10月予定。テストネット参加者向けのエアドロップが期待される。",
            "tasks": [
                "Monadテストネットへの参加",
                "Monadカード（Wave 2）クレーム",
                "MonadエコシステムのdApps利用",
                "Discordコミュニティでの活動",
            ],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/40492/small/monad.jpg",
            "url": "https://monad.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "grvt-exchange",
            "name": "GRVT",
            "symbol": "GRVT",
            "category": "DeFi/DEX",
            "type": "シーズン制ポイント",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1000,
            "description": "ハイブリッドDEX。Season 2進行中でコミュニティ向け28%配分（Season 2だけで18%）。TGE 2026年6月予定。取引高が多いほどポイント倍率アップ。",
            "tasks": [
                "GRVT上での先物/オプション取引",
                "流動性提供（マーケットメイク）",
                "Season 2ポイントを継続取得",
                "紹介プログラムへの参加",
            ],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/43116/small/GRVT.png",
            "url": "https://grvt.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "利用者向けエアドロップ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 800,
            "description": "最大の分散型予測市場。評価額$9B。独自チェーン構築計画あり。Polygonネットワーク上での取引・アクティビティとXアカウント連携が対象。",
            "tasks": [
                "Polymarketで予測市場に参加（賭け）",
                "MetaMask + Polygonネットワーク接続",
                "X（旧Twitter）アカウントをプロフィールにリンク",
                "複数カテゴリの市場に参加",
            ],
            "end_date": (today + timedelta(days=150)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/43217/small/polymarket.jpg",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        # ===== 中型注目案件 =====
        {
            "id": "megaeth-l2",
            "name": "MegaETH",
            "symbol": "",
            "category": "Layer2",
            "type": "エコシステムエアドロップ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "次世代Ethereum L2。超高速処理・低コストを実現。テストネット参加とエコシステム活動でポイント獲得。早期参加者に有利な配分が期待される。",
            "tasks": [
                "MegaETHテストネットへの参加",
                "エコシステムDAppsの利用",
                "ブリッジ・スワップアクティビティ",
                "コミュニティイベントへの参加",
            ],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/44000/small/megaeth.jpg",
            "url": "https://megaeth.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "berachain-s2",
            "name": "Berachain Season 2",
            "symbol": "BERA",
            "category": "Layer1",
            "type": "PoL流動性証明",
            "status": "active",
            "difficulty": "hard",
            "estimated_value_usd": 1500,
            "description": "独自のPoL（流動性証明）コンセンサスを採用するEVM互換L1。$140M調達。Season 2が進行中。DeFi流動性提供でBGTトークン報酬を獲得。",
            "tasks": [
                "Berachain v2 Bartioテストネット参加",
                "流動性提供（BGTバリデーターへのデリゲート）",
                "エコシステムDApps（Kodiak等）利用",
                "Infrared/Honeypot等のプロトコル利用",
            ],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/35480/small/bera.jpg",
            "url": "https://berachain.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "linea-consensys",
            "name": "Linea (Consensys L2)",
            "symbol": "LXP",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 500,
            "description": "Consensys（MetaMask開発元）のEVM L2。Linea Surgeポイントシステムで活動量を計測中。MetaMaskユーザーが有利。近日中のTGEが期待される。",
            "tasks": [
                "LineaへのETHブリッジ",
                "Linea上でのDeFi利用（Uniswap/SyncSwap等）",
                "Linea Surgeポイントを継続取得",
                "MetaMaskウォレットでの利用（ボーナス期待）",
            ],
            "end_date": (today + timedelta(days=75)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/asset_platforms/images/135/small/linea.png",
            "url": "https://linea.build/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        # ===== 継続注目案件 =====
        {
            "id": "hyperliquid-hype",
            "name": "Hyperliquid (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "取引所トークン",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1000,
            "description": "高速オンチェーン永久先物DEX。独自L1チェーン上で動作。HLPバルトへの参加や取引量でポイント蓄積。継続的な報酬プログラムを提供中。",
            "tasks": [
                "Hyperliquid上での先物取引",
                "HLP (Hyperliquidity Provider) Vault参加",
                "紹介プログラム参加",
            ],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
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
            "description": "Ethereumのリステーキングプロトコル。AVSエコシステムが急拡大中。Season 2エアドロップが継続中。新しいAVSへの参加で追加報酬の可能性。",
            "tasks": [
                "ETHをEigenLayerにリステーキング",
                "LST (stETH/rETH等) をデポジット",
                "AVSへの参加・オペレーター選択",
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
    Returns: (airdrops_list, new_scraped_names)
    """
    curated = _build_seed_airdrops()
    scraped = _scrape_airdrops_io()

    seen_names = {a["name"].lower() for a in curated}
    new_items = []

    for s in scraped:
        if s["name"].lower() not in seen_names:
            curated.append({
                "id": s["name"].lower().replace(" ", "-")[:50],
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
