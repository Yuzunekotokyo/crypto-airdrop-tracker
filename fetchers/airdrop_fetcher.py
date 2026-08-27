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
    """手動管理の注目エアドロップシードデータ (毎日の調査結果で更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "aligned-align",
            "name": "Aligned (ALIGN)",
            "symbol": "ALIGN",
            "category": "インフラ/ZK",
            "type": "ジェネシスドロップ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "ゼロ知識証明検証レイヤー。供給量の8.74%をジェネシスドロップとして開発者・Discordメンバー・Galxeクエスト参加者・STRK/MINA/ZK/POL/SCR/TAIKO/EIGEN保有者など約89万アドレスに配布。ALIGNは既にクレーム受付中。",
            "tasks": [
                "airdrop.alignedlayer.com で対象ウォレットを確認",
                "1万ALIGN以下はBase(L2)でTGE時に全額アンロックされガス代を抑えてクレーム可能",
                "対象外の場合は今後の追加ウェーブに注目",
            ],
            "end_date": "クレーム受付中(期限未定)",
            "logo": "",
            "url": "https://airdrop.alignedlayer.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "grass-grass",
            "name": "Grass",
            "symbol": "GRASS",
            "category": "DePIN",
            "type": "USDCクレーム (Season 2)",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "分散型データ収集ネットワーク。2024年10月〜2026年6月(Epoch1-19)に獲得したNetwork Pointsに応じ、総額約300万USDCをapp.grass.ioでクレーム可能。新規タスクは不要。",
            "tasks": [
                "app.grass.io でウォレットを接続しクレーム状況を確認",
                "VPN経由でのアクセスは対象除外・没収リスクがあるため注意",
                "制限地域(OFAC等)に該当しないか確認",
            ],
            "end_date": "2027-01-22",
            "logo": "",
            "url": "https://app.grass.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "propr-propr",
            "name": "Propr (PROPR)",
            "symbol": "PROPR",
            "category": "RWA/不動産",
            "type": "ジェネシスエアドロップ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "Hyperliquid上でローンチした不動産関連プロジェクト。2026年8月24日にTGEし、供給量10億PROPRのうち20%を蓄積ポイントに応じてジェネシス配布(全て即時アンロック)。",
            "tasks": [
                "propr.xyz で獲得済みProprポイントとウォレット対象状況を確認",
                "TGE後のクレーム受付状況を公式アナウンスで確認",
            ],
            "end_date": "TGE済み(クレーム期限は公式発表待ち)",
            "logo": "",
            "url": "https://www.propr.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "grvt-grvt",
            "name": "GRVT",
            "symbol": "GRVT",
            "category": "DeFi/デリバティブ取引所",
            "type": "トークンアンロック (要クレーム)",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "オンチェーン・デリバティブ取引所。2026年7月30日にTGEし、合計2.8億GRVTをSeason1/2トレーダーに12ヶ月かけて分割配布。各トランシェは解放から30日以内にクレームしないと失効するため、7/30解放分は8/29が期限。",
            "tasks": [
                "GRVT公式サイトでSeason1/2で取引したアカウントにログイン",
                "報酬ポータルで未クレームのトランシェを確認しクレーム",
                "毎月の新規解放分も30日以内にクレーム",
            ],
            "end_date": "2026-08-29",
            "logo": "",
            "url": "https://airdrops.io/grvt/",
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
