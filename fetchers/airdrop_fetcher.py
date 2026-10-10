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
            "id": "pharos-pros",
            "name": "Pharos (PROS)",
            "symbol": "PROS",
            "category": "Layer1",
            "type": "クレーム",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "【期限間近】クレーム受付中(4/28開始)。2026-10-25で終了、未請求分は財団に返還され猶予なし。",
            "tasks": ['対', '象', 'ウ', 'ォ', 'レ', 'ッ', 'ト', 'で', '公', '式', 'サ', 'イ', 'ト', 'か', 'ら', 'ク', 'レ', 'ー', 'ム'],
            "end_date": (today + timedelta(days=15)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://pharos.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "sonic-s",
            "name": "Sonic (S)",
            "symbol": "S",
            "category": "Layer1",
            "type": "クレーム",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "【期限間近】未請求の約3,269万S(シーズン1・2合計)が2026-10-15にバーン予定。",
            "tasks": ['公', '式', 'ク', 'レ', 'ー', 'ム', 'ペ', 'ー', 'ジ', 'で', '未', '請', '求', '分', 'を', '請', '求'],
            "end_date": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://www.soniclabs.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "grass-stage2",
            "name": "Grass (Stage 2)",
            "symbol": "GRASS",
            "category": "DePIN",
            "type": "クレーム",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Stage 2のUSDC配布。クレーム期限は2027-01-22。",
            "tasks": ['G', 'r', 'a', 's', 's', 'ア', 'カ', 'ウ', 'ン', 'ト', 'で', 'ク', 'レ', 'ー', 'ム'],
            "end_date": (today + timedelta(days=104)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://www.getgrass.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "concrete-ct",
            "name": "Concrete (CT)",
            "symbol": "CT",
            "category": "DeFi",
            "type": "ポイント",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "2026年9月にCTトークンとTGEを公式が確認。ポイント(Bags)はソーシャル・ガバナンス・テストで獲得。",
            "tasks": ['ポ', 'イ', 'ン', 'ト', '獲', '得', 'タ', 'ス', 'ク', 'に', '参', '加'],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://www.concrete.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "push-chain",
            "name": "Push Chain (PC)",
            "symbol": "PC",
            "category": "Layer1",
            "type": "テストネット",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "トークノミクスでエアドロップ配分が公表済み。テストネット参加が対象(2026年8月時点でトークン未発行)。",
            "tasks": ['テ', 'ス', 'ト', 'ネ', 'ッ', 'ト', '参', '加'],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://push.org/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket",
            "name": "Polymarket",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "取引量",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "未確定/要確認: 取引量に連動する報酬が報じられているが情報源は古くタイミング不明。",
            "tasks": ['予', '測', '市', '場', 'で', 'の', '取', '引'],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "dac-quantum",
            "name": "DAC Quantum Chain (DACT)",
            "symbol": "DACT",
            "category": "Layer1",
            "type": "コミュニティ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "未確定: ホワイトペーパーで総供給10億の5%をコミュニティ配布枠に確保。エアドロップ自体は未確認。",
            "tasks": ['公', '式', '発', '表', 'を', '監', '視'],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://usethebitcoin.com/airdrop/dac-quantum-chain-airdrop-guide/",
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
