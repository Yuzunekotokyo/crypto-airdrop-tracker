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
    """手動管理の注目エアドロップシードデータ — 2026年6月30日更新"""
    today = datetime.utcnow()
    return [
        # ===== 🔥 2026年6月現在 アクティブ/近日TGE =====
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 1500,
            "description": "最大の分散型予測市場。CMOが2025年10月にトークン&エアドロップを公式確認。2026年後半TGE予定。取引量・アカウント年齢・カテゴリ分散が鍵。",
            "tasks": [
                "polymarket.comで予測市場取引を継続",
                "政治・暗号・スポーツなど複数カテゴリに分散",
                "設定からXアカウントを連携",
                "流動性提供プログラム参加",
                "紹介プログラム活用",
            ],
            "end_date": "2026-12-31",
            "logo": "https://assets.coingecko.com/coins/images/37202/small/polymarket.png",
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
            "type": "ロイヤルティ報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 2000,
            "description": "Consensys CEOが「予想より早くトークン来る」と明言。Season 2ポイントプログラム進行中。MetaMask Rewardsへのオプトインが必須。クリプト史上最大規模エアドロップになる可能性。",
            "tasks": [
                "MetaMask Mobileダウンロード & Rewardsオプトイン",
                "MetaMask内でスワップを定期的に実行",
                "Linea(L2)へのブリッジ & エコシステム利用",
                "MetaMask Cardの利用",
                "紹介プログラムへの参加",
                "ロイヤルティボーナスの請求",
            ],
            "end_date": "2026-12-31",
            "logo": "https://assets.coingecko.com/coins/images/13762/small/metamask.png",
            "url": "https://metamask.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-base",
            "name": "Base (BASE)",
            "symbol": "BASE",
            "category": "Layer2",
            "type": "エコシステム報酬",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 800,
            "description": "Coinbaseが開発するEthereum L2。2025年9月にチームがネットワークトークン検討を公式表明。エコシステムが急拡大中で、アクティビティ記録が重要。",
            "tasks": [
                "Baseネットワークへのブリッジ & 入金",
                "Base上でのDeFi/NFT活動",
                "Aerodrome・Uniswap v3など主要DEXの利用",
                "長期・継続的なオンチェーン活動",
                "複数週にわたるトランザクション",
            ],
            "end_date": "2026-12-31",
            "logo": "https://assets.coingecko.com/coins/images/34269/small/base.png",
            "url": "https://base.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-hype",
            "name": "Hyperliquid (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "取引報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 500,
            "description": "2026年6月1日にDOGEを抜き時価総額トップ10入り($160億)。オンチェーン永久先物DEX。継続的な取引・流動性提供でポイント獲得可能。",
            "tasks": [
                "Hyperliquid上での先物・スポット取引",
                "HLP(流動性プール)への参加",
                "紹介プログラムの活用",
            ],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "monad-mon",
            "name": "Monad (MON)",
            "symbol": "MON",
            "category": "Layer1",
            "type": "エコシステム報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "高速EVM互換L1。メインネット稼働中。第1回エアドロップは2025年10月に配布済。継続的なオンチェーン活動が次回配布に向け重要。",
            "tasks": [
                "monad.xyz上のdAppsを利用",
                "Monadエコシステムのトークンスワップ",
                "Discordコミュニティへの参加",
                "NFTミントやDeFi利用",
            ],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/47014/small/monad.jpg",
            "url": "https://monad.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        # ===== 配布済み (参考記録) =====
        {
            "id": "backpack-bp",
            "name": "Backpack (BP)",
            "symbol": "BP",
            "category": "取引所",
            "type": "ポイント報酬",
            "status": "ended",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "【配布完了 2026年3月23日】Solana系CEX。TGEにて総供給量25%をコミュニティに配布完了。",
            "tasks": [],
            "end_date": "2026-03-23",
            "logo": "https://assets.coingecko.com/coins/images/35557/small/backpack.jpg",
            "url": "https://backpack.exchange/",
            "is_hot": False,
            "added_date": "2026-03-23",
            "source": "curated",
        },
        {
            "id": "opensea-sea",
            "name": "OpenSea (SEA)",
            "symbol": "SEA",
            "category": "NFTマーケット",
            "type": "レトロアクティブ",
            "status": "ended",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "【配布完了 2026年Q1】最大NFTマーケット。総供給量の50%がコミュニティに配布完了。",
            "tasks": [],
            "end_date": "2026-03-31",
            "logo": "https://assets.coingecko.com/coins/images/12465/small/ghost.png",
            "url": "https://opensea.io/",
            "is_hot": False,
            "added_date": "2026-01-01",
            "source": "curated",
        },
        {
            "id": "movement-move",
            "name": "Movement (MOVE)",
            "symbol": "MOVE",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "ended",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "【配布完了 2024年12月】Move VMを使用するEthereum L2。エアドロップは配布済み。",
            "tasks": [],
            "end_date": "2024-12-31",
            "logo": "https://assets.coingecko.com/coins/images/39619/small/MOVE_color.png",
            "url": "https://movementlabs.xyz/",
            "is_hot": False,
            "added_date": "2024-12-01",
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
            "description": "【配布完了 2024年】Ethereumリステーキングプロトコル。EIGENトークンは配布済み。",
            "tasks": [],
            "end_date": "2024-10-31",
            "logo": "https://assets.coingecko.com/coins/images/33751/small/eigen.png",
            "url": "https://eigenlayer.xyz/",
            "is_hot": False,
            "added_date": "2024-01-01",
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
            "description": "【配布完了 2024年6月】クロスチェーンメッセージングプロトコル。ZROトークンは配布済み。",
            "tasks": [],
            "end_date": "2024-06-30",
            "logo": "https://assets.coingecko.com/coins/images/28206/small/ftxG9_TJ_400x400.jpeg",
            "url": "https://layerzero.network/",
            "is_hot": False,
            "added_date": "2024-01-01",
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
            "description": "【配布完了 2024年10月】EVM互換ZK-Rollup。SCRトークンは配布済み。",
            "tasks": [],
            "end_date": "2024-10-31",
            "logo": "https://assets.coingecko.com/coins/images/25734/small/scroll.png",
            "url": "https://scroll.io/",
            "is_hot": False,
            "added_date": "2024-01-01",
            "source": "curated",
        },
        {
            "id": "zksync-era",
            "name": "zkSync Era (ZK)",
            "symbol": "ZK",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "ended",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "【配布完了 2024年6月】Matter Labs製ZK-Rollup。ZKトークンは配布済み。",
            "tasks": [],
            "end_date": "2024-06-30",
            "logo": "https://assets.coingecko.com/coins/images/38043/small/ZKTokenBlack.png",
            "url": "https://zksync.io/",
            "is_hot": False,
            "added_date": "2024-01-01",
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
