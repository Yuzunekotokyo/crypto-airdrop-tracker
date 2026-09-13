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
    """手動管理の注目エアドロップシードデータ (2026年9月時点の情報に更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "opensea-sea",
            "name": "OpenSea (SEA)",
            "symbol": "SEA",
            "category": "NFT/マーケットプレイス",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "最大手NFTマーケットプレイス。供給量の50%をコミュニティに割当。OS2のXPシステム(Voyages/Treasure Chest)と過去の取引履歴でスコアリング。最終報酬フェーズが9/15開始予定で配布が目前に迫っている最重要案件。",
            "tasks": ["OpenSea 2.0でNFT取引を行う", "Treasure Chest/Voyagesに参加してXPを獲得", "ウォレットをOS2にリンクして待機リスト登録"],
            "end_date": (today + timedelta(days=10)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/2680/small/opensea.png",
            "url": "https://opensea.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ (未確定)",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "世界最大の予測市場プラットフォーム。CMOが「トークンとエアドロップは実施する」と公式に言及済みだが、日程・配布基準は未発表。継続的な取引実績が重要と見られる。",
            "tasks": ["複数カテゴリで継続的に予測市場に参加", "X(Twitter)アカウントを連携", "Rewardsプログラムに参加"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/48312/small/polymarket.png",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-token",
            "name": "Base (未発行トークン)",
            "symbol": "BASE",
            "category": "Layer2",
            "type": "検討中",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "Coinbase運営のEthereum L2、L2 DeFi TVLの約46.6%を占める最大手。ネットワークトークン発行をCoinbaseが検討中と公式に言及。予測市場では2026年末までの発行確率が高いとされる。公式のクレーム窓口はまだ存在せずエアドロップを騙る詐欺サイトに注意。",
            "tasks": ["Baseチェーン上でオンチェーン活動履歴を積む", "Base上のdAppsを継続的に利用", "公式アナウンス以外のクレームサイトには絶対アクセスしない"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/33081/small/base.png",
            "url": "https://base.org/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "openledger-open",
            "name": "OpenLedger (OPEN)",
            "symbol": "OPEN",
            "category": "AI/データ",
            "type": "テストネット参加型",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "AIデータ提供・学習に特化したブロックチェーン。テストネット参加やノード運用を通じたポイント制エアドロップキャンペーンを実施中。",
            "tasks": ["テストネットに参加", "データセット提供/検証タスクをこなす", "コミュニティ(Discord等)での活動"],
            "end_date": "未定",
            "logo": "",
            "url": "https://openledger.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "monad-mon",
            "name": "Monad (MON)",
            "symbol": "MON",
            "category": "Layer1",
            "type": "レトロアクティブ",
            "status": "ended",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "高速並列EVM互換L1。2025年11月にメインネット稼働とMONトークンのエアドロップ配布が完了済み(約7.6万ウォレットに配布)。新規クレームは終了。",
            "tasks": [],
            "end_date": "2025-11-03",
            "logo": "https://assets.coingecko.com/coins/images/31258/small/monad.png",
            "url": "https://monad.xyz/",
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
