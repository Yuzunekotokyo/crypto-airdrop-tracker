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
    """手動管理の注目エアドロップシードデータ (2026年7月時点の最新情報で更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "grass-season2",
            "name": "Grass Season 2 (USDC配布)",
            "symbol": "GRASS",
            "category": "DePIN",
            "type": "クレーム受付中",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 150,
            "description": "帯域幅共有型DePINネットワーク。Season 2はUSDCで配布され、2026年7月22日にクレーム開始。Epoch 1〜19 (2024年10月〜2026年6月) の貢献分が対象。",
            "tasks": ["Grass公式サイトでSeason 2クレームページにアクセス", "非custodialウォレットをパスキーまたはメールOTPで作成", "対象エポックのブラウザ拡張機能利用実績を確認しUSDCをクレーム"],
            "end_date": "2027-01-22",
            "logo": "",
            "url": "https://www.getgrass.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY・未確定)",
            "symbol": "POLY",
            "category": "予測市場/DeFi",
            "type": "レトロアクティブ(予定)",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "世界最大級の分散型予測市場。CMOがトークンとエアドロップの実施を公式に明言。供給の5〜10%がアクティブトレーダー向けに配分される見込み。",
            "tasks": ["Polymarketで実際に予測市場取引を行う", "取引量・市場の多様性を積み重ねる", "Xアカウントをウォレットにリンク", "継続的なアクティビティを維持"],
            "end_date": "未定（トークン発行時期未確定）",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "katana-network-kat",
            "name": "Katana Network (KAT)",
            "symbol": "KAT",
            "category": "DeFi/Layer2",
            "type": "未確定エアドロップ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 300,
            "description": "DeFi特化のLayer2ネットワーク。流動性提供やKaitoキャンペーン参加でポイント(krates)を獲得可能。",
            "tasks": ["Katanaダッシュボードでウォレット接続", "ETH/USDC/USDT/WBTCなどをデポジットしkrates獲得", "Katana x Kaitoキャンペーンに参加"],
            "end_date": "未定",
            "logo": "",
            "url": "https://katana.network/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "aether-depin",
            "name": "Aether (帯域幅DePIN)",
            "symbol": "AETHER",
            "category": "DePIN",
            "type": "ポイント制エアドロップ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 100,
            "description": "インターネット帯域幅の共有で報酬を得るDePINプロジェクト。Grassと並び注目度上昇中だが、トークン配布は未確定。",
            "tasks": ["公式アプリ/拡張機能をインストール", "バックグラウンドで帯域幅を共有しポイント獲得", "TGE(トークン生成イベント)の公式発表を待つ"],
            "end_date": "未定",
            "logo": "",
            "url": "https://airdrops.io/categories/depin/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-network",
            "name": "Base (Coinbase L2・噂)",
            "symbol": "—",
            "category": "Layer2",
            "type": "噂・未確定",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 500,
            "description": "Coinbase運営のEthereum L2。トークン未発行だが2026年に最有力のエアドロップ候補として名前が挙がり続けている。",
            "tasks": ["Base上でのトランザクション・DeFi利用実績を積む", "Base対応dAppsの利用", "公式発表を注視"],
            "end_date": "未定",
            "logo": "",
            "url": "https://base.org/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "opensea",
            "name": "OpenSea (噂)",
            "symbol": "—",
            "category": "NFTマーケットプレイス",
            "type": "噂・未確定",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 200,
            "description": "最大手NFTマーケットプレイス。トークン未発行だがBase・MetaMask・Polymarketと並び有力候補として言及されている。",
            "tasks": ["OpenSeaでのNFT取引実績を積む", "OS2新機能の利用", "公式発表を注視"],
            "end_date": "未定",
            "logo": "",
            "url": "https://opensea.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "xstocks",
            "name": "xStocks",
            "symbol": "—",
            "category": "RWA/トークン化株式",
            "type": "ポイント制",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 150,
            "description": "株式をトークン化して取引できるプラットフォーム。2026年7月の注目エアドロップ候補として言及。",
            "tasks": ["xStocksプラットフォームでトークン化株式を取引", "対応DEX/チェーンでの利用実績を積む"],
            "end_date": "未定",
            "logo": "",
            "url": "https://xstocks.com/",
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
