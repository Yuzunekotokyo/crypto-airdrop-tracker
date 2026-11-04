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
    """手動管理の注目エアドロップシードデータ (定期的に更新)"""
    today = datetime.utcnow()
    return [
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
            "tasks": ["Stargate経由でブリッジを実行", "複数チェーンでのトランザクション", "LayerZero対応dApps利用"],
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
            "description": "EVM互換ZK-Rollup。Ethereum L2でのトランザクション実績でエアドロップ獲得可能。",
            "tasks": ["ScrollネットワークへETHブリッジ", "Scroll上でのDeFi利用", "複数週にわたるアクティビティ"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/25734/small/scroll.png",
            "url": "https://scroll.io/",
            "is_hot": True,
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
            "description": "Matter Labsが開発するZK-Rollup。エコシステムが急拡大中。",
            "tasks": ["Era上でのスワップ", "Syncswap/Mute利用", "zkSync公式ブリッジ利用"],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/38043/small/ZKTokenBlack.png",
            "url": "https://zksync.io/",
            "is_hot": False,
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
            "estimated_value_usd": 1000,
            "description": "高速オンチェーン永久先物DEX。独自L1チェーン上で動作。取引量によるポイント報酬。",
            "tasks": ["Hyperliquid上での先物取引", "流動性提供", "紹介プログラム参加"],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
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
            "description": "Ethereumのリステーキングプロトコル。ETHをステーキングし追加報酬を獲得。",
            "tasks": ["ETHをリステーキング", "LST (stETH等) をデポジット", "AVSへの参加"],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/33751/small/eigen.png",
            "url": "https://eigenlayer.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
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
            "end_date": (today + timedelta(days=20)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39619/small/MOVE_color.png",
            "url": "https://movementlabs.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "standx-dusd",
            "name": "StandX (DUSD)",
            "symbol": "DUSD",
            "category": "DeFi/DEX",
            "type": "クレーム受付中",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "【2026-11-02 クレーム開始】TGEはキャンセルされ、過去のプラットフォーム利用実績に基づく配布のみ実施。クレーム期限は2026-12-31。",
            "tasks": ["公式サイトでクレーム可否を確認", "ウォレット接続してクレーム"],
            "end_date": "2026-12-31",
            "logo": "",
            "url": "https://standx.com/",
            "is_hot": True,
            "added_date": "2026-11-04",
            "source": "cryptoticker / coingabbar",
        },
        {
            "id": "aster-stage6",
            "name": "Aster (ASTER) Stage 6",
            "symbol": "ASTER",
            "category": "DeFi/DEX",
            "type": "クレーム受付中",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Stage 6のフルアロケーションのクレームが2026-10-28 12:00 UTCから開始。期限は2026-11-28 12:00 UTC。",
            "tasks": ["対象ウォレットでクレーム"],
            "end_date": "2026-11-28",
            "logo": "",
            "url": "https://www.asterdex.com/",
            "is_hot": False,
            "added_date": "2026-11-04",
            "source": "cryptoticker",
        },
        {
            "id": "doppler-xdp",
            "name": "Doppler Finance (XDP)",
            "symbol": "XDP",
            "category": "DeFi/DEX",
            "type": "ジェネシスエアドロップ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "XDP Genesis Airdropのクレームが受付中。期限は2026-11-28 12:00 UTC。",
            "tasks": ["対象ウォレットでクレーム"],
            "end_date": "2026-11-28",
            "logo": "",
            "url": "https://doppler.finance/",
            "is_hot": False,
            "added_date": "2026-11-04",
            "source": "cryptoticker",
        },
        {
            "id": "lia-labs",
            "name": "Lia Labs (LIA)",
            "symbol": "LIA",
            "category": "その他",
            "type": "アプリ連動",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "LIAトークンを公式Xで発表。エアドロップは今後のアプリ更新(iOS/Android)経由で配布予定。詳細・日程は未確定。",
            "tasks": ["公式アプリをインストール", "公式Xで続報を確認"],
            "end_date": "未定",
            "logo": "",
            "url": "https://x.com/",
            "is_hot": False,
            "added_date": "2026-11-04",
            "source": "coingabbar",
        },
        {
            "id": "predict-fun",
            "name": "Predict.fun",
            "symbol": "",
            "category": "DeFi/DEX",
            "type": "ポイントプログラム",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "予測市場。10/6にトークンティザー公開済みだがスナップショット日・トークン詳細は未発表。非公式の日付情報に注意。",
            "tasks": ["ポイント獲得のため予測市場を利用", "公式のスナップショット告知を待つ"],
            "end_date": "未定",
            "logo": "",
            "url": "https://predict.fun/",
            "is_hot": False,
            "added_date": "2026-11-04",
            "source": "bitrue",
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
