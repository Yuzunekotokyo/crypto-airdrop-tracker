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
    """手動管理の注目エアドロップシードデータ。毎日のリサーチ結果で更新する。"""
    today = datetime.utcnow()
    return [
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "ウォレット/インフラ",
            "type": "レトロアクティブ(予定)",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 1500,
            "description": "ConsenSys CEOが存在を公式表明した最大級の期待を集める未発行トークン。正式な配布方法・時期は未発表だが、'Rewards'ポイント制度が事実上の適格基準とみられる。",
            "tasks": ["MetaMask Mobileをダウンロード", "定期的にスワップを実行", "Lineaへブリッジ", "MetaMask Cardを利用", "Rewardsプログラムでポイント獲得"],
            "end_date": "未定 (2026年Q3-Q4予想)",
            "logo": "",
            "url": "https://metamask.io/",
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
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "米国最大級の分散型予測市場プラットフォーム。トークン未発行だが公式が将来のトークン化を示唆しており、MASKと並び2026年最有力候補の一つ。",
            "tasks": ["予測市場でのベット参加", "取引量・頻度を積み上げる", "公式Discord/Xでの活動"],
            "end_date": "未定",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-hype-s2",
            "name": "Hyperliquid Season 2 (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "継続エミッション",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1200,
            "description": "史上最大級だったHYPE Genesisに続き、コミュニティ向けに供給の38.888%を将来配分すると公式表明。継続的な取引・流動性提供が対象。",
            "tasks": ["Hyperliquid上での先物取引", "流動性提供 (HLP)", "紹介プログラム参加"],
            "end_date": "継続中",
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "ritual-airdrop",
            "name": "Ritual",
            "symbol": "RITUAL",
            "category": "AI/インフラ",
            "type": "レトロアクティブ(確定)",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 400,
            "description": "AI推論をオンチェーンで実行する分散型インフラ。エアドロップ実施が確定しており、直近ではミント/配布イベントの日程も報じられている。",
            "tasks": ["公式テストネット/ノード活動への参加", "コミュニティタスクの実行", "対象NFT/ミントイベントへの参加"],
            "end_date": "確定 (詳細日程は公式発表待ち)",
            "logo": "",
            "url": "https://ritual.net/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hertzflow",
            "name": "HertzFlow",
            "symbol": "HZF",
            "category": "DeFi",
            "type": "ポイント制エアドロップ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "TGEとエアドロップ実施を公式が確認済み。Season 1は「Merits」ポイント制で、TGE時の配分量を決定する。",
            "tasks": ["プラットフォーム利用でMeritsポイントを獲得", "コミュニティタスクへの参加", "SNSでの拡散タスク"],
            "end_date": "Season 1 進行中",
            "logo": "",
            "url": "https://airdrops.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "sweep-swp",
            "name": "Sweep (SWEEP)",
            "symbol": "SWEEP",
            "category": "DeFi",
            "type": "レトロアクティブ(配布中)",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 200,
            "description": "総供給量の約27%(約2.7億SWEEP)を参加者に配布する2026年8月確定案件。クレーム受付が進行中。",
            "tasks": ["公式サイトでウォレット接続しクレーム状況を確認", "対象期間中の利用実績を確認"],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://airdrops.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-token",
            "name": "Base",
            "symbol": "—",
            "category": "Layer2",
            "type": "レトロアクティブ(未確定)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Coinbase運営のEthereum L2。独自トークンは未確定だが、公式発言やトークノミクス面から将来の配布可能性が期待されている。",
            "tasks": ["Base上でのブリッジ・スワップ", "Base上のdApps利用実績を積む"],
            "end_date": "未確定",
            "logo": "https://assets.coingecko.com/coins/images/38108/small/wsQ.png",
            "url": "https://base.org/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "monad-mon",
            "name": "Monad (MON)",
            "symbol": "MON",
            "category": "Layer1",
            "type": "レトロアクティブ(終了)",
            "status": "ended",
            "difficulty": "easy",
            "estimated_value_usd": 200,
            "description": "2025年10月にクレームが開始し11月に終了済み。28.9万ウォレットに配布され、トークンはメインネット解禁までエスクロー中。新規参加は不可。",
            "tasks": [],
            "end_date": "2025-11-03 (受付終了)",
            "logo": "",
            "url": "https://www.monad.xyz/",
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
