"""
Airdrop情報をWeb/APIから収集するモジュール。
ソース: curated(管理データ) / airdrops.io / DeFiLlama API
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
        selectors = [
            ".airdrop-item", ".hot-airdrop", ".airdrop-card",
            "article.airdrop", ".airdrop-listing-item",
        ]
        cards = []
        for sel in selectors:
            cards = soup.select(sel)
            if cards:
                break

        for card in cards[:30]:
            name_el = (card.select_one(".airdrop-title")
                       or card.select_one("h3")
                       or card.select_one("h2")
                       or card.select_one(".title"))
            link_el = card.select_one("a[href]")
            value_el = (card.select_one(".airdrop-value")
                        or card.select_one(".value")
                        or card.select_one(".prize"))
            end_el = (card.select_one(".airdrop-end")
                      or card.select_one(".end-date")
                      or card.select_one(".deadline"))
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
        logger.info(f"airdrops.io: {len(items)}件取得")
        return items
    except Exception as e:
        logger.warning(f"airdrops.io scrape failed: {e}")
        return []


def _fetch_defillama_airdrop_candidates() -> list[dict]:
    """
    DeFiLlamaからトークン未発行・高TVLプロトコルを取得してエアドロップ候補を生成。
    token==nullかつTVL>$30Mのものを対象とする。
    """
    try:
        r = requests.get("https://api.llama.fi/protocols", headers=HEADERS, timeout=20)
        r.raise_for_status()
        protocols = r.json()

        candidates = []
        for p in protocols:
            symbol = p.get("symbol", "")
            tvl = p.get("tvl") or 0
            name = p.get("name", "")
            url = p.get("url", "")
            logo = p.get("logo", "")
            chain = p.get("chain", "")
            category = p.get("category", "")

            # トークン未発行 & TVL > $30M
            if (not symbol or symbol in ("-", "")) and tvl > 30_000_000 and name:
                est_value = min(int(tvl / 10_000), 5000)  # TVLから推定報酬を概算
                candidates.append({
                    "id": f"defillama-{name.lower().replace(' ', '-')}",
                    "name": name,
                    "symbol": "",
                    "category": _map_category(category),
                    "type": "レトロアクティブ候補",
                    "status": "active",
                    "difficulty": "medium",
                    "estimated_value_usd": max(est_value, 100),
                    "description": f"DeFiLlamaより: TVL ${tvl/1e6:.1f}M。{chain}チェーンで展開中。トークン未発行のためエアドロップ期待大。",
                    "tasks": ["プロトコルの利用", "流動性提供", "複数回のトランザクション"],
                    "end_date": "未定",
                    "logo": logo,
                    "url": url or f"https://defillama.com/protocol/{name.lower().replace(' ', '-')}",
                    "is_hot": tvl > 200_000_000,
                    "added_date": datetime.utcnow().strftime("%Y-%m-%d"),
                    "source": "defillama",
                })
        # TVL降順ソート
        candidates.sort(key=lambda x: x.get("estimated_value_usd", 0), reverse=True)
        logger.info(f"DeFiLlama候補: {len(candidates[:10])}件取得")
        return candidates[:10]
    except Exception as e:
        logger.warning(f"DeFiLlama fetch failed: {e}")
        return []


def _map_category(cat: str) -> str:
    mapping = {
        "Dexes": "DeFi/DEX",
        "Lending": "DeFi/貸付",
        "Yield": "DeFi/Yield",
        "Derivatives": "DeFi/デリバティブ",
        "Bridge": "ブリッジ",
        "CDP": "DeFi/ステーブル",
        "Liquid Staking": "ステーキング",
        "RWA": "RWA",
        "Restaking": "リステーキング",
        "Chain": "Layer1",
        "Rollup": "Layer2",
        "NFT": "NFT",
        "Gaming": "ゲーム",
    }
    return mapping.get(cat, cat or "DeFi")


def _build_seed_airdrops() -> list[dict]:
    """管理済み注目エアドロップシードデータ (2025-2026年版)"""
    today = datetime.utcnow()
    return [
        {
            "id": "monad-monad",
            "name": "Monad (MONAD)",
            "symbol": "MONAD",
            "category": "Layer1",
            "type": "テストネット参加",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 2000,
            "description": "高性能EVM互換L1。10,000 TPS超。テストネット参加者への大型エアドロップが期待される注目No.1案件。",
            "tasks": [
                "テストネットFaucetでテストトークン入手",
                "テストスワップ・DeFi操作を実行",
                "Discordコミュニティに参加",
                "Nadをミント・転送",
            ],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/35543/small/monad.jpg",
            "url": "https://monad.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "megaeth",
            "name": "MegaETH",
            "symbol": "",
            "category": "Layer2",
            "type": "テストネット参加",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 1500,
            "description": "100,000 TPS対応の超高速EVM L2。テストネット参加者への大型エアドロップが噂される。フォローすべき最注目案件。",
            "tasks": [
                "テストネットFaucetでETH入手",
                "テストスワップ・NFT mint実行",
                "Twitter/Discordフォロー＆参加",
                "OGバッジ獲得",
            ],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://www.megaeth.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "babylon-baby",
            "name": "Babylon (BABY)",
            "symbol": "BABY",
            "category": "インフラ",
            "type": "BTCステーキング",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1200,
            "description": "ビットコインをステーキングしてPoSチェーンのセキュリティを強化するプロトコル。BTCホルダー向け大型エアドロップ実施中。",
            "tasks": [
                "BTCをBabylonへステーキング",
                "メインネットへの参加",
                "バリデーターへ委任",
            ],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/54268/small/baby.jpg",
            "url": "https://babylonchain.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "story-protocol-ip",
            "name": "Story Protocol (IP)",
            "symbol": "IP",
            "category": "インフラ",
            "type": "早期参加",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 800,
            "description": "IPをオンチェーン管理するブロックチェーン。クリエイター・コンテンツ系プロジェクト向けエアドロップ。ODYSSEYキャンペーン開催中。",
            "tasks": [
                "IPAsset(作品)の登録",
                "ライセンス取引の実行",
                "ODYSSEYキャンペーン参加",
            ],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/53252/small/ip.png",
            "url": "https://www.story.foundation/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "fuel-fuel",
            "name": "Fuel Network (FUEL)",
            "symbol": "FUEL",
            "category": "Layer2",
            "type": "並列EVM",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 700,
            "description": "最速の並列処理EVM L2。独自言語Swayを使用。初期ユーザーへの大型エアドロップ予定。",
            "tasks": [
                "Fuel Walletのセットアップ",
                "テストネットでのスワップ",
                "Swayコントラクトのデプロイ",
            ],
            "end_date": (today + timedelta(days=40)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/37266/small/fuel.png",
            "url": "https://fuel.network/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "grass-grass",
            "name": "Grass Protocol (GRASS)",
            "symbol": "GRASS",
            "category": "DePIN",
            "type": "帯域幅シェア",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 500,
            "description": "未使用のインターネット帯域幅をシェアしてGRASSトークンを獲得。Chrome拡張で誰でも簡単に参加可能。",
            "tasks": [
                "Chrome拡張をインストール",
                "常時接続で帯域幅を提供",
                "紹介プログラムへの参加",
            ],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/37693/small/grass.jpg",
            "url": "https://www.getgrass.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "initia-init",
            "name": "Initia (INIT)",
            "symbol": "INIT",
            "category": "Layer1",
            "type": "テストネット参加",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 600,
            "description": "モジュラーL1ブロックチェーン。CosmosとMove VMを組み合わせたユニーク設計。",
            "tasks": [
                "テストネットへの参加",
                "バリデーター操作",
                "ブリッジの利用",
            ],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/37979/small/initia.jpg",
            "url": "https://initia.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "sonic-s",
            "name": "Sonic (S)",
            "symbol": "S",
            "category": "Layer1",
            "type": "DeFi利用",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 350,
            "description": "元Fantom OperaがリブランディングされたL1。10,000 TPS対応。Sonic Gemsプログラムで報酬獲得可能。",
            "tasks": [
                "Sonic上でのDeFi利用",
                "流動性提供",
                "Sonic Gemsプログラム参加",
            ],
            "end_date": (today + timedelta(days=75)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/38405/small/sonic.jpg",
            "url": "https://www.soniclabs.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "io-net-io",
            "name": "IO.net (IO)",
            "symbol": "IO",
            "category": "DePIN",
            "type": "GPU提供",
            "status": "active",
            "difficulty": "hard",
            "estimated_value_usd": 500,
            "description": "分散型GPUネットワーク。GPUを提供してIOトークンを獲得。AI/ML開発者・GPU保有者向け。",
            "tasks": [
                "GPU/CPUを提供",
                "IO Workerのセットアップ",
                "AI推論ジョブの実行",
            ],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/37168/small/io-net.jpg",
            "url": "https://io.net/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "abstract-abs",
            "name": "Abstract (ABS)",
            "symbol": "ABS",
            "category": "Layer2",
            "type": "コンシューマー向けL2",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "Ethereum L2のコンシューマー向けチェーン。NFT・ゲーム特化。Pudgy Penguins系チームが開発。",
            "tasks": [
                "Abstract Walletを作成",
                "Abstract上でNFT mint/購入",
                "AGPコミュニティ参加",
            ],
            "end_date": (today + timedelta(days=50)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/53055/small/abstract.jpg",
            "url": "https://abs.xyz/",
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
    seen_names = {a["name"].lower() for a in curated}
    new_items = []

    # airdrops.io スクレイピング
    for s in _scrape_airdrops_io():
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

    # DeFiLlama 候補
    for d in _fetch_defillama_airdrop_candidates():
        if d["name"].lower() not in seen_names:
            curated.append(d)
            if d.get("is_hot"):
                new_items.append(d["name"])
            seen_names.add(d["name"].lower())

    # ソート: is_hot → estimated_value_usd
    curated.sort(key=lambda x: (not x.get("is_hot"), -x.get("estimated_value_usd", 0)))

    return curated, new_items
