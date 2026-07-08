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
    2026年7月時点のWeb調査に基づき、実際にまだ稼働中/開始前の案件のみを掲載。
    (LayerZero・Scroll・zkSync・EigenLayer・旧Hyperliquid Season1・Movement等は
    既にTGE/配布が完了済みのため一覧から除外)
    """
    today = datetime.utcnow()
    return [
        {
            "id": "metamask-mask",
            "name": "MetaMask Rewards (MASK)",
            "symbol": "MASK",
            "category": "ウォレット",
            "type": "ポイント/リワード",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "ConsenSysが正式発表した$MASKトークン。MetaMaskアプリ内のRewardsプログラムでスワップ・ブリッジ・パーペチュアル取引・ステーキングのポイントが将来のエアドロップ配分に直結。Season1ではLINEAトークンで$30M以上配布済み。",
            "tasks": ["MetaMaskモバイル版(v7.57+)でRewardsタブに参加", "アプリ内でスワップ/ブリッジを実行", "パーペチュアル取引・ステーキングでポイント獲得", "友達紹介プログラムに参加"],
            "end_date": "2026年Q3-Q4予定(未定)",
            "logo": "",
            "url": "https://metamask.io/rewards",
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
            "estimated_value_usd": 0,
            "description": "CMOが正式にトークン発行とエアドロップ実施を確認済みの予測市場最大手。供給の5〜10%をアクティブトレーダー・コミュニティに配分予定。CFTC規制承認待ちのため時期は未定。",
            "tasks": ["政治・スポーツ・経済など複数カテゴリで継続的に取引", "設定画面でX(旧Twitter)アカウントを連携", "指値注文でRewardsプログラムに参加", "複数ウォレットでのSybilファーミングは避ける"],
            "end_date": "未定(2026年後半見込み)",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-hype-s2",
            "name": "Hyperliquid Season 2 (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "ポイント/リワード",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "高速オンチェーン永久先物DEX。HYPE供給の約38.9%が「将来の配分」として留保されており、Season2ポイントプログラムが2025年12月より稼働中。スナップショット時期は非公開。",
            "tasks": ["Hyperliquid上での先物取引量を積み上げる", "HYPEのステーキング", "HyperEVM上でのDeFi利用・流動性提供"],
            "end_date": "未定(スナップショット非公開)",
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "opensea-sea",
            "name": "OpenSea (SEA)",
            "symbol": "SEA",
            "category": "NFTマーケットプレイス",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "供給の50%をコミュニティに配分する大型トークン。過去のNFT取引履歴を持つユーザーとRewards(XP/Treasure Chest)参加者が対象。Q1 2026launch予定だったが遅延の可能性あり。",
            "tasks": ["OpenSea Rewardsページでウォレット接続しオンボーディング完了", "Treasure Chestを開封しXPを貯める", "Weekly Voyagesに参加", "過去のSeaportプロトコル利用実績があれば有利"],
            "end_date": "Q1 2026予定(遅延の可能性あり)",
            "logo": "",
            "url": "https://opensea.io/rewards",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "kraken-ink",
            "name": "Kraken Ink (INK)",
            "symbol": "INK",
            "category": "Layer2/取引所",
            "type": "ポイント/リワード",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "KrakenのOP Stack系L2「Ink」のユーティリティトークン。Kraken Drops経由での配布が確定済み。Kraken Proでの取引が唯一確認済みのポイント獲得方法。TGEは2026年Q3〜Q4予想。",
            "tasks": ["Kraken Proで取引してInk Pointsを獲得", "Nado/Tydro等のInk上DeFiを利用", ".inkドメインを登録", "Guild.xyz/Layer3クエストに参加"],
            "end_date": "2026年Q3-Q4予定(未定)",
            "logo": "",
            "url": "https://www.kraken.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-token",
            "name": "Base (未発表トークン)",
            "symbol": "—",
            "category": "Layer2",
            "type": "潜在的エアドロップ",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "Coinbase系L2 Base。ネットワークトークン発行の検討を表明済みだが未確定(2026年Q2〜Q4の可能性)。Base App利用・オンチェーン活動実績が将来配布の判断材料になる見込み。",
            "tasks": ["Base App(旧Coinbase Wallet)をダウンロードしFarcaster/Xを連携", "Aerodrome等でスワップ・流動性提供", "coinbase.idユーザー名を取得", "数ヶ月にわたる継続的なオンチェーン活動"],
            "end_date": "未確定(トークン発行自体が未確定)",
            "logo": "",
            "url": "https://www.base.org/",
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
