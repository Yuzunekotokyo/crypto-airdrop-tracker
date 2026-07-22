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
    """手動管理の注目エアドロップシードデータ (2026年7月22日 最新情報に更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "grass-season2",
            "name": "Grass (GRASS) Season 2",
            "symbol": "GRASS",
            "category": "DePIN",
            "type": "リワード請求 (Claim受付中)",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 150,
            "description": "帯域共有型DePINプロジェクト。Season 2のUSDC請求ウィンドウが本日2026年7月22日13:00(EST)に開始。2024年10月〜2026年6月のネットワークポイントに応じて報酬額が変動 (総額約$300万相当)。2027年1月22日までに請求しないと権利消滅。",
            "tasks": ["Grassダッシュボードにアクセスしウォレット接続", "パスキー/メールOTPで新規非カストディアルウォレットを設定", "2027年1月22日までに請求を完了"],
            "end_date": "2027-01-22",
            "logo": "",
            "url": "https://www.grass.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "opensea-sea",
            "name": "OpenSea (SEA)",
            "symbol": "SEA",
            "category": "NFT/マーケットプレイス",
            "type": "コミュニティ配布 (未実施)",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "NFTマーケットプレイス最大手。CEOが供給の50%をコミュニティ (OG・報酬参加者) に配布すると表明。当初Q1 2026予定だったが2026年7月時点で正式なスナップショット日・配点基準は未発表。",
            "tasks": ["OpenSeaでのNFT売買を継続", "Voyages(デイリークエスト)をこなす", "Treasure Chestのレベルを上げる", "複数ウォレットをリンク"],
            "end_date": "未定",
            "logo": "",
            "url": "https://opensea.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket-token",
            "name": "Polymarket",
            "symbol": "未定",
            "category": "予測市場",
            "type": "コミュニティ配布 (予定)",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "世界最大の予測市場プラットフォーム。CMOが『トークンとエアドロップは実施される』と公式に言及済み。配布基準・時期は未発表 (2026年後半が有力視)。",
            "tasks": ["実際にPolymarketで予測市場に参加・取引する", "幅広いカテゴリのイベント市場を利用", "公式Xアカウントで続報を確認"],
            "end_date": "未定",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "spicenet-points",
            "name": "Spicenet",
            "symbol": "未定",
            "category": "インフラ/クロスチェーン",
            "type": "ポイントファーミング",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "クロスチェーン向け新興プロトコル。PortalでクエストやチェックインをこなしSpice Pointsを貯める。トークン化・エアドロップは公式未確定。フィッシングサイトが多数報告されているため参加前に公式リンクを要検証。",
            "tasks": ["公式に確認済みのリンクからのみPortalへアクセス", "デイリーチェックイン", "紹介プログラムでボーナスポイント獲得"],
            "end_date": "未定",
            "logo": "",
            "url": "https://airdrops.io/spicenet/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-speculative",
            "name": "Base (Coinbase L2)",
            "symbol": "未定",
            "category": "Layer2",
            "type": "トークン未確定 (投機的)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Coinbase運営のEthereum L2。独自トークン発行の検討は表明されているが、2026年7月時点で公式な発表・スケジュールは無し。『Base公式クレームサイト』を名乗るものは全て詐欺なので絶対にアクセスしないこと。",
            "tasks": ["Base上のdAppsを日常的に利用しオンチェーン活動履歴を積む", "公式発表 (base.org) のみを情報源にする"],
            "end_date": "未定",
            "logo": "",
            "url": "https://www.base.org/",
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
