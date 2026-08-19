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
    """手動管理の注目エアドロップシードデータ。日次スケジュールタスクが
    Web検索で得た最新情報をもとに更新する (2026年8月時点の情報を反映)。"""
    today = datetime.utcnow()
    return [
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "取引所トークン (未確定)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "米大手予測市場プラットフォーム。CMOがトークン発行とエアドロップの実施を公式に示唆。発行日・詳細な配布条件は未発表だが、継続的な取引実績・X連携が有利になるとの見方が有力。",
            "tasks": ["複数カテゴリで継続的に少額〜中額の取引を行う", "設定画面でXアカウントを連携", "Rewardsプログラムに参加", "同一ユーザーによる複数ウォレット作成は避ける"],
            "end_date": "未定 (2026年後半見込み)",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "web-research-2026-08",
        },
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "ウォレット/インフラ",
            "type": "リワードプログラム (未確定)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "最大手Web3ウォレット。ConsenSys CEOがMASKトークンの存在に言及したが、公式ヘルプページでは配布計画なしとの記載もあり情報が錯綜。MetaMask Rewardsプログラム(2025年10月開始)のポイントが将来の配布基準になる可能性。偽エアドロップの詐欺注意喚起が公式から出ている点に留意。",
            "tasks": ["MetaMask Rewardsプログラムに登録", "オンチェーン活動(スワップ・ブリッジ等)を継続", "公式ドメイン(metamask.io)以外のリンクは踏まない"],
            "end_date": "未定 (2026年Q3〜Q4見込み)",
            "logo": "",
            "url": "https://metamask.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "web-research-2026-08",
        },
        {
            "id": "grass-season2",
            "name": "Grass Season 2",
            "symbol": "GRASS",
            "category": "DePIN/AI",
            "type": "レトロアクティブ (claim受付中)",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 50,
            "description": "未使用の帯域幅を提供しAIデータ収集に貢献するDePINプロジェクト。Season2は2026年7月22日にclaim開始、2027年1月22日まで受付。今回はGRASSではなくUSDC建てで配布される点に変更あり。Uptime PointsとNetwork Pointsの2軸で報酬が決定。",
            "tasks": ["Grassノード/拡張機能を稼働させる", "公式ダッシュボードでclaim申請", "Network Points(実利用帯域)を稼ぐ"],
            "end_date": "2027-01-22",
            "logo": "",
            "url": "https://www.grass.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "web-research-2026-08",
        },
        {
            "id": "variational",
            "name": "Variational",
            "symbol": "-",
            "category": "DeFi/デリバティブ",
            "type": "コミュニティ配分 (アーリーステージ)",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "CryptoRankが2026年8月時点で有望案件として挙げるデリバティブ系プロトコル。コミュニティへの配分方針が明文化されている点が評価されているが、詳細な配布条件・時期は今後の発表待ち。情報が少ないため参加は自己責任で。",
            "tasks": ["公式サイト・SNSで最新情報を確認", "プロトコルの対象タスクに参加"],
            "end_date": "未定",
            "logo": "",
            "url": "",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "web-research-2026-08",
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
