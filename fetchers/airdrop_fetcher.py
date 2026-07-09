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
        # ── 現在アクティブ/近日予定の注目案件 ──────────────────────────
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 600,
            "description": "予測市場最大手。ワールドカップ2026関連マーケットで$100万規模の流動性インセンティブ実施中 (6/11〜7/19)。QCX買収による米国正式再上陸後にTGE観測。",
            "tasks": ["Polymarketでの取引・指値注文の投稿", "Xアカウントの連携", "マーケットメイクへの参加"],
            "end_date": "2026-07-19",
            "logo": "https://assets.coingecko.com/coins/images/49312/small/polymarket.png",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "backpack-token",
            "name": "Backpack Exchange",
            "symbol": "BACKPACK",
            "category": "取引所",
            "type": "取引所トークン",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 750,
            "description": "2026/2/9にTGE配分方針を公式発表 (コミュニティに25% ・ ポイント保有者24% ・ Mad Lads保有者1%)。エアドロップ実施がほぼ確実視されている最有力案件。",
            "tasks": ["Backpack取引所でのポイント獲得", "Mad Lads NFTの保有", "継続的な取引量の積み上げ"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/40001/small/backpack.png",
            "url": "https://backpack.exchange/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "ウォレット",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "最大手Web3ウォレット。ポイントプログラムがMASKトークン・手数料割引に転換予定。スワップ・ブリッジ利用が対象。",
            "tasks": ["MetaMask内でのスワップ実行", "ブリッジ機能の利用", "Rewardsポイントの蓄積"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/40898/small/metamask.png",
            "url": "https://metamask.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-l2",
            "name": "Base",
            "symbol": "—",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 350,
            "description": "Coinbase運営のEthereum L2。トークン自体は未発表だが、最有力の潜在エアドロップ案件の一つとしてオンチェーン活動が継続的に追跡されている。",
            "tasks": ["Base上でのdApps利用", "ETHのブリッジ実行", "エコシステムキャンペーン参加"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/28205/small/base.jpeg",
            "url": "https://base.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "opensea-sea",
            "name": "OpenSea",
            "symbol": "—",
            "category": "NFTマーケットプレイス",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "NFT最大手マーケットプレイス。2026年に最も期待されるエアドロップ候補の一つとして継続的に名前が挙がる。",
            "tasks": ["OpenSeaでのNFT売買", "OS2新機能の利用", "コミュニティ参加"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/47040/small/opensea.png",
            "url": "https://opensea.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        # ── 配布・TGE完了済み (参考/実績記録) ──────────────────────────
        {
            "id": "monad-mon",
            "name": "Monad (MON)",
            "symbol": "MON",
            "category": "Layer1",
            "type": "レトロアクティブ",
            "status": "ended",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "2025/11/24にメインネット稼働と同時にMONトークンを配布済み。約22.5万ウォレットが受給、うち76,021ウォレットが実際にクレーム完了。",
            "tasks": [],
            "end_date": "2025-11-24 (配布終了)",
            "logo": "https://assets.coingecko.com/coins/images/35123/small/monad.png",
            "url": "https://monad.xyz/",
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
            "status": "ended",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "2024年にZROトークンを配布済み。クロスチェーンメッセージングプロトコル。",
            "tasks": [],
            "end_date": "2024年配布終了",
            "logo": "https://assets.coingecko.com/coins/images/28206/small/ftxG9_TJ_400x400.jpeg",
            "url": "https://layerzero.network/",
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
            "status": "ended",
            "difficulty": "hard",
            "estimated_value_usd": 0,
            "description": "2024年にEIGENトークンを配布済み。Ethereumのリステーキングプロトコル。",
            "tasks": [],
            "end_date": "2024年配布終了",
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
            "status": "ended",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "2024年にZKトークンを配布済み。Matter Labsが開発するZK-Rollup。",
            "tasks": [],
            "end_date": "2024年配布終了",
            "logo": "https://assets.coingecko.com/coins/images/38043/small/ZKTokenBlack.png",
            "url": "https://zksync.io/",
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
