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
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 400,
            "description": "予測市場最大手。CMOが「トークンとエアドロップは確定」と公言済みだが、スナップショット日程は未発表。2026年Q3〜Q4が有力視されている。",
            "tasks": ["Polymarket(米国版含む)で継続的に取引", "様々なマーケットへ参加し活動実績を積む", "公式アカウントで正式発表を確認"],
            "end_date": "未定 (2026年Q3-Q4予想)",
            "logo": "https://assets.coingecko.com/markets/images/polymarket.png",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "インフラ",
            "type": "リワードプログラム",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "業界最大級のウォレット。MetaMask Rewardsのポイントがトークン化される見込みで「史上最大級のトークンイベント」との呼び声も。ConsenSys IPOに合わせたQ3〜Q4予想。",
            "tasks": ["MetaMaskモバイルでRewardsに参加", "スワップ・ブリッジ・Perps取引でポイント獲得", "継続的なウォレット利用実績を積む"],
            "end_date": "未定 (2026年Q3-Q4予想)",
            "logo": "https://assets.coingecko.com/coins/images/40898/small/metamask.png",
            "url": "https://metamask.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "backpack-bp",
            "name": "Backpack (BP)",
            "symbol": "BP",
            "category": "取引所トークン",
            "type": "取引所リワード",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 250,
            "description": "Solana系取引所。2026年3月にBPトークンをTGEし供給の25%をコミュニティへ配布済み。毎週金曜のポイント集計による継続配布が進行中。",
            "tasks": ["Backpack Exchangeで現物・Perp取引を継続", "毎週金曜のポイント集計に向け取引量を積む", "Mad Lads NFT保有で追加配分"],
            "end_date": "継続中",
            "logo": "https://assets.coingecko.com/coins/images/40157/small/backpack.png",
            "url": "https://backpack.exchange/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "variational-var",
            "name": "Variational (VAR)",
            "symbol": "VAR",
            "category": "DeFi/デリバティブ",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "hard",
            "estimated_value_usd": 350,
            "description": "Arbitrum上の無手数料Perp DEX。供給の50%をコミュニティへ配布することを確約済み。Omniポイントプログラムは2026年Q3末まで実施予定。実資金・レバレッジ取引が必要な点に注意。",
            "tasks": ["omni.variational.io でウォレット接続", "実資金でPerp取引しOmniポイント獲得", "2025年12月17日以前の取引実績があれば+10%ブースト", "紹介プログラムを活用"],
            "end_date": "2026-09-30",
            "logo": "https://assets.coingecko.com/coins/images/40200/small/variational.png",
            "url": "https://omni.variational.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "opensea-sea",
            "name": "OpenSea (SEA)",
            "symbol": "SEA",
            "category": "NFT",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "最大手NFTマーケットプレイス。SEAトークンは複数回延期されているが正式に確定しており、供給の半分がコミュニティへ。初回配布で全体の約25%を放出予定。",
            "tasks": ["OpenSea上でNFTの売買・出品を継続", "ウォレットの利用実績を積む", "公式アナウンスで対象ウォレット確認"],
            "end_date": "未定 (延期中)",
            "logo": "https://assets.coingecko.com/coins/images/28684/small/opensea.jpeg",
            "url": "https://opensea.io/",
            "is_hot": False,
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
            "estimated_value_usd": 50,
            "description": "分散型帯域共有ネットワーク。Season 2は2026年7月22日にクレーム開始、2027年1月22日まで受付中。今回はUSDC建てで配布。",
            "tasks": ["公式サイトでウォレット接続しクレーム確認", "Epoch 1-19のNetwork/Uptimeポイントを確認", "期限(2027年1月22日)までにクレーム実行"],
            "end_date": "2027-01-22",
            "logo": "https://assets.coingecko.com/coins/images/37554/small/grass.png",
            "url": "https://www.grass.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-hype-s2",
            "name": "Hyperliquid Season 2",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "取引所リワード",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1000,
            "description": "高速オンチェーン永久先物DEX。独自L1チェーン上で動作し、Season 2の取引量ベースのポイント報酬が進行中。",
            "tasks": ["Hyperliquid上での先物取引", "流動性提供", "紹介プログラム参加"],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
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
    curated.sort(key=lambda x: (not x.get("is_hot"), -x.get("estimated_value_usd", 0)))

    return curated, new_items
