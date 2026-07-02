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
    """手動管理の注目エアドロップシードデータ。毎日の実行時にWeb検索で得た最新情報を基に更新する。"""
    today = datetime.utcnow()
    return [
        {
            "id": "hyperliquid-hype-s2",
            "name": "Hyperliquid Season 2 (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "レトロアクティブ Season2",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1500,
            "description": "オンチェーン永久先物DEX。Season1は史上最大級のエアドロップ($6.2B評価)。供給の38.888%がSeason2向けに確保されており、2026年2月開始のHyperEVM(スマートコントラクト層)はまだ参加者が少なく狙い目。",
            "tasks": ["HyperCoreでの先物取引・ステーキング(HYPEステークで1日8ポイント/枚)", "HyperEVM上でのDeFiアプリ利用", "strict list銘柄(HYPE/PURR/HFUN/CATBAL)の保有・取引"],
            "end_date": "未定(スナップショット時期は事前に公表されない見込み)",
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-07",
        },
        {
            "id": "layerzero-zro-s2",
            "name": "LayerZero Season2 / Zero L1 (ZRO)",
            "symbol": "ZRO",
            "category": "インフラ",
            "type": "レトロアクティブ Season2",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 600,
            "description": "クロスチェーンメッセージングプロトコル。2026年2月11日に独自L1「Zero」を発表、Tether・Citadel Securitiesが戦略投資、Cathie Wood(ARK)がアドバイザー就任。Season2向けに供給の15.3%(1.5億ドル以上相当)を確保。",
            "tasks": ["Stargate経由でのマルチチェーンブリッジ", "複数チェーンでのトランザクション実績", "LayerZero対応dApps・Zero L1エコシステム利用"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/28206/small/ftxG9_TJ_400x400.jpeg",
            "url": "https://layerzero.network/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-07",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY・未上場)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "将来のトークン配布(未確定)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 350,
            "description": "世界最大級の分散型予測市場。CMOがトークン発行を公言、供給の約5〜10%をアクティブトレーダー/コミュニティに配布予定。ワールドカップ2026関連マーケットで50,000 USDTの流動性インセンティブを2026年6月11日〜7月19日の期間限定で実施中 — 今が参加の好機。",
            "tasks": ["複数カテゴリのマーケットで継続的に取引", "X(旧Twitter)アカウントを連携", "ワールドカップ関連マーケットで指値注文(マーケットメイク)を提供 (7/19まで)"],
            "end_date": "2026-07-19",
            "logo": "https://assets.coingecko.com/coins/images/38155/small/polymarket.jpg",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-07",
        },
        {
            "id": "base-token",
            "name": "Base Network Token (未確定)",
            "symbol": "—",
            "category": "Layer2",
            "type": "検討中トークン",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Coinbase開発のL2。2025年9月にJesse Pollak氏がネイティブトークン検討を公式表明(従来の「発行予定なし」から方針転換)。2026年Q2〜Q4の間にリリース検討中も、詳細は未発表の思惑段階。",
            "tasks": ["Base上でのdApps利用・トランザクション実績を積む", "公式発表を継続的にウォッチ"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/31199/small/base-logo.png",
            "url": "https://base.org/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-2026-07",
        },
        {
            "id": "backpack-token",
            "name": "Backpack (BACKPACK)",
            "symbol": "BACKPACK",
            "category": "取引所",
            "type": "TGE済み・Season4ポイント継続中",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 150,
            "description": "Solana系次世代CEX。2026年3月23日にTGE実施済み(供給の25%をコミュニティ配布 = Pointsホルダー24%+Mad Ladsホルダー1%)。2025年11月開始のSeason4ポイントが金曜ごとに取引量ベースで加算され続けており、追加配布機会が残る。",
            "tasks": ["現物・無期限先物の取引量を積み上げる(毎週金曜集計)", "Mad Lads NFT保有でVIP1資格", "TGE前の本人確認(mandatory verification)を完了"],
            "end_date": "進行中",
            "logo": "https://assets.coingecko.com/coins/images/39676/small/backpack.png",
            "url": "https://backpack.exchange/",
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
