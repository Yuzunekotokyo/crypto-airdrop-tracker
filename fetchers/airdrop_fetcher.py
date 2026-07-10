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
    """手動管理の注目エアドロップシードデータ (Web調査に基づき定期的に更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "ウォレット",
            "type": "リワードプログラム",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 2000,
            "description": "MetaMaskが独自トークンMASKの発行を確認。Rewardsプログラム(Season 1でLINEAトークンを3000万ドル超配布)がエアドロップ資格判定に使われる見込み。2026年Q3-Q4のローンチが予想される「史上最大級」の案件。",
            "tasks": ["MetaMaskモバイルでRewardsプログラムに参加", "スワップ・ブリッジを実行", "MetaMask Cardでの支払い", "Perps取引でポイント獲得"],
            "end_date": (today + timedelta(days=150)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/13442/small/Metamask.png",
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
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1500,
            "description": "評価額20億ドル超の予測市場最大手。CMOがトークン発行を公式に認めており、供給の5〜10%をアクティブトレーダー・コミュニティに配分予定。TGE時期は米国展開完了後になる見込み。",
            "tasks": ["複数カテゴリの市場で継続的に取引", "指値注文で流動性提供リワードを獲得", "X(Twitter)アカウントを連携", "単一ウォレットで数ヶ月継続利用 (Sybil対策)"],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/48331/small/polymarket.png",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-hype-s2",
            "name": "Hyperliquid Season 2 (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "ポイント/リステーキング型",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1500,
            "description": "HYPE供給の約38.9%(約3.88億トークン)が将来の報酬用に留保。2026年2月開始のHyperEVM上での活動が新たな配分対象になる可能性。スナップショット日は未発表で、継続的な参加が推奨される。",
            "tasks": ["現物・Perps取引でポイント獲得 ($1毎に1pt)", "HYPEステーキング (1トークン/日で8pt)", "HyperEVMへのブリッジ・DeFi利用", "HyperSwapへの流動性供給"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-token",
            "name": "Base Token",
            "symbol": "BASE",
            "category": "Layer2",
            "type": "投機的 (未確定)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "CoinbaseのJesse PollakがBaseネットワークトークンの検討を公式に認めた (2025年9月)。2026年Q2〜Q4のローンチが取り沙汰されるが、配布方式・エアドロップ有無は未確定。Arbitrum/Optimismの前例から期待は高い。",
            "tasks": ["Base上でのトランザクション実行", "Base上のdApps利用", "公式発表を継続的にウォッチ"],
            "end_date": (today + timedelta(days=200)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/asset_platforms/images/131/small/base-network.png",
            "url": "https://base.org/",
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
