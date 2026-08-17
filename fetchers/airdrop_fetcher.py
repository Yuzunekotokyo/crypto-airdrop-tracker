"""
Airdrop情報をWeb/APIから収集するモジュール。
現在はairdrops.ioのパブリックページとCoinGeckoトレンドを組み合わせて使用。
"""

import requests
import logging
from datetime import datetime
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
    """手動管理の注目エアドロップシードデータ。毎日のWeb調査結果を基に更新。
    最終調査日: 2026-08-17"""
    today = datetime.utcnow()
    return [
        {
            "id": "opensea-sea",
            "name": "OpenSea (SEA)",
            "symbol": "SEA",
            "category": "NFT/マーケットプレイス",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 500,
            "description": "NFT取引最大手OpenSeaの新トークン。2021〜2022年にNFT取引した「OG」ウォレットは初回配布対象になる見込み。総供給の50%をコミュニティに配分予定だが、当初Q1 2026予定だった発行は複数回延期中で2026年8月時点も未発行。",
            "tasks": ["OpenSea Rewardsページでウォレットを接続しXP獲得を開始", "Voyages(クエスト)をクリアしてTreasure Chestをアップグレード", "EVM/Solana/Abstractなど複数チェーンでOpenSeaを利用"],
            "end_date": "未定（発表延期中、2026年内配布との観測）",
            "logo": "",
            "url": "https://opensea.io/rewards",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-live-research",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "DeFi/予測市場",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "世界最大級の分散型予測市場。CMOがトークン発行とエアドロップの実施を公式に確認済み（時期未定、2026年後半が有力視）。$100〜200程度の継続的な取引実績があれば対象になりやすいとの見方が強い。",
            "tasks": ["政治・スポーツ・経済など複数カテゴリで継続的に取引", "設定画面でXアカウントを連携", "Rewardsプログラムに参加しUSDCを日次獲得", "複数ウォレットの使い分けを避け1つに活動を集中"],
            "end_date": "未定（2026年後半見込み）",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-live-research",
        },
        {
            "id": "base-token",
            "name": "Base (Coinbase L2)",
            "symbol": "—",
            "category": "Layer2",
            "type": "検討段階（未確定）",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Coinbase開発L2「Base」のネイティブトークン構想。2025年9月に開発者Jesse Pollak氏が検討開始を公表しArmstrong CEOも追認したが、正式な発行決定・トークノミクスは未発表。上場企業ゆえ規制対応に時間を要し、発行時期はQ2〜Q4 2026の可能性。",
            "tasks": ["Base上のdAppsを日常的に利用", "資産をBaseへブリッジしオンチェーン活動を積み上げる", "公式発表を継続的にウォッチ（未確定情報のため過度な期待は禁物）"],
            "end_date": "未定（トークン発行自体が未確定）",
            "logo": "",
            "url": "https://base.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-live-research",
        },
        {
            "id": "plume-plume-s2",
            "name": "Plume Network (PLUME) Season 2",
            "symbol": "PLUME",
            "category": "RWA/Layer2",
            "type": "ポイント配布（クレーム中）",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 30,
            "description": "RWA(現実資産)特化L2。Plume Points Season 2の登録は2026年4/29〜5/27で終了済み、3/31時点で1万PP以上保有が条件だった。現在クレームポータルで受取可能。配布プールは1.5億トークンだが単価が低く1人あたり$3〜50程度と少額（米国・OFAC制裁国は対象外）。",
            "tasks": ["登録済みウォレットで公式クレームポータルに接続", "対象国か確認（米国は対象外）", "ガス代が報酬額を上回らないか事前確認"],
            "end_date": "2026-08-31（クレーム受付中・要公式確認）",
            "logo": "",
            "url": "https://plume.org/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-live-research",
        },
        {
            "id": "grass-grass-s2",
            "name": "Grass Network (GRASS) Season 2",
            "symbol": "GRASS",
            "category": "DePIN",
            "type": "USDC配布（トークンではない）",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 20,
            "description": "未使用の帯域幅をAI学習データ収集に提供するDePIN。Season 2は2024年10月〜2026年6月のNetwork/Uptimeポイント保有者にUSDCで還元。クレームは2026年7月22日開始、2027年1月22日まで受付。少額($数ドル程度)との声が多い点に注意。",
            "tasks": ["Grass拡張機能/アプリで帯域幅提供を継続しポイントを維持", "公式クレームサイトでウォレット接続しUSDCを受け取る", "対象国かどうかを事前確認"],
            "end_date": "2027-01-22（クレーム受付中）",
            "logo": "",
            "url": "https://www.grass.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-live-research",
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
