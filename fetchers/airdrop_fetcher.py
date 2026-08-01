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
    """手動管理の注目エアドロップシードデータ (2026年8月時点の最新情報を反映)"""
    today = datetime.utcnow()
    return [
        {
            "id": "base-network-token",
            "name": "Base Network Token",
            "symbol": "BASE",
            "category": "Layer2",
            "type": "レトロアクティブ (未確定)",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 1200,
            "description": "CoinbaseのL2「Base」が独自トークン発行を検討中と公式表明。実現すれば過去最大級のエアドロップになる可能性 (時価総額$12〜34B予想)。Polymarketの予測市場では2026年内のトークン発行確率69%。",
            "tasks": ["Base上でのDeFi/DEX利用実績を積む", "Base公式dAppsの継続利用", "Coinbase Walletでのオンチェーン活動"],
            "end_date": "未定 (2026年Q2〜Q4に検討中)",
            "logo": "https://assets.coingecko.com/asset_platforms/images/131/small/base-network.png",
            "url": "https://base.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "opensea-sea",
            "name": "OpenSea (SEA)",
            "symbol": "SEA",
            "category": "NFT",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 500,
            "description": "NFTマーケットプレイス最大手。供給の50%をコミュニティに配分予定と公式発表。当初2026年Q1予定だったが市場環境により延期中、新日程は未発表。KYC不要で請求可能と案内。",
            "tasks": ["OpenSeaでの売買・出品実績", "OpenSea Rewardsプログラム参加", "ウォレット接続によるXP蓄積"],
            "end_date": "未定 (Q1 2026予定より延期)",
            "logo": "https://assets.coingecko.com/coins/images/1359/small/opensea.png",
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
            "difficulty": "hard",
            "estimated_value_usd": 400,
            "description": "世界最大の予測市場プラットフォーム。CMOが「トークンとエアドロップは実施する」と明言。米国での正式サービス再開後の実施が濃厚。配分基準は取引量・市場の多様性・継続性が有力視。",
            "tasks": ["複数カテゴリでの予測市場取引", "継続的な取引履歴の構築", "勝利ポジションの再投資", "X(旧Twitter)アカウント連携"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/markets/images/1157/small/polymarket.jpg",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "aster-stage",
            "name": "Aster (ASTER) 次期ステージ",
            "symbol": "ASTER",
            "category": "DeFi/DEX",
            "type": "ポイント配布",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 350,
            "description": "永久先物DEX。多段階ステージ形式でトークンを継続配布中 (Stage 6は2026年2〜3月に供給の0.8%=約6,400万ASTERを配布済)。取引量・ポジション保有・紹介ポイントで次期ステージの配分が決定。",
            "tasks": ["Asterでの先物取引によるポイント獲得", "ポジション保有期間の維持", "紹介プログラム経由の招待", "$ASTER資産の保有"],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39803/small/aster.png",
            "url": "https://www.asterdex.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "grass-season2",
            "name": "Grass Season 2",
            "symbol": "GRASS",
            "category": "DePIN",
            "type": "レトロアクティブ (未確定)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 250,
            "description": "未使用の帯域幅を提供するDePINプロジェクト。2026年後半に約1.7億GRASS(供給の約17%)のSeason 2配布が噂されるが財団未公式発表。直近のStage 2報酬はUSDC建てで請求受付中。",
            "tasks": ["Grassブラウザ拡張機能/アプリの常時起動", "帯域幅提供の継続", "公式アプリ内ウォレットの登録"],
            "end_date": "未定 (2026年後半見込み)",
            "logo": "https://assets.coingecko.com/coins/images/38108/small/grass.png",
            "url": "https://www.grass.io/",
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
