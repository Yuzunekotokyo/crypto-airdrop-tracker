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
    """手動管理の注目エアドロップシードデータ (2026年7月時点の最新情報でリサーチ・更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "ink-kraken",
            "name": "Ink (INK) — Kraken L2",
            "symbol": "INK",
            "category": "Layer2",
            "type": "ポイント制",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 600,
            "description": "Kraken発のOP Stack系L2。Ink Points Season1が2026年4月開始、Kraken確約$25Mの配布枠あり。TGEは2026年Q2〜Q3見込みで直近最注目の案件。",
            "tasks": ["Krakenで資産をInkへブリッジ", "Nado (パーペチュアルDEX) で取引", "Tydro (レンディング) で流動性供給", ".ink ドメイン登録"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39897/small/ink.png",
            "url": "https://inkonchain.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-token",
            "name": "Base (BASE)",
            "symbol": "BASE",
            "category": "Layer2",
            "type": "未確定 (検討中)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 900,
            "description": "Coinbase運営のL2。2025年9月にJesse Pollak氏がネイティブトークン検討を公式表明。日次取引高は数十億ドル規模で、実現すればArbitrumの$12億分配を超える可能性。Polymarketでは2026年内ローンチ確率69%。",
            "tasks": ["ETHをBaseへブリッジ", "Base上のdAppsを継続利用", "Coinbase Walletでの活動実績を積む"],
            "end_date": (today + timedelta(days=170)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/asset_platforms/images/131/small/base-network.png",
            "url": "https://base.org/",
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
            "estimated_value_usd": 500,
            "description": "世界最大級の予測市場プラットフォーム。CMOがトークン・エアドロップ実施を公式に明言済み (配布詳細は未発表)。継続的な取引実績が有力な判定基準と目される。",
            "tasks": ["複数カテゴリで継続的に取引", "X (旧Twitter) アカウントを連携", "Rewardsプログラムに参加"],
            "end_date": (today + timedelta(days=140)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/32440/small/polymarket.png",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "ウォレット/インフラ",
            "type": "ポイント制",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "月間3,000万以上のアクティブユーザーを抱えるConsensys製ウォレット。ネイティブトークン発行をCEOが公式表明済み。ローンチは2026年Q3〜Q4が有力視される。",
            "tasks": ["MetaMask Rewardsでのスワップ", "パーペチュアル取引", "MetaMask Card利用", "新規ユーザー招待"],
            "end_date": (today + timedelta(days=150)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/40273/small/metamask.png",
            "url": "https://metamask.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "layerzero-zro",
            "name": "LayerZero (ZRO) — 次期シーズン",
            "symbol": "ZRO",
            "category": "インフラ",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 350,
            "description": "クロスチェーンメッセージングプロトコル。全供給量の約38.3%がコミュニティ配布枠として確保されており、うち約30%が未配布のため今後の追加シーズンが見込まれる。",
            "tasks": ["Stargate経由でブリッジを継続実行", "複数チェーンでのトランザクション", "LayerZero対応dApps利用"],
            "end_date": (today + timedelta(days=100)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/28206/small/ftxG9_TJ_400x400.jpeg",
            "url": "https://layerzero.network/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "opensea-sea",
            "name": "OpenSea (SEA) — 追加配布枠",
            "symbol": "SEA",
            "category": "NFT",
            "type": "ポイント制",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 250,
            "description": "最大手NFTマーケットプレイス。SEAトークンは既に確認済みだが追加配布の新ラウンド日程は未発表。",
            "tasks": ["OpenSea上でのNFT売買", "OS2 (新プラットフォーム) の利用", "コミュニティ活動への参加"],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/28452/small/opensea.png",
            "url": "https://opensea.io/",
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
