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
    """手動管理の注目エアドロップシードデータ (定期的に更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "ウォレット",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": None,
            "description": "Consensys公式ウォレット。MASKトークンの配布(供給の15%)が開始済み。2026年3月1日以前のスワップ/ブリッジ/DeFi利用実績があるウォレットが対象。claim期間は開始から90日間。",
            "tasks": ["mskfndt.info でウォレットの対象確認", "対象ならその場でclaim", "Rewardsプログラム(Season2)でのポイント継続獲得"],
            "end_date": (today + timedelta(days=75)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/28861/small/metamask.png",
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
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": None,
            "description": "NYSE運営元ICEから20億ドルの出資を受けた最大手予測市場。POLYトークンとエアドロップは確定済みだが、スナップショット日・詳細条件は未発表。複数カテゴリでの継続的な取引が有利とされる。",
            "tasks": ["政治・スポーツ・経済など複数カテゴリで取引", "数週間〜数ヶ月にわたり継続的に利用", "X(Twitter)アカウントをリンク"],
            "end_date": "未定(スナップショット未発表)",
            "logo": "https://assets.coingecko.com/coins/images/47421/small/polymarket.png",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-coinbase-l2",
            "name": "Base",
            "symbol": "—",
            "category": "Layer2",
            "type": "潜在的エアドロップ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": None,
            "description": "Coinbase運営のL2。トークン未発行だが日次取引高が最大級で、現在最も多くファーマーが活動しているチェーンの一つ。スワップ・ブリッジ・NFTミント・レンディング利用が対象になり得る。",
            "tasks": ["Base上でスワップ/ブリッジを実行", "Base上のdAppでレンディング・NFTミント", "継続的なオンチェーン活動を維持"],
            "end_date": "未定(トークン未発行)",
            "logo": "https://assets.coingecko.com/asset_platforms/images/131/small/base-network.png",
            "url": "https://base.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "backpack-bp-season4",
            "name": "Backpack (BP) Season 4",
            "symbol": "BP",
            "category": "取引所",
            "type": "ポイントプログラム",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": None,
            "description": "2026年3月にTGE済み(供給の25%をコミュニティに配布)。現在進行中のSeason 4ポイントプログラムが将来の追加配布・エピローグ再配分の対象になる見込み。",
            "tasks": ["Backpack取引所でSeason 4ポイントを獲得", "現物/デリバティブ取引を継続", "Mad Ladsホルダーは追加優遇あり"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39824/small/backpack.png",
            "url": "https://backpack.exchange/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "opensea-sea",
            "name": "OpenSea (SEA)",
            "symbol": "SEA",
            "category": "NFT/マーケットプレイス",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": None,
            "description": "最大手NFTマーケットプレイス。当初2026年3月30日ローンチ予定だったが市場環境を理由に延期中で新日程は未発表。Treasure ChestのVoyage達成や売買実績が対象。",
            "tasks": ["Treasure ChestのVoyageを達成", "OpenSea上でNFT/トークンの売買を継続", "公式発表を継続的にチェック"],
            "end_date": "未定(ローンチ延期中)",
            "logo": "https://assets.coingecko.com/markets/images/302/small/opensea.png",
            "url": "https://opensea.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "grass-season2",
            "name": "Grass Network Season 2",
            "symbol": "GRASS",
            "category": "DePIN",
            "type": "ポイントプログラム",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": None,
            "description": "未使用の帯域幅を提供してAI学習データ収集に貢献するDePINプロジェクト。2026年7月7日のコミュニティコールでSeason 2ロードマップを発表、7月中旬にウォレット機能(パスキー/メールOTP対応)がリリース予定。",
            "tasks": ["Grassアプリ/拡張機能をインストールし帯域幅を共有", "新ウォレット機能でアカウントを準備", "公式コミュニティコールをフォロー"],
            "end_date": "未定(Season2詳細待ち)",
            "logo": "https://assets.coingecko.com/coins/images/38556/small/grass.png",
            "url": "https://www.getgrass.io/",
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
    curated.sort(key=lambda x: (not x.get("is_hot"), -(x.get("estimated_value_usd") or 0)))

    return curated, new_items
