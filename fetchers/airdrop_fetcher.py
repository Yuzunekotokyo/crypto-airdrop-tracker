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
    """手動管理の注目エアドロップシードデータ (2026年9月時点の最新情報でリサーチ・更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "grass-season2",
            "name": "Grass Season 2 (GRASS)",
            "symbol": "GRASS",
            "category": "DePIN",
            "type": "クレーム受付中",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 600,
            "description": (
                "帯域幅シェア型DePINプロジェクト。Season 2クレームが開始済み。"
                "2024年10月〜2026年6月の対象期間にアクティビティがあったユーザーはGrass Walletから"
                "USDC/GRASS報酬を今すぐ受け取り可能。約1.7億GRASS(全供給の約17%)を配布予定。"
            ),
            "tasks": [
                "Grass Wallet で対象期間 (2024/10〜2026/6) の適格性を確認",
                "ウォレット接続してクレームを実行",
                "2027年1月20日の受取期限までに必ず請求する (期限超過で権利失効)",
            ],
            "end_date": "2027-01-20",
            "logo": "https://assets.coingecko.com/coins/images/51942/small/Grasslogo.jpg",
            "url": "https://www.grass.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-season2",
            "name": "Hyperliquid Season 2 (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX (Perps)",
            "type": "ポイントファーミング",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1200,
            "description": (
                "高速オンチェーン永久先物DEX。2025年12月からSeason 2のポイント付与が開始済みで"
                "スナップショット日は未発表。全供給の38.888%がシーズンをまたいで配布される設計。"
            ),
            "tasks": [
                "Hyperliquid上で継続的に先物取引を行う (取引量・OIでポイント加算)",
                "$HYPEをステーキング (1トークンあたり1日8ポイント)",
                "ステーキングを取引アカウントにリンクして手数料減免+スナップショット加重を得る",
            ],
            "end_date": "未定 (スナップショット日未発表)",
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "トークン未上場 (計画中)",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 2000,
            "description": (
                "最大手の分散型予測市場。コミュニティへ約7.5億ドル相当のPOLYエアドロップを計画中と表明。"
                "米国での正式サービス再開後にトークン配布時期が固まる見通しで、正式な適格基準は未公表。"
            ),
            "tasks": [
                "Polymarketで実際に予測市場に参加 (取引・流動性提供)",
                "米国向けサービス再開後の追加キャンペーンに注目",
                "公式アカウント以外の『適格基準確定』情報は詐欺の可能性があるため注意",
            ],
            "end_date": "未定 (時期未確定)",
            "logo": "https://assets.coingecko.com/coins/images/35331/small/polymarket.jpg",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "lighter-perp",
            "name": "Lighter (無期限DEX)",
            "symbol": "LIT?",
            "category": "DeFi/DEX (Perps)",
            "type": "ポイントファーミング (TGE前)",
            "status": "active",
            "difficulty": "hard",
            "estimated_value_usd": 300,
            "description": (
                "ZK技術を使うオーダーブック型永久先物DEX。毎週金曜に20万ポイントをリテール層に配布中。"
                "トークン化・クレームは2026年8月時点でも未確定のため、公式発表のみを信頼すること。"
            ),
            "tasks": [
                "app.lighter.xyz でウォレット接続し本人確認 (Discord連携)",
                "実際の売買で出来高・建玉を積む (自己売買/シビル行為はポイント対象外)",
                "無理な損切り・清算はポイントにならないため注意",
            ],
            "end_date": "未定 (TGE未確定)",
            "logo": "",
            "url": "https://app.lighter.xyz/",
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
