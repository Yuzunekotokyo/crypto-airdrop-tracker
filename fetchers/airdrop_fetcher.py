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
    """手動管理の注目エアドロップシードデータ (2026年7月時点の最新情報に基づき更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "grass-grass-s2",
            "name": "Grass Season 2 (GRASS)",
            "symbol": "GRASS",
            "category": "DePIN",
            "type": "レトロアクティブ Season2",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 150,
            "description": "未使用の帯域幅を提供してAI学習用データ収集に貢献するDePINプロジェクト。Season2で供給量の約17%(1.7億GRASS)を配布予定。7/22よりStage2分の請求受付開始。",
            "tasks": ["Grass拡張機能をインストールし接続を維持", "公式ダッシュボードでReward Checkerを確認", "7/22の請求受付開始後に公式ポータルからクレーム"],
            "end_date": "2027-01-22",
            "logo": "https://assets.coingecko.com/coins/images/38366/small/grass.png",
            "url": "https://app.getgrass.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-hype-s2",
            "name": "Hyperliquid Season 2 (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "取引所トークン ポイント",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "高速オンチェーン永久先物DEX。供給量の約38.9%が将来的な報酬用に確保されておりSeason2の原資と目される。HyperEVM開始で新たな稼働機会が拡大中。",
            "tasks": ["Hyperliquid Perpsで取引を継続", "HYPEをステーキング", "HyperEVMへブリッジしdApps利用"],
            "end_date": "未定(スナップショット日未発表)",
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "backpack-bp",
            "name": "Backpack Exchange (BP)",
            "symbol": "BP",
            "category": "取引所",
            "type": "取引所トークン",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "2026年3月23日にBACKPACKトークンをローンチ済み。供給量の25%がコミュニティ配分(Season4ポイント保有者へ2.4億枚、Mad Lads保有者へ1000万枚)。継続的なSeason4ポイント稼働で追加配分の可能性。",
            "tasks": ["KYC済Backpack Exchangeアカウントを作成", "Backpack Walletをインストール", "取引量を積みSeason4ポイントを獲得"],
            "end_date": "継続中(ポイントは毎週金曜更新)",
            "logo": "https://assets.coingecko.com/coins/images/39676/small/backpack.png",
            "url": "https://backpack.exchange/bp",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ(予定)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "世界最大級の予測市場プラットフォーム。2025年10月にCMOがPOLYトークンとエアドロップ計画を公式確認。供給量の5〜10%をエアドロップ参加者に配分予定。米国プラットフォーム安定化後、2026年後半のトークンイベントが有力視。",
            "tasks": ["Polymarketで予測市場に参加・取引", "米国プラットフォームでの利用実績を積む", "公式XやDiscordで最新情報を確認"],
            "end_date": "未定(2026年後半の可能性)",
            "logo": "https://assets.coingecko.com/coins/images/41482/small/polymarket.png",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-token",
            "name": "Base Token (Coinbase)",
            "symbol": "BASE",
            "category": "Layer2",
            "type": "検討中(未確定)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Base創設者Jesse Pollak氏が2025年9月にネットワークトークンの検討を公式表明。JPMorganアナリストは時価総額120〜340億ドルと試算。Coinbaseが公開企業のため規制面のハードルは大きいが、2026年Q2〜Q4のロールアウト観測も。",
            "tasks": ["Base上でトランザクション/dApps利用実績を積む", "公式発表(Jesse Pollak氏のX等)を継続的にウォッチ"],
            "end_date": "未定(公式未発表)",
            "logo": "https://assets.coingecko.com/coins/images/32411/small/base.png",
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
