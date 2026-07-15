"""
Airdrop情報をWeb/APIから収集するモジュール。
現在はairdrops.ioのパブリックページとCoinGeckoトレンドを組み合わせて使用。
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
    """手動管理の注目エアドロップシードデータ。
    2026年7月時点のWeb検索結果に基づき随時更新 (LayerZero/Scroll/zkSync/EigenLayer/
    Hyperliquid/Movement等は既にTGE済みのため除外し、現在進行中の案件に差し替え)。
    """
    today = datetime.utcnow()
    return [
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場/DeFi",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "分散型予測市場のトップランナー。CMOがトークン発行とエアドロップ実施を公式に明言。"
                           "現行の流動性リワードプログラムは2026年7月19日終了予定のため参加はお早めに。"
                           "供給の約5〜10%がアクティブユーザー向けに配分される見込み。",
            "tasks": ["複数カテゴリでの継続的な取引", "X(Twitter)アカウントの連携", "Rewardsプログラムへの参加"],
            "end_date": "2026-07-19",
            "logo": "https://assets.coingecko.com/coins/images/42563/small/polymarket.jpg",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-token",
            "name": "Base",
            "symbol": "",
            "category": "Layer2",
            "type": "投機的 (トークン未発行)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Coinbase運営のL2。2025年9月にリード開発者がネットワークトークン検討を公式表明。"
                           "Polymarketの予測市場では2026年内のトークン化確率69%と観測されており注目度が高い。",
            "tasks": ["Base上でのDeFi/dApps継続利用", "公式ブリッジの利用", "エコシステムdAppsとのインタラクション"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/asset_platforms/images/131/small/base.jpeg",
            "url": "https://base.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "zama-fhevm",
            "name": "Zama (fhEVM)",
            "symbol": "",
            "category": "プライバシー/AI",
            "type": "テストネット",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "完全準同型暗号(FHE)による機密計算プロトコル。fhEVMテストネットが稼働中で、"
                           "2026年前半〜中盤のメインネット/トークンローンチが有力視されているAI系注目候補。",
            "tasks": ["fhEVMテストネットでの暗号化トランザクション実行", "スマートコントラクトのデプロイ", "ネットワークアクティビティへの貢献"],
            "end_date": "未定",
            "logo": "",
            "url": "https://www.zama.ai/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "bitcoin-hyper",
            "name": "Bitcoin Hyper (HYPER)",
            "symbol": "HYPER",
            "category": "Bitcoin Layer2",
            "type": "プレセール",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "BTCエコシステムにDeFi/エアドロップ機能を統合するBitcoin L2。プレセールで既に$32.75M超を調達。"
                           "プレセール型のため投機性・リスクが高い点に注意。",
            "tasks": ["公式コミュニティでのアクティビティ", "テストネット参加 (提供時)"],
            "end_date": "未定",
            "logo": "",
            "url": "https://bitcoinhyper.com/",
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
