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
    """手動管理の注目エアドロップシードデータ (2026年7月時点の最新情報に基づき更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "hyperliquid-season2",
            "name": "Hyperliquid Season 2 (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "追加エアドロップ (Season 2)",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1200,
            "description": "高速オンチェーン永久先物DEX。HyperEVMも稼働中で、Season 1に続き取引量・HLP預入・手数料上位者にポイントが付与されている。スナップショット時期は未発表。",
            "tasks": [
                "Hyperliquidで累計$1,000以上の取引",
                "HLPへ流動性を預入 (3倍加点)",
                "HyperEVMへHYPEをブリッジしDeFiを利用",
                "リファラルで5人以上を招待",
            ],
            "end_date": "未定 (スナップショット未発表)",
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://app.hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "grass-depin",
            "name": "Grass (GRASS)",
            "symbol": "GRASS",
            "category": "DePIN",
            "type": "報酬クレーム中 + Season 2予定",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "未使用の通信帯域を提供するDePINプロジェクト。Stage 2報酬 (USDC) のクレームが7月22日に開始 (2027年1月22日締切)。Season 2では供給量17%・約1.7億GRASSの追加配布が控えている。",
            "tasks": [
                "Grassアプリ/拡張機能をインストールし帯域を共有",
                "毎日ログインしアップタイムを維持",
                "リファラルでネットワークポイントを上乗せ",
                "Reward CheckerでStage 2報酬を確認しクレーム",
            ],
            "end_date": "2027-01-22",
            "logo": "https://assets.coingecko.com/coins/images/51172/small/Grass.png",
            "url": "https://www.grass.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "予定トークン (未確定)",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "最大手の予測市場。CMOが「トークンとエアドロップは実施する」と公式に言及済みだが、スナップショットや配布条件は未発表 (2026年後半との観測)。",
            "tasks": [
                "Polymarketで実際に予測市場に参加し取引量を積む",
                "流動性報酬プログラムに参加",
                "ウォレットでの継続的な活動を維持",
                "公式X/Discordで最新情報をフォロー",
            ],
            "end_date": "未定",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "metamask-mask",
            "name": "MetaMask Rewards (MASK)",
            "symbol": "MASK",
            "category": "ウォレット",
            "type": "予定トークン (未確定)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 600,
            "description": "世界最大級のウォレット。$MASKトークンの発行を公式表明しており、MetaMask Rewardsのポイントが将来の配布基準になる見込み (2026年Q3〜Q4予想)。公式チャネル以外の「配布サイト」は詐欺のため要注意。",
            "tasks": [
                "MetaMask Rewardsに登録しポイントを蓄積",
                "MetaMask Swap/Bridgeを日常的に利用",
                "連携チェーン (Linea等) での活動を継続",
                "公式発表 (metamask.io/news) を定期確認",
            ],
            "end_date": "未定",
            "logo": "",
            "url": "https://portfolio.metamask.io/rewards",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-l2-token",
            "name": "Base",
            "symbol": "—",
            "category": "Layer2",
            "type": "噂・トークン検討中",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Coinbase発のL2。開発者が「ネットワークトークンを検討中」と発言したのみで正式発表はまだ無い。実現すればArbitrum級の大型配布との観測もあるが、現時点ではあくまで噂の段階。",
            "tasks": [
                "Base上でのブリッジ・スワップなど基本利用を継続",
                "Base上の主要dAppを日常的に使用",
                "公式発表を待つ (現時点でエアドロップは未確約)",
            ],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/asset_platforms/images/131/small/base-network.png",
            "url": "https://base.org/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "particle-network",
            "name": "Particle Network (PARTI)",
            "symbol": "PARTI",
            "category": "インフラ (チェーン抽象化)",
            "type": "テストネットポイント",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 250,
            "description": "ウォレット/チェーン抽象化基盤。テストネット参加者にPARTIポイントを配布中で、将来のエアドロップとThe People's Launchpadでの優待を確約済み。",
            "tasks": [
                "Particle Testnetに参加しデイリーチェックイン",
                "Universal Gas (USDG) でテストネットのガスを支払う",
                "リファラルでポイントを上乗せ",
                "テストネットトークンをデポジット",
            ],
            "end_date": "未定",
            "logo": "",
            "url": "https://particle.network/",
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
