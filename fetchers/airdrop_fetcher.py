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
    """手動管理の注目エアドロップシードデータ。2026年8月時点の最新情報に基づき更新。"""
    today = datetime.utcnow()
    return [
        {
            "id": "flop-flop",
            "name": "Flop Labs (FLOP)",
            "symbol": "FLOP",
            "category": "AI/インフラ",
            "type": "フェアローンチ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Arthur Hayes氏(BitMEX共同創業者)が現役復帰して率いるAIエージェント経済向け通貨プロジェクト。VC配分・プレセール無しの100%フェアローンチを標榜し、本人が「massive」と表現するエアドロップをQ4 2026に予告(ブロックチェーン本体はQ1 2027稼働予定)。",
            "tasks": ["X (Twitter) で @flop_labs をフォロー", "公式発表を継続ウォッチ(要件は今後追加される可能性)"],
            "end_date": "2026年Q4 (未定)",
            "logo": "",
            "url": "https://x.com/flop_labs",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-08",
        },
        {
            "id": "push-chain-pc",
            "name": "Push Chain (PC)",
            "symbol": "PC",
            "category": "インフラ",
            "type": "テストネット",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "Push Protocol(旧EPNS)チームによるクロスチェーンL1。EVM/非EVM問わず一度のデプロイで全チェーンのユーザーにリーチ可能。$PCは現在テストネット段階。",
            "tasks": ["Push Portalにログインし X/Discordを連携", "Zappi.to・Cetra.appなど連携アプリでクエスト達成", "6時間おきにフォーセットからガス受給"],
            "end_date": "テストネット期間中 (TGE未定)",
            "logo": "",
            "url": "https://push.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-08",
        },
        {
            "id": "mint-mntd",
            "name": "Mint Casino (MNTD)",
            "symbol": "MNTD",
            "category": "GameFi/カジノ",
            "type": "ポイント/リーダーボード",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "オンラインカジノ/スポーツブックのMintが、Base上で2026年9月にTGE予定。Season1として$125,000相当の$MNTDをプレイヤー間で山分け。スナップショット直前が最後のチャンス。",
            "tasks": ["MINTアカウント作成 (無料)", "カジノ/スポーツブックで累計$50以上ベット", "XPリーダーボード順位を上げる(紹介ボーナスあり)"],
            "end_date": "2026年9月 (TGE直前スナップショット)",
            "logo": "",
            "url": "https://www.mintchain.io/airdrop",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-08",
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
            "description": "CMOのMatthew Modabber氏が「トークンとエアドロップは実施する」と明言済み。米国向けアプリ展開完了後の実施が濃厚だが、具体的な日程・スナップショット・適格条件は未発表(2026年後半が有力視)。",
            "tasks": ["Polymarketで通常通り予測市場に参加", "米国向けアプリのローンチ状況をウォッチ", "公式アナウンスを待つ"],
            "end_date": "未定 (2026年後半有力)",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-08",
        },
        {
            "id": "dgrid-dgai",
            "name": "DGrid AI (DGAI)",
            "symbol": "DGAI",
            "category": "AI/インフラ",
            "type": "レトロアクティブ(受付終了)",
            "status": "ended",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "分散型AIネットワーク。総供給10億枚のうち8%(8,000万DGAI)をエアドロップに割当。クレーム受付は2026年8月17日〜22日8:00 UTCで既に終了。参考情報として掲載。",
            "tasks": ["(受付終了) Premium会員/AI Arenaポイント保有者/Galxeキャンペーン参加者/初期コントリビューターが対象だった"],
            "end_date": "2026-08-22 (終了)",
            "logo": "",
            "url": "https://dgrid.ai/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-08",
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
