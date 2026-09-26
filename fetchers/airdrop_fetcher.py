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
    2026年9月時点の最新情報に基づき更新 (LayerZero/Scroll/zkSync/Hyperliquid/
    EigenLayer/Movement/Monad/Fogo/MegaETHは既にTGE・クレーム済のため一覧から除外)。
    """
    today = datetime.utcnow()
    return [
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場/DeFi",
            "type": "レトロアクティブ (未確定)",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 1500,
            "description": "世界最大の分散型予測市場。CMOがトークン・エアドロップの実施を公言済みだが、スナップショット日・配布基準は未発表。取引量・市場の多様性・継続性・X連携が有力な評価軸と見られる。",
            "tasks": ["Polymarketで実際に予測市場取引を行う", "複数カテゴリの市場で取引する", "継続的にアクティビティを維持する", "Xアカウントを連携する"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/prediction-market/polymarket.png",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "canopy-cnpy",
            "name": "Canopy (CNPY)",
            "symbol": "CNPY",
            "category": "インフラ/L1",
            "type": "テストネット",
            "status": "active",
            "difficulty": "hard",
            "estimated_value_usd": 700,
            "description": "Arrington Capital・Fenbushi等が出資するアプリチェーンL1フレームワーク。2026年2月12日からパブリックテストネット稼働中で、供給の50%をコミュニティ配分予定という現存案件の中でも最大級のコミュニティ配分比率。",
            "tasks": ["パブリックテストネットに参加", "ノード運用/バリデーション関連タスク", "継続的なオンチェーンアクティビティ"],
            "end_date": "未定",
            "logo": "",
            "url": "https://canopynetwork.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "zerofi-protocol",
            "name": "ZeroFi Protocol",
            "symbol": "",
            "category": "プライバシー/DeFi",
            "type": "テストネット",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "プライバシー重視のDeFiプロトコル。秘匿トランザクションのテストネット参加者向けに将来的な報酬が見込まれる新興案件。",
            "tasks": ["テストネットで秘匿トランザクションを試す", "コミュニティ(Discord等)への参加"],
            "end_date": "未定",
            "logo": "",
            "url": "https://airdrops.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-token-rumor",
            "name": "Base (Coinbase L2)",
            "symbol": "BASE?",
            "category": "Layer2",
            "type": "噂・未確定",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "⚠️未確定情報: Coinbase創業のBaseがネイティブトークン発行を検討中と2025年9月に公表 (2026年7月時点でも正式発表なし)。実現すればJPMorgan試算で時価総額120〜340億ドル規模とされるが、規制上の制約もあり不透明。既存のBaseネットワーク利用実績は将来の判定材料になり得る。",
            "tasks": ["Base上でのブリッジ/スワップ等の通常利用を継続 (トークン化は未確定のため過度な農作業は非推奨)"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/base.png",
            "url": "https://base.org/",
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
