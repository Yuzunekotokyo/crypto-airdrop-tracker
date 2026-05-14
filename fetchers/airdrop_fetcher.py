"""
Airdrop情報をWeb/APIから収集するモジュール。
- airdrops.io スクレイピング
- CoinGecko 新着コイン (エアドロップ候補)
- キュレーテッドシードデータ (定期メンテ)
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
    """airdrops.io のトップページからアクティブエアドロップを取得"""
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
        logger.info(f"airdrops.io: {len(items)}件取得")
        return items
    except Exception as e:
        logger.warning(f"airdrops.io scrape 失敗: {e}")
        return []


def _scrape_coingecko_candidates(new_coins: list[dict]) -> list[dict]:
    """
    CoinGecko 新着コインのうち、エアドロップ候補になりそうなものを返す。
    (上場直後の新規コインはエアドロップの可能性が高い)
    """
    candidates = []
    for coin in new_coins[:10]:
        coin_id = coin.get("id", "")
        name = coin.get("name", "")
        symbol = coin.get("symbol", "").upper()
        if not name or not coin_id:
            continue
        candidates.append({
            "id": f"cg-new-{coin_id}",
            "name": f"{name} ({symbol})",
            "symbol": symbol,
            "category": "新規上場",
            "type": "エアドロップ候補",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": f"CoinGeckoに新規上場。エアドロップ実施の可能性あり。要確認。",
            "tasks": ["公式サイト・Twitterをフォロー", "コミュニティ参加 (Discord/Telegram)", "ウォレット登録"],
            "end_date": "未定",
            "logo": coin.get("thumb", ""),
            "url": f"https://www.coingecko.com/en/coins/{coin_id}",
            "is_hot": False,
            "added_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "source": "coingecko-new",
        })
    return candidates


def _build_seed_airdrops() -> list[dict]:
    """手動管理の注目エアドロップシードデータ"""
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
            "estimated_value_usd": 1500,
            "description": "高速オンチェーン永久先物DEX。独自L1チェーン上で動作。取引量に応じたポイント報酬。月間取引量上位者へ大量配布実績あり。",
            "tasks": [
                "Hyperliquid上での先物取引 (毎日アクティブ推奨)",
                "流動性提供 (Vault参加)",
                "紹介プログラム参加",
                "HLPポイント蓄積",
            ],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "movement-move",
            "name": "Movement (MOVE)",
            "symbol": "MOVE",
            "category": "Layer2",
            "type": "テストネット",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 600,
            "description": "Move VMを搭載するEthereum L2。高速・低コストを実現。テストネット参加者へのエアドロップ予定あり。早期参加者ほど有利。",
            "tasks": [
                "テストネット参加 (公式サイトから登録)",
                "Discordコミュニティ参加・role取得",
                "テストトランザクション実行 (最低5回)",
                "公式Twitterフォロー・RT",
            ],
            "end_date": (today + timedelta(days=20)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39619/small/MOVE_color.png",
            "url": "https://movementlabs.xyz/",
            "is_hot": True,
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
            "description": "クロスチェーンメッセージングプロトコル。ブリッジ・DeFi利用実績のあるウォレットへ配布。多チェーン利用がポイント。",
            "tasks": [
                "Stargate経由でブリッジを実行 (複数チェーン推奨)",
                "複数チェーンでのトランザクション継続",
                "LayerZero対応dApps (Pancake, Sushiなど) 利用",
            ],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/28206/small/ftxG9_TJ_400x400.jpeg",
            "url": "https://layerzero.network/",
            "is_hot": True,
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
            "description": "EVM互換ZK-Rollup。Ethereum L2でのトランザクション実績でエアドロップ獲得可能。初心者向けで難易度低め。",
            "tasks": [
                "ScrollネットワークへETHブリッジ",
                "Scroll上でのDeFi利用 (Syncswap等)",
                "複数週にわたるアクティビティ継続",
            ],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/25734/small/scroll.png",
            "url": "https://scroll.io/",
            "is_hot": True,
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
            "description": "Ethereumのリステーキングプロトコル。ETHをステーキングし追加報酬を獲得。資金が必要だが報酬は大きい。",
            "tasks": [
                "ETHをEigenLayerにリステーキング",
                "LST (stETH, rETH等) をデポジット",
                "AVSへの参加 (オペレーター委任)",
            ],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/33751/small/eigen.png",
            "url": "https://eigenlayer.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "zksync-era",
            "name": "zkSync Era",
            "symbol": "ZK",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 200,
            "description": "Matter Labsが開発するZK-Rollup。エコシステムが急拡大中。早期から利用しているウォレット有利。",
            "tasks": [
                "zkSync Era上でのスワップ (Syncswap/Mute)",
                "zkSync公式ブリッジ利用",
                "NFT mint やDeFi利用",
            ],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/38043/small/ZKTokenBlack.png",
            "url": "https://zksync.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "kakarot-zkevm",
            "name": "Kakarot zkEVM",
            "symbol": "KRT",
            "category": "Layer2",
            "type": "テストネット",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "StarkNetベースのzkEVM。Ethereum互換のL2。大手VCが支援しており注目度が高い新興プロジェクト。",
            "tasks": [
                "テストネット参加登録",
                "Discordに参加しVerified取得",
                "テストETH取得 (Faucet利用)",
                "テストトランザクション実行",
            ],
            "end_date": (today + timedelta(days=40)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://www.kakarot.org/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "monad-mon",
            "name": "Monad",
            "symbol": "MON",
            "category": "Layer1",
            "type": "テストネット",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 1000,
            "description": "高性能EVM互換L1ブロックチェーン。10,000 TPS達成を目標。大型ファンディング済みで上場期待大。テストネット参加者へのエアドロップ噂あり。",
            "tasks": [
                "公式ウェイトリスト登録 (monad.xyz)",
                "Twitterフォロー・コミュニティ参加",
                "テストネット開始時に即参加",
            ],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://www.monad.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
    ]


def fetch_all_airdrops() -> tuple[list[dict], list[str]]:
    """
    全ソースからエアドロップデータを収集し、新着名リストと共に返す。
    Returns: (airdrops_list, new_items_names)
    """
    curated = _build_seed_airdrops()
    scraped = _scrape_airdrops_io()

    # CoinGecko 新着コインをエアドロップ候補として追加
    try:
        new_coins = get_new_coins()
        cg_candidates = _scrape_coingecko_candidates(new_coins)
    except Exception as e:
        logger.warning(f"CoinGecko新着取得失敗: {e}")
        cg_candidates = []

    seen_names = {a["name"].lower() for a in curated}
    new_items = []

    # airdrops.io スクレイピング結果をマージ
    for s in scraped:
        if s["name"].lower() not in seen_names:
            curated.append({
                "id": "aio-" + s["name"].lower().replace(" ", "-")[:30],
                "name": s["name"],
                "symbol": "",
                "category": "エアドロップ",
                "type": "エアドロップ",
                "status": "active",
                "difficulty": "easy",
                "estimated_value_usd": 0,
                "description": f"airdrops.io 掲載: {s.get('estimated_value', '')}",
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

    # CoinGecko 新着候補をマージ
    for c in cg_candidates:
        if c["name"].lower() not in seen_names:
            curated.append(c)
            seen_names.add(c["name"].lower())

    # ソート: ホット優先 → 推定価値降順
    curated.sort(key=lambda x: (not x.get("is_hot"), -x.get("estimated_value_usd", 0)))

    logger.info(
        f"fetch_all_airdrops: 計{len(curated)}件 "
        f"(curated={len(_build_seed_airdrops())}, "
        f"scraped={len(scraped)}, "
        f"cg_candidates={len(cg_candidates)}, "
        f"new={len(new_items)})"
    )
    return curated, new_items
