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
    """手動管理の注目エアドロップシードデータ。2026年9月時点の最新情報に基づき更新。"""
    today = datetime.utcnow()
    return [
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "ウォレット",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Consensys CEO Joseph Lubin氏が「予想より早く」登場すると公言。2024〜2026年のウォレット利用実績に基づき、アクティビティスコアに応じて1ウォレットあたり250〜15,000 MASKが配布されると噂されている(未公式)。時期はConsensysのIPOに絡めた2026年Q3〜Q4が有力視。",
            "tasks": ["MetaMask経由でスワップ・ブリッジを実行", "MetaMask Rewardsプログラムへ参加してポイント蓄積", "パープス取引など対応dAppsの利用"],
            "end_date": "未定 (2026年Q3〜Q4予想)",
            "logo": "https://assets.coingecko.com/coins/images/22990/small/metamask.png",
            "url": "https://metamask.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-token",
            "name": "Base",
            "symbol": "BASE(未定)",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 2000,
            "description": "Coinbase開発のL2「Base」がネイティブトークン発行を検討中とJesse Pollak氏(Base創設者)が公表。JPMorganの試算では時価総額120〜340億ドル規模になる可能性があり、コミュニティ配分が20〜25%なら1人あたり$500〜$5,000超の価値になるとの見方も。上場企業Coinbase発のため規制面の扱いが焦点。",
            "tasks": ["Base上のdApps利用", "Baseへのブリッジ実行", "各種プロトコルとの継続的なインタラクション"],
            "end_date": "未定 (2026年Q2〜Q4に発表の可能性)",
            "logo": "https://assets.coingecko.com/asset_platforms/images/131/small/base-network.png",
            "url": "https://base.org/",
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
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 500,
            "description": "OpenSeaがSEAトークンのTGEを正式発表済み。供給量の50%をコミュニティに配分し、初回クレームで全体の約25%を放出予定。長期利用者(OG)と「Voyages」ポイントプログラムの現行参加者の双方を個別に評価する方式。",
            "tasks": ["OpenSea「Voyages」ポイントプログラムに参加", "NFTの売買・出品を継続的に実施", "過去のOpenSea利用実績を保持(2025年以前の利用者は評価対象)"],
            "end_date": "配布中 (2026年Q1にTGE済み、追加配布継続中)",
            "logo": "https://assets.coingecko.com/coins/images/19556/small/opensea.png",
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
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 400,
            "description": "CMOのMatthew Modabber氏が「トークンとエアドロップは実施する」と公式に明言。正式な時期・基準は未発表だが、コミュニティ予想では2026年後半が有力。継続的な取引実績と複数カテゴリでの参加が評価される見込み。",
            "tasks": ["予測市場での継続的な取引", "複数カテゴリ(政治・スポーツ等)での参加", "X(Twitter)アカウントとの連携"],
            "end_date": "未定 (2026年後半予想)",
            "logo": "https://assets.coingecko.com/coins/images/38753/small/polymarket.png",
            "url": "https://polymarket.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "backpack-token",
            "name": "Backpack (BACKPACK)",
            "symbol": "BACKPACK",
            "category": "取引所",
            "type": "取引所トークン",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "2026年3月23日にTGE実施済み。供給量の25%をコミュニティに配分(ポイント保有者24%・Mad Ladsホルダー1%)。現在はSeason 4のポイントファーミングが進行中で、継続的な取引で追加配分の対象になる可能性。",
            "tasks": ["Backpack取引所での現物・先物取引でポイント獲得(毎週金曜集計)", "本人確認(KYC)を完了", "Mad Lads NFT保有者はウォレット連携を確認"],
            "end_date": "Season進行中",
            "logo": "https://assets.coingecko.com/coins/images/39676/small/backpack.png",
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
