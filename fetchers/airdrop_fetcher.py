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
            "id": "meteora-met",
            "name": "Meteora (MET)",
            "symbol": "MET",
            "category": "DeFi/DEX",
            "type": "LPクレーム",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Season 2 LP報酬のクレーム期間。期限は2026-10-21（時刻・タイムゾーン不明のため当日中に）。",
            "tasks": "['公式サイトでウォレットの対象確認','Season 2 LP報酬をクレーム']",
            "end_date": "2026-10-21",
            "logo": "",
            "url": "https://meteora.ag/",
            "is_hot": True,
            "added_date": "2026-10-18",
            "source": "curated",
        },
        {
            "id": "pharos-pros",
            "name": "Pharos (PROS)",
            "symbol": "PROS",
            "category": "Layer1",
            "type": "クレーム",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "2026-04-28開始・180日間のエアドロップ。最終日は10/25頃。未請求分はFoundationに返却。",
            "tasks": "['公式クレームページで対象確認','期限前にクレーム']",
            "end_date": "2026-10-25",
            "logo": "",
            "url": "https://pharos.xyz/",
            "is_hot": True,
            "added_date": "2026-10-18",
            "source": "curated",
        },
        {
            "id": "questflow-arena-s3",
            "name": "Questflow Trader Arena S3",
            "symbol": "",
            "category": "AI/Base",
            "type": "トレード大会",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "Base上のトレーダーアリーナ Season 3（8/24〜10/24）。",
            "tasks": "['Base上でArenaに参加','期間中のトレード成績を積む']",
            "end_date": "2026-10-24",
            "logo": "",
            "url": "https://questflow.ai/",
            "is_hot": False,
            "added_date": "2026-10-18",
            "source": "curated",
        },
        {
            "id": "ekiden",
            "name": "Ekiden",
            "symbol": "",
            "category": "DeFi/DEX",
            "type": "ポイント",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "Ekidenがメインネット連動のリワード（取引ポイント→エアドロ）を確認済み（10/16付）。テストネット上位トレーダーに招待制の早期アクセス。注目の新規案件。",
            "tasks": "['テストネットで取引','取引量でポイント獲得','公式Xで招待情報を確認']",
            "end_date": "未定",
            "logo": "",
            "url": "https://ekiden.fi/",
            "is_hot": True,
            "added_date": "2026-10-18",
            "source": "curated",
        },
        {
            "id": "tastyco-tasty",
            "name": "TastyCo ($TASTY)",
            "symbol": "TASTY",
            "category": "その他",
            "type": "ポイント",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "TGE前にポイントを貯めた初期ユーザー向けに$100,000相当の$TASTYを配布予定。",
            "tasks": "['ポイントを獲得（TGE前）']",
            "end_date": "未定",
            "logo": "",
            "url": "https://x.com/",
            "is_hot": False,
            "added_date": "2026-10-18",
            "source": "curated",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "未確定",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "CMOがトークン/エアドロに言及（2025年）が、ヘルプセンターは『トークン未発表』と記載。公式発表まで未確定。偽クレームリンクに注意。",
            "tasks": "['公式発表を待つ','Polymarketで通常利用']",
            "end_date": "未定",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": False,
            "added_date": "2026-10-18",
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
