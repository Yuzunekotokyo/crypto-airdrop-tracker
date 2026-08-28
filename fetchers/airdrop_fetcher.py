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
    """手動管理の注目エアドロップシードデータ (2026年8月時点の最新情報で更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "opensea-sea",
            "name": "OpenSea (SEA)",
            "symbol": "SEA",
            "category": "NFT",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 600,
            "description": "最大手NFTマーケットプレイス。SEAトークンの発行を正式表明し、供給量の50%をコミュニティに配分予定。当初2026年Q1予定だったが延期中、引き続き実績を積む価値あり (推定額は非公式)。",
            "tasks": ["OpenSea上でのNFT売買実績を積む", "OGユーザー特典対象か過去の取引履歴を確認", "Rewardsプログラムに参加してポイント獲得"],
            "end_date": "未定 (延期中、動向注視)",
            "logo": "",
            "url": "https://opensea.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 400,
            "description": "最大手の予測市場プラットフォーム。CMOがトークン発行とエアドロップ実施を公式に明言済み。スナップショット日・詳細条件は未発表だが、継続的な取引実績が有利と見られる。",
            "tasks": ["複数カテゴリで継続的に予測市場取引 (目安$100〜200以上)", "設定からXアカウントを連携", "Rewardsプログラムに参加"],
            "end_date": "未定 (米国事業再開後に発行予定)",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "grass-season2",
            "name": "Grass Season 2",
            "symbol": "GRASS",
            "category": "DePIN",
            "type": "クレーム受付中",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 150,
            "description": "未使用の帯域幅を提供してAI学習データ収集に貢献するDePINプロジェクト。Season 2の請求 (総額約$3M USDC相当、トークンプール1.7億枚) が既に開始済み。今すぐ確認する価値あり。",
            "tasks": ["Grassブラウザ拡張機能をインストールし稼働", "ウォレットをスナップショット前にリンク済みか確認", "対象国か確認 (制裁対象国は対象外)"],
            "end_date": "2027-01-22",
            "logo": "",
            "url": "https://www.getgrass.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-network-token",
            "name": "Base Network Token (未確定)",
            "symbol": "—",
            "category": "Layer2/インフラ",
            "type": "検討中",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Coinbase開発のL2「Base」がネットワークトークン発行の検討を表明。トークノミクス・スナップショット条件は未公開で、発行自体まだ未確定 (投機的情報のため過度な期待は禁物)。",
            "tasks": ["Base上のdAppsを継続利用", "Coinbase Wallet経由でBaseへブリッジ", "公式アナウンスを注視"],
            "end_date": "未定 (トークン発行自体が未確定)",
            "logo": "",
            "url": "https://base.org/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "yakkamon",
            "name": "Yakkamon",
            "symbol": "—",
            "category": "ゲーム",
            "type": "早期参加",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Roninチェーン上のクリーチャー収集・放置育成ゲーム。Season 0の事前登録が早期アクセス優先度を左右する。2026年Q4に早期アクセス予定。",
            "tasks": ["Season 0事前登録を実施", "公式Discordコミュニティに参加", "早期アクセス開始後にプレイ実績を積む"],
            "end_date": "未定 (Q4 2026 早期アクセス予定)",
            "logo": "",
            "url": "https://ronin.chain",
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
