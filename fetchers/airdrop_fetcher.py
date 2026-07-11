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
    """手動管理の注目エアドロップシードデータ。
    毎日の自動更新実行時、Web検索で得た最新情報をもとに書き換える。
    最終更新: 2026-07-11 (それ以前のLayerZero/Scroll/zkSync/EigenLayer/Movement等は
    既にTGE済みのため、現在アクティブな新規注目案件に総入れ替え)。
    """
    today = datetime.utcnow()
    return [
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "ウォレット",
            "type": "エアドロップ濃厚",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 350,
            "description": "世界最大級のウォレット(月間利用者3000万人超)。ConsensysのCEOが2026年にMASKトークン発行を公式に確認済み。史上最大規模の配布になる可能性。",
            "tasks": ["MetaMaskウォレットを継続利用", "MetaMask Rewardsポイント収集", "MetaMask Card/Swap利用"],
            "end_date": "未定 (2026年内ローンチ見込み)",
            "logo": "https://assets.coingecko.com/coins/images/263/small/MetaMask-icon-fox.svg",
            "url": "https://metamask.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-07",
        },
        {
            "id": "base-l2",
            "name": "Base (Coinbase L2)",
            "symbol": "BASE?",
            "category": "Layer2",
            "type": "未確定・高期待",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 600,
            "description": "Coinbase発のEthereum L2。JPMorganアナリストは時価総額120〜340億ドル規模と試算。創業者Jesse Pollak氏はトークン発行を検討中と明言(未確定)。",
            "tasks": ["Base上でのDeFi/dApps利用実績", "Baseブリッジ利用", "Coinbase Wallet連携での活動"],
            "end_date": "未定 (トークン発行は未確定)",
            "logo": "https://assets.coingecko.com/asset_platforms/images/131/small/base-network.png",
            "url": "https://base.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-07",
        },
        {
            "id": "backpack",
            "name": "Backpack",
            "symbol": "BACK?",
            "category": "取引所/ウォレット",
            "type": "TGE計画発表済み",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 400,
            "description": "自己管理型ウォレット・規制取引所・Mad Lads NFTを展開。$37M調達済み、2026年2月にTGE計画を正式発表しており実現濃厚。",
            "tasks": ["Backpack取引所での取引実績", "Backpackウォレット利用", "Mad Lads等エコシステム参加"],
            "end_date": "未定 (TGE計画発表済み)",
            "logo": "https://assets.coingecko.com/coins/images/39456/small/backpack.png",
            "url": "https://backpack.exchange/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-07",
        },
        {
            "id": "megaeth",
            "name": "MegaETH",
            "symbol": "MEGA",
            "category": "Layer2",
            "type": "メインネット稼働中",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 500,
            "description": "超高速EVM互換L2。The Fluffle NFT保有者にMEGA供給の5%以上を配布予定。メインネット実利用も評価対象。",
            "tasks": ["MegaETHメインネットでのトランザクション", "The Fluffle NFT保有", "エコシステムdApps利用"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39619/small/megaeth.png",
            "url": "https://megaeth.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-07",
        },
        {
            "id": "axiom-dex",
            "name": "Axiom",
            "symbol": "AXIOM?",
            "category": "DeFi/DEX",
            "type": "インセンティブ・テストネット",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 350,
            "description": "Solana / Hyperliquid上で動くプライバシー重視の分散型取引所。現在インセンティブ付きテストネットを実施中。",
            "tasks": ["テストネットでの取引", "流動性提供", "紹介プログラム参加"],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://axiom.trade/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-07",
        },
        {
            "id": "n1-layern",
            "name": "N1 (旧Layer N)",
            "symbol": "N1?",
            "category": "インフラ",
            "type": "未確定",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 250,
            "description": "旧Layer N。公式なエアドロップ確約はまだないが、テストネット・エコシステムキャンペーンへの早期参加が有利とされる。",
            "tasks": ["テストネット参加", "エコシステムキャンペーン参加", "コミュニティ活動"],
            "end_date": "未定",
            "logo": "",
            "url": "https://n1.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-07",
        },
        {
            "id": "bitcoin-hyper",
            "name": "Bitcoin Hyper (HYPER)",
            "symbol": "HYPER",
            "category": "Solanaエコシステム",
            "type": "ステーキング",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 150,
            "description": "Solanaエコシステムで注目のプロジェクト。HYPERのステーキングで報酬機会。",
            "tasks": ["HYPERをステーキング", "コミュニティ参加"],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://airdrops.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-07",
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
