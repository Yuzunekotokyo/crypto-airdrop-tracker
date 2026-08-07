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
    """手動管理の注目エアドロップシードデータ。日次更新のたびにWeb検索で内容を見直す。"""
    today = datetime.utcnow()
    added = today.strftime("%Y-%m-%d")
    return [
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 1500,
            "description": "世界最大の予測市場プラットフォーム。CMOが「トークンとエアドロップは必ず来る」と公言済みだが、スナップショット日・配布基準は未公表。取引実績に応じ一般ユーザーで$150〜$1,500、ヘビーユーザーで$1,000〜$12,500相当と試算されている。",
            "tasks": ["政治・スポーツ・暗号資産など複数カテゴリーで実際に取引する", "X(旧Twitter)アカウントをプロフィールに連携", "Polygon対応ウォレットを使用しMATICでガス代を用意", "複数ウォレットでのSybil行為は失格対象なので避ける"],
            "end_date": "未定(スナップショット日未公表)",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": added,
            "source": "curated",
        },
        {
            "id": "base-network-token",
            "name": "Base (Coinbase L2)",
            "symbol": "TBD",
            "category": "Layer2/インフラ",
            "type": "投機的(未確定)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "CoinbaseのL2チェーン。ネットワークトークン検討の示唆があり、予測市場ではトークン化確率が高いとされる。公式発表はまだ無く、偽の申請サイトに要注意。",
            "tasks": ["Base上でのオンチェーン活動履歴を積む(ブリッジ・スワップ・NFT等)", "Base上の主要dAppsを継続的に利用", "公式アナウンス以外の『申請サイト』には絶対アクセスしない"],
            "end_date": "未定(トークン未発行)",
            "logo": "",
            "url": "https://base.org/",
            "is_hot": True,
            "added_date": added,
            "source": "curated",
        },
        {
            "id": "grass-grass-stage2",
            "name": "Grass Stage 2 Claim",
            "symbol": "GRASS",
            "category": "DePIN/AI",
            "type": "クレーム受付中",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "未使用の通信帯域をAI学習データ収集に提供して報酬を得るDePINプロジェクト。Stage2クレームは2027年1月22日締切(未クレーム分は失効)。今回はUSDCで支払われる点に注意。",
            "tasks": ["公式サイトでウォレット接続し受給資格を確認", "Grass拡張機能/デスクトップアプリでのアップタイム維持(継続分は次ステージ対象)", "期限までにクレームを完了する"],
            "end_date": "2027-01-22",
            "logo": "",
            "url": "https://www.grass.io/",
            "is_hot": True,
            "added_date": added,
            "source": "curated",
        },
        {
            "id": "variational-var",
            "name": "Variational (Omni Points)",
            "symbol": "VAR",
            "category": "DeFi/デリバティブDEX",
            "type": "ポイントプログラム",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "Arbitrum上のパーペチュアルDEX。Omni Pointsは毎週金曜0時UTCに配布、2026年Q3までの実施予定。VARトークン供給の約50%がコミュニティ配分予定。実資金でのトレードを伴うためリスク管理に注意。",
            "tasks": ["Variational Omniでテストネット/メインネット取引を行う", "30日間の取引量でティアと倍率を維持", "紹介プログラムで追加ポイントを獲得"],
            "end_date": "2026-09-30(プログラム終了目安)",
            "logo": "",
            "url": "https://variational.io/",
            "is_hot": True,
            "added_date": added,
            "source": "curated",
        },
        {
            "id": "mintcasino-mntd",
            "name": "MintCasino ($MNTD)",
            "symbol": "MNTD",
            "category": "GameFi/カジノ",
            "type": "TGE直前",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Base上のカジノ/スポーツブックプラットフォーム。2026年9月にTGE予定で、$125,000相当のMNTDをプレイヤーに分配。参加条件は累計$50相当のベット(負け額ではなく賭けた累計額)。実資金の賭けを伴うためギャンブルリスクに要注意。",
            "tasks": ["MintCasinoアカウントを作成(無料)", "対象カジノ/スポーツブックで累計$50相当を賭ける(スナップショット前)", "シーズン1リーダーボードでの順位・XPで配分が決まる"],
            "end_date": "2026-09(TGE予定月)",
            "logo": "",
            "url": "https://airdrops.io/mint-2/",
            "is_hot": False,
            "added_date": added,
            "source": "curated",
        },
        {
            "id": "k25-ai",
            "name": "K25.ai",
            "symbol": "TBD",
            "category": "予測市場/AI",
            "type": "アーリーステージ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "APAC向けAIネイティブなライブ配信×予測市場プラットフォーム。Nasdaq上場企業から$100M評価額での出資を獲得済み。トークンは未確定の超アーリーステージ案件で、現状はウェイトリスト登録のみ。",
            "tasks": ["公式サイトでウェイトリストフォームに登録するのみ"],
            "end_date": "未定",
            "logo": "",
            "url": "https://www.k25.ai/",
            "is_hot": False,
            "added_date": added,
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
