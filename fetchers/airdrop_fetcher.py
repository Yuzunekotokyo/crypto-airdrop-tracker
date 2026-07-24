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
    """手動管理の注目エアドロップシードデータ (2026年7月時点の実在プロジェクトで更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "grass-network",
            "name": "Grass Network (GRASS)",
            "symbol": "GRASS",
            "category": "DePIN",
            "type": "ポイント制/リワード",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": (
                "遊休インターネット帯域幅を共有してAI学習用データ収集に貢献するDePINプロジェクト。"
                "Season 2の報酬 (総額300万ドル相当のUSDC) のクレーム受付が2026年7月22日に開始し、"
                "2027年1月22日まで6か月間継続。さらに供給の17%にあたる約1.7億GRASSトークンの"
                "エアドロップも2026年後半に予定 (詳細未発表)。"
            ),
            "tasks": ["Grass拡張機能/アプリをインストールしてノードを稼働", "Uptime PointsとNetwork Pointsを蓄積", "USDC報酬をSeason 2ポータルでクレーム"],
            "end_date": "2027-01-22",
            "logo": "",
            "url": "https://airdrops.io/grass/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-07-24",
        },
        {
            "id": "orbinum-network",
            "name": "Orbinum Network (ORB)",
            "symbol": "ORB",
            "category": "プライバシー/インフラ",
            "type": "テストネット参加",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": (
                "プライベート送金を扱うL1ネットワーク。2026年3月13日開始のSeason 1「Genesis Community」で、"
                "クエスト・週次ログインストリーク・リファラル・テストネット操作 (シールド送金/アンシールド等) に応じて"
                "ORBクレジットを付与。コミュニティプールは1,500万ORB、アンバサダープールは500万ORBで、"
                "合計2,000万ORBがSeason 1参加者に配分予定。スナップショットはメインネット開始14日前 (日程未定)。"
            ),
            "tasks": ["Orbinumポータルでウォレット接続", "テストネットでシールド/プライベート送金を実行", "週次ログインストリークを維持", "リファラルで友人を招待"],
            "end_date": "スナップショット日未定 (メインネット開始14日前)",
            "logo": "",
            "url": "https://airdrops.io/orbinum/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-07-24",
        },
        {
            "id": "katana-network",
            "name": "Katana Network (KAT)",
            "symbol": "KAT",
            "category": "DeFi/Layer2",
            "type": "ステーキング報酬 (TGE済み)",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": (
                "DeFi向け流動性レイヤー2。2026年3月18日にKATトークンのTGEが完了済み。"
                "供給100億KATのうち20%を流動性マイニング、15% (35億KAT) をコミュニティエアドロップとして"
                "段階的に配分中。先着3.5億KATのプレステークは60日間で35%リターン+vKATボーナスを提供。"
            ),
            "tasks": ["Katana公式サイトでウォレット接続", "最低100 KATをプレステーク", "Questsセクションでオンチェーンクエストを達成"],
            "end_date": "プレステーク枠終了まで (先着順、日程未定)",
            "logo": "",
            "url": "https://airdrops.io/katana-network/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-07-24",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ (未確定)",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": (
                "分散型予測市場プラットフォーム。POLYトークンの正式なローンチ日・配布ルールは"
                "2026年7月24日時点で未発表。コミュニティ予想では2026年後半とされるが未確定。"
                "継続的な少額取引・X連携・Rewardsプログラム参加が有利とされる一方、"
                "複数ウォレットでの水増し取引はウォッシュトレードとして除外される可能性が高い。"
            ),
            "tasks": ["複数カテゴリの市場で継続的に取引", "設定画面でXアカウントを連携", "Rewardsプログラムに参加してUSDCを獲得しつつ実績を積む"],
            "end_date": "未定 (公式発表待ち)",
            "logo": "",
            "url": "https://airdrops.io/polymarket/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-07-24",
        },
        {
            "id": "monetrix",
            "name": "Monetrix",
            "symbol": "",
            "category": "DeFi/イールドファーミング",
            "type": "ポイント制 (トークン未確定)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": (
                "2026年7月にMerkl上で初のYieldMaxxingキャンペーンを開始したばかりの新規DeFiプロジェクト。"
                "ポイント付与は行われているが、トークン配布や配布時期は2026年7月24日時点で未確定。"
                "情報の少ない新興案件のため、公式チャンネルでの継続的な情報確認を推奨。"
            ),
            "tasks": ["Merkl経由でMonetrixのYieldMaxxingキャンペーンに参加", "指定プールに流動性を提供", "公式X (Twitter) で最新情報を確認"],
            "end_date": "未定",
            "logo": "",
            "url": "https://airdrops.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-07-24",
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
