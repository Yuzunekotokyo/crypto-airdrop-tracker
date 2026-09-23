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
    毎日の自動更新実行時にWeb検索で得た最新情報を基に更新する。
    最終リサーチ更新日: 2026-09-23
    """
    today = datetime.utcnow()
    return [
        {
            "id": "base-token",
            "name": "Base (未発表トークン)",
            "symbol": "BASE?",
            "category": "Layer2",
            "type": "レトロアクティブ (噂/未確定)",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "CoinbaseのL2「Base」。CEOブライアン・アームストロング氏がトークン発行の検討を認め、2026年Q2〜Q4のリリース観測も。JPMorganはネットワーク評価額120〜340億ドルと試算し「史上最大級のトークンローンチ」になる可能性。公式な配布計画・スナップショットはまだ未確定。",
            "tasks": ["Base Appをダウンロードしウォレット作成", "ETHをBaseにブリッジ", "Aerodrome/Aaveなど主要DeFiを利用", "Farcaster等ソーシャルdAppsに参加", "Builder Rewardsプログラムへの開発貢献"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/asset_platforms/images/131/small/base-network.png",
            "url": "https://base.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-research-2026-09-23",
        },
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "ウォレット/インフラ",
            "type": "レトロアクティブ (発行確定・詳細未定)",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "ConsenSys CEOジョセフ・ルービン氏がMASKトークンの発行を明言。配布基準・スナップショット日は未公表だが、MetaMask Rewardsプログラム(Linea上のポイント)の実績が有力な判定基準と見られている。",
            "tasks": ["MetaMask内蔵スワップ機能を定期利用", "MetaMask Bridgeで複数チェーン間送金", "Linea上でのアクティビティを重視", "Rewardsプログラムにオプトインしポイント獲得"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/1085/small/metamask-fox.svg",
            "url": "https://metamask.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-research-2026-09-23",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ (発行確定)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "2025年10月にPOLYトークン発行とエアドロップ実施を正式表明。供給量の5〜10%がエアドロップに充当される見込み。米国での正式サービス開始(2026年5月)後、2026年後半のローンチが有力視されている。",
            "tasks": ["Polymarketで実際に予測市場に参加", "取引量・ポジション保有を継続", "米国版ローンチ後のアクティビティも評価対象の可能性"],
            "end_date": "未定 (2026年後半予想)",
            "logo": "https://assets.coingecko.com/markets/images/polymarket.png",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-research-2026-09-23",
        },
        {
            "id": "opensea-sea",
            "name": "OpenSea (SEA)",
            "symbol": "SEA",
            "category": "NFT/マーケットプレイス",
            "type": "レトロアクティブ (発行確定・延期中)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "供給量の50%をコミュニティに配分すると発表済み。当初2026年3月30日ローンチ予定だったが弱気相場を理由に延期、新日程は未発表。初回クレームで全体の約25%を配布予定。",
            "tasks": ["OpenSea/OS2で早期からの取引・出品実績を作る", "報酬プログラムへの参加", "延期中のため継続的な利用実績の蓄積が重要"],
            "end_date": "未定 (延期中)",
            "logo": "https://assets.coingecko.com/coins/images/1071/small/opensea.png",
            "url": "https://opensea.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-research-2026-09-23",
        },
        {
            "id": "hyperliquid-hype-season2",
            "name": "Hyperliquid Season 2 (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "ポイント → 追加配布",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "2024年11月のGenesisで供給量の31%超を配布済み。Season 2として供給量の38.888%が今後の配布用に確保されており、ポイントは1:1でHYPEに転換予定。2026年2月18日開始のHyperEVMは利用者がまだ少なく、狙い目のポイント獲得先。",
            "tasks": ["Perps/Spot取引でポイント獲得", "HYPEをステーキング (1トークンあたり1日8ポイント)", "HyperEVM上のdAppsを利用 (穴場)"],
            "end_date": "未定 (Season2転換イベント未公表)",
            "logo": "https://assets.coingecko.com/coins/images/50882/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-research-2026-09-23",
        },
        {
            "id": "backpack-bp",
            "name": "Backpack (BP)",
            "symbol": "BP",
            "category": "取引所",
            "type": "エアドロップ (配布済み)",
            "status": "ended",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "2026年3月にTGE、Solana上でBPトークンをローンチ済み。供給10億枚のうち25% (約2.5億枚) を即時配布 (うちPointsプログラム参加者に2.4億枚、Mad Lads NFT保有者に1000万枚)。運営・投資家への初期配分なし。新規の獲得機会は終了。",
            "tasks": ["(配布済み) 当時Backpack PointsまたはMad Lads NFT保有者が対象だった"],
            "end_date": "2026-03-23 (配布完了)",
            "logo": "https://assets.coingecko.com/coins/images/38771/small/backpack.jpg",
            "url": "https://backpack.exchange/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated-research-2026-09-23",
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
