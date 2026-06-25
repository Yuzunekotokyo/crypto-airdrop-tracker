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
    """手動管理の注目エアドロップシードデータ — 2026年版"""
    today = datetime.utcnow()
    return [
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "ウォレット",
            "type": "リワードポイント",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 2000,
            "description": "世界最大の暗号資産ウォレット。MASKトークンを確認済み。MetaMask Rewardsシーズン2稼働中。スワップ・ブリッジ・先物取引でポイント獲得。Q3〜Q4 2026 TGE予想。",
            "tasks": [
                "MetaMask Rewardsに登録・オプトイン",
                "MetaMaskでトークンスワップ",
                "MetaMask Bridgeでクロスチェーン送金",
                "先物取引 (MetaMask Perps) の活用",
                "友人を紹介 (250ポイント / 紹介ごと)",
            ],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/13669/small/meta-mask.png",
            "url": "https://metamask.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-token",
            "name": "Base Token",
            "symbol": "BASE",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 5000,
            "description": "CoinbaseのEthereum L2。JPMorganは潜在的トークン時価総額を$120〜340億と試算。2026年最大のワイルドカード。エコシステムの積極利用が鍵。",
            "tasks": [
                "BaseにETHをブリッジ (公式Bridge使用)",
                "Aerodrome / Uniswap v3でスワップ",
                "Base上DeFi (Moonwell, Aave等) を利用",
                "複数月にわたる継続的なアクティビティ",
                "Base上でのNFT mint / 取引",
            ],
            "end_date": (today + timedelta(days=270)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/asset_platforms/images/131/small/base-network-logo.png",
            "url": "https://base.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1500,
            "description": "世界最大の分散型予測市場。CMOがトークン・エアドロップを確認済み。米国正式ローンチ後のTGE予定 (late 2026)。アンチシビル対策が厳重。",
            "tasks": [
                "複数カテゴリ (政治・暗号・スポーツ等) で継続的に取引",
                "X (Twitter) アカウントを設定でリンク",
                "Polymarket Rewardsプログラムに参加",
                "複数ウォレットの使用厳禁",
            ],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/28838/small/polymarket-200x200.png",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "kraken-ink",
            "name": "Kraken Ink (INK)",
            "symbol": "INK",
            "category": "Layer2",
            "type": "新規TGE",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "KrakenがインキュベートするOP Stack L2。2026年4月13日に最初のポイント配布済み。Kraken Proでの取引がポイント源。Q3〜Q4 2026 TGE予想。",
            "tasks": [
                "Kraken Proでスポット・先物取引",
                "InkネットワークへETHをブリッジ",
                "Ink上DeFi: Nado (先物), Tydro (レンディング), Velodrome (LP)",
                "Kraken Drops プログラムの確認・登録",
            ],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/asset_platforms/images/279/small/ink.jpeg",
            "url": "https://inkonchain.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-season2",
            "name": "Hyperliquid Season 2",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "取引所トークン",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1000,
            "description": "高速オンチェーン永久先物DEX。シーズン2稼働中でトレーダーポイントを継続配布。独自L1チェーン上で動作し、取引量に応じたポイント報酬制度。",
            "tasks": [
                "Hyperliquid上での永久先物取引",
                "流動性提供 (HLP Vault)",
                "紹介プログラムへの参加",
            ],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
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
            "description": "Ethereumのリステーキングプロトコル。複数シーズンのエアドロップが進行中。ETHをリステーキングし、AVS参加で追加報酬を獲得。",
            "tasks": [
                "ETHまたはLST (stETH, rETH等) をリステーキング",
                "EigenDA / AVSサービスへの参加",
                "長期ロックアップでポイント倍率アップ",
            ],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
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
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 500,
            "description": "クロスチェーンメッセージングプロトコル。Stargate経由のブリッジ利用者向けに継続的なインセンティブプログラムが実施中。",
            "tasks": [
                "Stargate経由でブリッジを実行",
                "複数チェーンでのトランザクション",
                "LayerZero対応dApps利用",
            ],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/28206/small/ftxG9_TJ_400x400.jpeg",
            "url": "https://layerzero.network/",
            "is_hot": False,
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
            "description": "EVM互換ZK-Rollup。Ethereum L2でのトランザクション実績でエアドロップ獲得可能。追加インセンティブが予定されている。",
            "tasks": [
                "ScrollネットワークへETHブリッジ",
                "Scroll上でのDeFi利用",
                "複数週にわたるアクティビティ",
            ],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/25734/small/scroll.png",
            "url": "https://scroll.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "movement-move",
            "name": "Movement (MOVE)",
            "symbol": "MOVE",
            "category": "Layer2",
            "type": "テストネット参加",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "Move VMを使用するEthereum L2。テストネット参加者向けエアドロップが進行中。高速・低コストトランザクションが特徴。",
            "tasks": [
                "テストネット参加",
                "Discordコミュニティ参加",
                "テストトランザクション実行",
            ],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39619/small/MOVE_color.png",
            "url": "https://movementlabs.xyz/",
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
