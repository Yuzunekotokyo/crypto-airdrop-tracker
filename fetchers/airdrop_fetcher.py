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
    """手動管理の注目エアドロップシードデータ。日次更新のたびにWeb検索した最新情報で洗い替え。
    2026-07-17時点の情報で更新: LayerZero/Scroll/zkSync/Hyperliquid/EigenLayer/Movementは
    いずれも2024年中に配布済みのため終了案件としてリストから外し、現在進行中/確定前の案件に差し替え。
    """
    today = datetime.utcnow()
    return [
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "取引所トークン",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": (
                "世界最大の予測市場プラットフォーム。CMOのMatthew Modabber氏が「トークンとエアドロップは実施する」"
                "と公式に明言。ICEから約20億ドルの出資を受け評価額は約150億ドル。米国展開が完了した後、"
                "2026年後半のトークン発表が有力視されているが、配布ルール・時期は未確定。"
            ),
            "tasks": ["Polymarketで取引実績を積む", "対応地域でアカウント開設・KYC", "公式X/Discordで発表を注視"],
            "end_date": "未定(2026年後半予想)",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-07-17",
        },
        {
            "id": "base-network-token",
            "name": "Base Network Token",
            "symbol": "TBD",
            "category": "Layer2",
            "type": "ネットワークトークン",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": (
                "CoinbaseのL2チェーン「Base」が2025年9月にネットワークトークン発行の検討を正式表明(従来の"
                "「トークンは発行しない」方針から転換)。2026年Q2〜Q4のローンチが観測筋の予想で、Polymarket上の"
                "予測市場では年内ローンチ確率が約69%。トークノミクス・配布詳細は未発表。"
            ),
            "tasks": ["Base上でDEX/DeFiの利用実績を積む", "Base公式Blog/Xで発表を注視", "対応dAppsでのアクティビティを継続"],
            "end_date": "未定(2026年Q2-Q4予想)",
            "logo": "",
            "url": "https://base.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-07-17",
        },
        {
            "id": "prismax-pix",
            "name": "PrismaX (PIX)",
            "symbol": "PIX",
            "category": "AI/ロボティクス",
            "type": "ポイント→TGE",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": (
                "ロボットの遠隔操作でAI学習データを収集する分散型ロボティクスプラットフォーム。a16z crypto CSX "
                "等から1,100万ドルを調達済み。貯めたPrisma PointsはTGE後に$PIXへ変換予定 (時期未確定)。"
            ),
            "tasks": ["Solanaウォレットを接続 (初回1,000ポイント)", "毎日ログインで+10ポイント", "遠隔操作タスク・クイズに参加"],
            "end_date": "TGE時期未定",
            "logo": "",
            "url": "https://airdrops.io/prismax/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-07-17",
        },
        {
            "id": "endmatch",
            "name": "EndMatch",
            "symbol": "",
            "category": "その他",
            "type": "Galxeキャンペーン",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": (
                "2026年7月中旬に登場したばかりの新しいエアドロップ案件。配布量が総供給量の15%と通常より大きい"
                "割当が特徴で注目度が高い。USD換算額・詳細タスクは現時点で未確定のため、参加前に必ず公式ページ"
                "で最新情報を確認すること。"
            ),
            "tasks": ["Galxe公式キャンペーンページでタスクを確認", "X/Telegramをフォロー", "公式サイトの追加タスクを完了"],
            "end_date": "未定",
            "logo": "",
            "url": "https://www.galxe.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-07-17",
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
