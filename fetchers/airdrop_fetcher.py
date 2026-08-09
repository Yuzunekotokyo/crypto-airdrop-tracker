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
    """手動管理の注目エアドロップシードデータ (2026年8月時点の最新情報に基づき更新)"""
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
            "estimated_value_usd": 1500,
            "description": (
                "予測市場最大手。CMOがPOLYトークンとエアドロップの実施を公式に認めたが、"
                "配布条件・時期は米国向けアプリ再展開の完了待ちで未公表。過去の取引量・流動性提供・"
                "アクティブ週数が対象基準になる見込み（供給の5〜10%が有力視・非公式）。"
            ),
            "tasks": ["Polymarketで実際に予測市場取引を行う", "複数カテゴリの市場に継続的に参加", "公式アナウンスを継続的に確認"],
            "end_date": "未定 (2026年内の発表を待つ)",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "opensea-sea",
            "name": "OpenSea (SEA)",
            "symbol": "SEA",
            "category": "NFT/マーケットプレイス",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 900,
            "description": (
                "最大手NFTマーケットプレイス。供給の50%をコミュニティに配分予定で、初回配布だけで"
                "総供給の約25%を放出する計画。当初2026年Q1予定だったが市況を理由に延期中。"
            ),
            "tasks": ["OpenSeaでのNFT売買・出品履歴を作る", "ウォレット連携で過去の利用実績を確認", "公式Xでの延期後の発表を待つ"],
            "end_date": "未定 (延期中)",
            "logo": "",
            "url": "https://opensea.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "fuel-network-fuel",
            "name": "Fuel Network (FUEL)",
            "symbol": "FUEL",
            "category": "インフラ",
            "type": "テストネット参加",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 350,
            "description": "Sway言語を用いる高性能実行レイヤー。ノード運用・技術的貢献者向けの報酬設計が特徴。",
            "tasks": ["テストネットでのノード運用", "Fuel対応dAppsの利用", "開発者コミュニティでの貢献"],
            "end_date": "未定",
            "logo": "",
            "url": "https://fuel.network/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-network-token",
            "name": "Base ネットワークトークン",
            "symbol": "TBA",
            "category": "Layer2",
            "type": "検討段階",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": (
                "Coinbase運営のL2。ネットワークトークン発行の検討を開始したと発表したのみで、"
                "配布方式・時期・対象基準は一切未定（2026年Q2〜Q4に何らかの動きの可能性）。"
            ),
            "tasks": ["Base上でのdApps利用実績を作っておく", "公式アナウンスを継続的に確認"],
            "end_date": "未定 (検討段階)",
            "logo": "",
            "url": "https://base.org/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "layerzero-zro",
            "name": "LayerZero (ZRO)",
            "symbol": "ZRO",
            "category": "インフラ",
            "type": "レトロアクティブ",
            "status": "ended",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "クロスチェーンメッセージングプロトコル。2024年6月にTGE済み。エアドロップは終了しています（参考掲載）。",
            "tasks": [],
            "end_date": "2024-06-20 (終了)",
            "logo": "https://assets.coingecko.com/coins/images/28206/small/ftxG9_TJ_400x400.jpeg",
            "url": "https://layerzero.network/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "scroll-scr",
            "name": "Scroll (SCR)",
            "symbol": "SCR",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "ended",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "EVM互換ZK-Rollup。2024年10月にTGE済み。エアドロップは終了しています（参考掲載）。",
            "tasks": [],
            "end_date": "2024-10-15 (終了)",
            "logo": "https://assets.coingecko.com/coins/images/25734/small/scroll.png",
            "url": "https://scroll.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "zksync-era",
            "name": "zkSync Era",
            "symbol": "ZK",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "ended",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Matter Labsが開発するZK-Rollup。2024年6月にTGE済み。エアドロップは終了しています（参考掲載）。",
            "tasks": [],
            "end_date": "2024-06-24 (終了)",
            "logo": "https://assets.coingecko.com/coins/images/38043/small/ZKTokenBlack.png",
            "url": "https://zksync.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-hype",
            "name": "Hyperliquid (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "取引所トークン",
            "status": "ended",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "高速オンチェーン永久先物DEX。2024年11月にTGE済み。エアドロップは終了しています（参考掲載）。",
            "tasks": [],
            "end_date": "2024-11-29 (終了)",
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "eigenlayer-eigen",
            "name": "EigenLayer (EIGEN)",
            "symbol": "EIGEN",
            "category": "インフラ",
            "type": "リステーキング",
            "status": "ended",
            "difficulty": "hard",
            "estimated_value_usd": 0,
            "description": "Ethereumのリステーキングプロトコル。2024年10月にTGE済み。エアドロップは終了しています（参考掲載）。",
            "tasks": [],
            "end_date": "2024-10-01 (終了)",
            "logo": "https://assets.coingecko.com/coins/images/33751/small/eigen.png",
            "url": "https://eigenlayer.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "movement-move",
            "name": "Movement (MOVE)",
            "symbol": "MOVE",
            "category": "Layer2",
            "type": "新規上場",
            "status": "ended",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Move VMを使用するEthereum L2。2024年12月にTGE済み。エアドロップは終了しています（参考掲載）。",
            "tasks": [],
            "end_date": "2024-12-09 (終了)",
            "logo": "https://assets.coingecko.com/coins/images/39619/small/MOVE_color.png",
            "url": "https://movementlabs.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "monad-mon",
            "name": "Monad (MON)",
            "symbol": "MON",
            "category": "Layer1",
            "type": "レトロアクティブ",
            "status": "ended",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "高速並列実行EVM互換L1。2025年11月24日にメインネット稼働とエアドロップ（供給の3.3%・約28.9万ウォレット対象）が完了済み（参考掲載）。",
            "tasks": [],
            "end_date": "2025-11-24 (終了)",
            "logo": "",
            "url": "https://www.monad.xyz/",
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
