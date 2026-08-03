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
    """手動管理の注目エアドロップシードデータ (定期的に更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "base-token",
            "name": "Base",
            "symbol": "—",
            "category": "Layer2",
            "type": "取引所発行トークン(未確定)",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 2000,
            "description": (
                "CoinbaseのLayer2チェーン。開発責任者Jesse PollakとCEO Brian Armstrongが"
                "「ネットワークトークンを検討中」と公言。JPMorganは時価総額120〜340億ドル規模と試算し、"
                "実現すれば史上最大級のエアドロップになる可能性。Polymarketでは2026年内のトークン化確率69%。"
                "※ 正式発表はまだ無く投機的情報である点に注意。"
            ),
            "tasks": ["Base上でのトランザクション実行", "Base上のDeFi/dAppsの継続利用", "Coinbase Walletでの活動実績を積む"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/45268/small/base.png",
            "url": "https://base.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "metamask-mask",
            "name": "MetaMask",
            "symbol": "MASK",
            "category": "ウォレット/インフラ",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 500,
            "description": (
                "ConsenSys CEOのJoseph Lubinが「予想より早く」MASKトークンが登場すると明言。"
                "MetaMask Rewardsプログラムで貯めたポイントが将来のエアドロップに直結する設計。"
                "Season 1では既に3,000万ドル相当のLINEAトークンを配布済み。"
            ),
            "tasks": ["MetaMask Rewardsプログラムに登録", "ウォレット内スワップでポイント獲得", "Linea上でのアクティビティ実行"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/9151/small/metamask-fox.svg",
            "url": "https://metamask.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket",
            "symbol": "POLY",
            "category": "予測市場/DeFi",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": (
                "世界最大の予測市場プラットフォーム。CMOのMatthew Modabberが「トークンもエアドロップも実施する」"
                "と公式ポッドキャストで明言。配布条件・時期は未公表 (TBA)。2026年の取引高は既に49億ドルを突破。"
            ),
            "tasks": ["Polymarketでの取引実績を積む", "米国版プラットフォームでの継続利用", "公式アナウンスをフォロー"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/34985/small/polymarket.png",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "n1-chain",
            "name": "N1 Chain",
            "symbol": "—",
            "category": "インフラ/Layer1",
            "type": "テストネット",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 200,
            "description": (
                "Solana Ventures出資のレイヤー1ブロックチェーン。2025年5月にテストネット開始、"
                "2026年8月のメインネット移行に向け活動中。トークン配布は未確定だが早期参加者への"
                "将来的エアドロップが期待されている。"
            ),
            "tasks": ["テストネット上のDEXを利用", "コミュニティキャンペーンに参加", "ウォレット接続とアクティビティ記録"],
            "end_date": "未定",
            "logo": "",
            "url": "https://cryptorank.io/drophunting/layer-n-activity775",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "little-pepe-lilpepe",
            "name": "Little Pepe (LILPEPE)",
            "symbol": "LILPEPE",
            "category": "ミームコイン/Layer2",
            "type": "プレセール",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 100,
            "description": (
                "ミームコイン特化の独自Layer2を構築中。ゼロ税制トレーディングとボット対策を特徴とする。"
                "CertiKの監査を完了しプレセールで650万ドル以上を調達。早期購入者向け特典あり。"
            ),
            "tasks": ["公式サイトでプレセールに参加", "コミュニティ(Telegram/X)参加", "ローンチ後のトークンクレーム"],
            "end_date": "未定",
            "logo": "",
            "url": "https://littlepepe.com/",
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
