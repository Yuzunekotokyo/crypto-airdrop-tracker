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
    """手動管理の注目エアドロップシードデータ (毎日の定期更新でリサーチし直す)"""
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
            "estimated_value_usd": 750,
            "description": "世界最大の分散型予測市場プラットフォーム。2025年10月にPOLYトークン発行とエアドロップ実施を公式表明済み。供給の5〜10%を参加者に配布予定で、TGEは2026年Q3〜Q4が有力視されている。",
            "tasks": ["実際のマーケットでベット/取引を継続", "USDC残高を維持してプラットフォームを利用", "米国版KYCを完了(該当者)", "紹介プログラムに参加"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/45106/small/polymarket.png",
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
            "type": "ポイントプログラム",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "MetaMask公式リワードプログラムSeason 2実施中。獲得ポイントはLINEAトークンに変換されるほか、Consensys CEOが示唆する将来のMASKトークン配布の判定材料になる可能性が高い。",
            "tasks": ["MetaMask Swapsでスワップ実行", "MetaMask Bridgeでブリッジ", "Rewardsプログラムにオプトイン", "ポイント蓄積を継続"],
            "end_date": (today + timedelta(days=150)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/40887/small/metamask.png",
            "url": "https://portfolio.metamask.io/rewards",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "opensea-sea",
            "name": "OpenSea (SEA)",
            "symbol": "SEA",
            "category": "NFT",
            "type": "新規上場/コミュニティ配布",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "OpenSea 2.0 (OS2) の一環としてSEAトークンが2026年に正式ローンチ。初回クレームで供給の約25%を配布済みで、残りは継続的なアクティビティ配布として展開中。",
            "tasks": ["OpenSeaでNFT取引を継続", "OS2プラットフォームを利用", "公式クレームページで受給資格を確認"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/40898/small/opensea.png",
            "url": "https://opensea.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "aster-dex-aster",
            "name": "Aster DEX (ASTER)",
            "symbol": "ASTER",
            "category": "DeFi/Perp DEX",
            "type": "ポイントプログラム",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 350,
            "description": "BNBチェーン発の永久先物DEX。総供給80億のうち53.5%をコミュニティ配分。複数ステージのポイント制エアドロップを継続実施中(取引量・ポジション保有・紹介で加点)。",
            "tasks": ["Asterで先物取引を実行", "ASTERトークンを保有", "流動性提供", "紹介プログラムに参加"],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39400/small/aster.png",
            "url": "https://www.asterdex.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "paradex",
            "name": "Paradex",
            "symbol": "未定",
            "category": "DeFi/Perp DEX",
            "type": "ポイントプログラム",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 450,
            "description": "Starknet基盤の永久先物取引所。供給の20%をコミュニティ配布に充てることを確約済み。Season 2は2026年Q3まで延長され、毎週金曜に400万XPが配布されている。",
            "tasks": ["Paradexで先物取引", "流動性提供(LP)", "オプション/XUSD機能を利用", "毎週配布のXPを蓄積"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39584/small/paradex.png",
            "url": "https://www.paradex.trade/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "backpack-bp",
            "name": "Backpack (BP)",
            "symbol": "BP",
            "category": "取引所",
            "type": "配布完了 (参考情報)",
            "status": "ended",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "2026年3月23日にTGE実施済み。供給の25% (2.5億BP) をポイント保有者・Mad Lads NFT保有者に配布完了。インサイダー配分なしで話題に。残りはマイルストーン連動で段階解放予定。",
            "tasks": [],
            "end_date": "2026-03-23",
            "logo": "https://assets.coingecko.com/coins/images/39916/small/backpack.png",
            "url": "https://backpack.exchange/",
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
