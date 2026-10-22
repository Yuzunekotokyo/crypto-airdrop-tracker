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
    added = today.strftime("%Y-%m-%d")

    def item(**kw):
        base = {
            "symbol": "", "category": "その他", "type": "エアドロップ", "status": "active",
            "difficulty": "easy", "estimated_value_usd": 0, "tasks": [], "logo": "",
            "is_hot": False, "added_date": added, "source": "curated",
        }
        base.update(kw)
        return base

    return [
        item(
            id="axis-robotics", name="Axis Robotics (AXIS)", symbol="AXIS", category="AI/ロボティクス",
            type="ポイント/TGE予定", status="upcoming", difficulty="medium", estimated_value_usd=500,
            description="ロボティクスAI。供給量の10%を2シーズンでエアドロップ予定。TGE日・配布日は未発表(未確定情報あり)。ポイントはTGEでの転換が保証されていない点に注意。",
            tasks=["Axisのタスク/ポイント活動に参加", "公式発表(TGE日)を確認"],
            end_date="未定", url="https://cryptorank.io/drophunting/axis-ai-activity1105", is_hot=True,
        ),
        item(
            id="pharos-pros", name="Pharos (PROS)", symbol="PROS", category="Layer1",
            type="クレーム受付", status="active", estimated_value_usd=300,
            description="Pharosのクレームポータルが10/25に閉鎖。未請求分はPharos Foundationへ返還。",
            tasks=["公式クレームポータルで請求"], end_date="2026-10-25", url="https://pharos.xyz/", is_hot=True,
        ),
        item(
            id="standx-dusd", name="StandX (DUSD)", symbol="DUSD", category="DeFi/DEX",
            type="清算配当", status="upcoming", estimated_value_usd=100,
            description="StandXが終了し残余資産をDUSDで分配。適格性ページは10/26公開、請求は11/1 00:00 UTC〜12/31。",
            tasks=["10/26に適格性を確認", "11/1以降にクレーム"], end_date="2026-12-31", url="https://standx.com/", is_hot=False,
        ),
        item(
            id="grass-stage2", name="Grass (stage 2)", symbol="GRASS", category="DePIN",
            type="クレーム受付", status="active", estimated_value_usd=100,
            description="Grassステージ2の請求(USDC配布)が受付中。期限は2027-01-22。",
            tasks=["Grass公式サイトで請求"], end_date="2027-01-22", url="https://www.getgrass.io/",
        ),
        item(
            id="ekiden", name="Ekiden", category="DeFi/DEX", type="エアドロップ確認済",
            description="CryptoRank上で10/21にエアドロップ確認済みと掲載。詳細情報は限定的なので公式発表を確認。",
            end_date="未定", url="https://cryptorank.io/drophunting",
        ),
        item(
            id="alphea", name="ALPHEA", category="その他", type="エアドロップ確認済",
            description="CryptoRank上で10/20にエアドロップ確認済みと掲載。詳細情報は限定的。",
            end_date="未定", url="https://cryptorank.io/drophunting",
        ),
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
