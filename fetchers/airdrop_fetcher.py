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
    """手動管理の注目エアドロップシードデータ (2026年7月時点の実際の状況を反映して定期更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "grass-stage2",
            "name": "Grass Stage 2 Claim",
            "symbol": "GRASS",
            "category": "DePIN",
            "type": "レトロアクティブ (USDC建て)",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 50,
            "description": "未使用の帯域幅を提供するDePINネットワーク。Stage 2はGRASSトークンではなくUSDC建てで、総額約300万ドルを2024年10月〜2026年6月のポイント実績に応じて配布。",
            "tasks": ["Grassダッシュボードでウォレット接続", "Allocationタブでクレーム申請を確認", "自己管理ウォレットへのUSDC着金を待つ"],
            "end_date": "2027-01-22",
            "logo": "https://assets.coingecko.com/coins/images/51872/small/Grass_200x200_%281%29.png",
            "url": "https://www.grass.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
            "notes": "クレーム開始: 2026年7月22日 13:00 EST",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "トークン未発行 (確定済みエアドロップ)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "CMOがPOLYトークンとエアドロップ実施を公式に明言。米国での事業再開後、2026年後半のローンチが有力視されている。配分基準は未発表だが、累計取引量・カテゴリ横断の利用実績が重視される見込み。",
            "tasks": ["Polymarketアカウント作成", "Web3ウォレット接続", "政治・スポーツ・経済等ジャンル横断で取引", "X (旧Twitter) アカウント連携"],
            "end_date": "未定 (2026年後半見込み)",
            "logo": "https://assets.coingecko.com/coins/images/45581/small/polymarket.jpg",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-token-speculative",
            "name": "Base (Coinbase L2) 潜在トークン",
            "symbol": "—",
            "category": "Layer2",
            "type": "トークン未発表 (投機的)",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "CoinbaseのL2、Baseはネットワークトークン発行を「検討中」と公式に認めているが、正式発表・配布方式・時期は未確定。市場予測では2026年中の発表確度は五分五分程度。JPMorganはトークン化時価総額を120〜340億ドルと試算。",
            "tasks": ["Base上でのスワップ・ブリッジ実績を積む", "Base対応dAppsの継続利用", "公式アナウンスを定期チェック"],
            "end_date": "未定 (トークン未確定)",
            "logo": "https://assets.coingecko.com/asset_platforms/images/131/small/base-network.png",
            "url": "https://base.org/",
            "is_hot": True,
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
