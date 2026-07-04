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
    """手動管理の注目エアドロップシードデータ (毎日のWeb調査結果を反映して更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 900,
            "description": "世界最大の分散型予測市場。CMOがトークン・エアドロップ実施を公式表明済み。スナップショットは未実施で参加ウィンドウは開いたまま。",
            "tasks": ["政治・スポーツ・暗号などの複数カテゴリで継続的にベット", "USDCでの取引量を積み上げる", "Xアカウントをウォレットに連携"],
            "end_date": "未定 (スナップショット未実施)",
            "logo": "https://assets.coingecko.com/coins/images/polymarket/small/polymarket.png",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "web-research",
        },
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "ウォレット",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 650,
            "description": "ConsenSys CEOがMASKトークン発行を公式確認。2025-2026年にアクティブだったウォレットが対象。MetaMask Rewardsのポイントが配分に影響する見込み。",
            "tasks": ["MetaMask Rewardsで日常的にスワップ/ブリッジ", "Lineaなど複数チェーンで継続利用", "週次で少額の取引を継続 (量より継続性)"],
            "end_date": "2026 Q3-Q4 予定 (Season 2終了後にスナップショット)",
            "logo": "https://assets.coingecko.com/coins/images/metamask/small/metamask.png",
            "url": "https://metamask.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "web-research",
        },
        {
            "id": "hyperliquid-season2",
            "name": "Hyperliquid Season 2 (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "ポイント制エアドロップ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1100,
            "description": "高速オンチェーン永久先物DEX。Season2の日程は未発表だが、コミュニティ報酬ウォレットに供給の38.9%が温存されており、HyperEVM上のdApp利用がまだ手薄で狙い目。",
            "tasks": ["HYPEをステーキング (1トークン/日で8ポイント)", "オンチェーン取引量を積む (新規ペアは1.5倍)", "HyperEVM上のdAppへブリッジ・LP提供"],
            "end_date": "未定 (Season2日程未告知)",
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "web-research",
        },
        {
            "id": "base-network-token",
            "name": "Base ネットワークトークン",
            "symbol": "BASE",
            "category": "Layer2",
            "type": "レトロアクティブ (未確定)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "Coinbase開発のL2。トークン検討を公式に認めたが詳細・時期は未発表。Polymarket予測市場では2026年内launchに69%の確率。",
            "tasks": ["Base上のdApps (DEX/レンディング) を継続利用", "Base上でのブリッジ・トランザクション実績を積む"],
            "end_date": "2026 Q2-Q4 (未確定、公式発表待ち)",
            "logo": "https://assets.coingecko.com/coins/images/base/small/base.png",
            "url": "https://base.org/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "web-research",
        },
        {
            "id": "pear-protocol",
            "name": "Pear",
            "symbol": "PEAR",
            "category": "予測市場",
            "type": "新着ファーミング",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 150,
            "description": "今週新たに確認された予測市場系エアドロップファーム。参加ハードルが低く早期ポジションが取りやすい新規案件。",
            "tasks": ["リワード待機リストに登録", "Xアカウントを連携", "ソーシャルクエストを完了", "デイリーポイントのため毎日チェックイン"],
            "end_date": "未定 (新規プロジェクトのため要注視)",
            "logo": "",
            "url": "https://pear.garden/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "web-research",
        },
        {
            "id": "deploy-finance",
            "name": "Deploy Finance",
            "symbol": "",
            "category": "DeFi/イールド",
            "type": "新着ファーミング",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 100,
            "description": "今週確認された新しいDeFiイールド系エアドロップ案件。登録・ウォレット連携のみで早期ポジションを確保できる。",
            "tasks": ["アカウント登録", "ウォレット接続", "Xアカウントをフォロー・連携", "今後の詳細発表を待つ"],
            "end_date": "未定 (新規プロジェクトのため要注視)",
            "logo": "",
            "url": "https://deploy.finance/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "web-research",
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
