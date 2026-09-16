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
    """手動管理の注目エアドロップシードデータ。
    2026年9月時点の最新情報 (Web検索調査ベース) に更新済み。
    """
    today = datetime.utcnow()
    return [
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "ウォレット",
            "type": "ポイント/リワード",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 2000,
            "description": "Consensys CEOのJoseph Lubin氏が「予想より早く」ローンチすると示唆。MetaMask Rewardsプログラムでポイントが継続蓄積中で、暗号資産史上最大級のエアドロップになる可能性がある。スナップショット日・配布条件は未発表。",
            "tasks": ["MetaMaskウォレットでスワップを実行", "MetaMask Rewardsプログラムでポイント獲得", "複数チェーンでのウォレット利用実績を積む"],
            "end_date": "未定 (2026年Q3-Q4予想)",
            "logo": "https://assets.coingecko.com/coins/images/40217/small/metamask.png",
            "url": "https://rewards.metamask.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "research-2026-09",
        },
        {
            "id": "base-token",
            "name": "Base (Coinbase L2)",
            "symbol": "—",
            "category": "Layer2",
            "type": "取引所L2トークン",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 1500,
            "description": "Coinbaseが手がけるBaseチームがネットワークトークンの検討を表明。正式なエアドロップ発表・詳細条件は未確定だが期待度は非常に高い。実現すれば上場企業初のL2トークンとなる。",
            "tasks": ["Base上でトランザクションを実行", "Aerodromeなど対応dAppsを利用", "Coinbase Walletでのオンチェーン活動を継続"],
            "end_date": "未定 (2026年Q2-Q4予想)",
            "logo": "https://assets.coingecko.com/coins/images/31145/small/base.png",
            "url": "https://base.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "research-2026-09",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "CMOのMatthew Modabber氏が「トークンとエアドロップは実施される」と公言。米国での正式展開も拡大中。供給の5〜10%が対象者向けに配分される見込みだが、スナップショット時期は未発表。",
            "tasks": ["Polymarketで継続的に取引する", "複数カテゴリの市場に参加", "Xアカウントを連携し取引履歴を積む"],
            "end_date": "未定 (2026年後半予想)",
            "logo": "https://assets.coingecko.com/coins/images/predictions/polymarket.png",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "research-2026-09",
        },
        {
            "id": "aster-dex",
            "name": "Aster (ASTER)",
            "symbol": "ASTER",
            "category": "DeFi/DEX",
            "type": "ベスティング配布",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 600,
            "description": "パーペチュアルDEX。ASTERトークンは既にローンチ済みで、100%ベスティングを選択した参加者向けの追加クレーム期間が2026年10月28日〜11月28日に設定されている。期限が近いため要チェック。",
            "tasks": ["Asterでの先物取引実績を積む", "ベスティングオプションを選択・確認", "10/28開始のクレームポータルで申請"],
            "end_date": "2026-11-28",
            "logo": "https://assets.coingecko.com/coins/images/39875/small/aster.png",
            "url": "https://asterdex.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "research-2026-09",
        },
        {
            "id": "edgex",
            "name": "EdgeX",
            "symbol": "—",
            "category": "DeFi/DEX",
            "type": "ポイントファーミング",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "急成長中のパーペチュアルDEX。トークン未発行のため先行ファーミングの好機とされている。",
            "tasks": ["EdgeXでの取引でポイント獲得", "流動性提供", "リファラルプログラムに参加"],
            "end_date": "未定",
            "logo": "",
            "url": "https://edgex.exchange/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "research-2026-09",
        },
        {
            "id": "lighter-season3",
            "name": "Lighter Season 3",
            "symbol": "LIT",
            "category": "DeFi/DEX",
            "type": "ポイントファーミング",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 400,
            "description": "高速オーダーブック型パーペチュアルDEX。Season1-2で供給の25%を配布済み、Season3が開始され追加配布の対象になっている。直近の出来高は月間ピーク比で大幅減少しており早期参加が有利。",
            "tasks": ["Lighterでの取引実績を積む", "Season3ポイントプログラムに参加", "継続的な出来高を維持"],
            "end_date": "未定",
            "logo": "",
            "url": "https://lighter.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "research-2026-09",
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
