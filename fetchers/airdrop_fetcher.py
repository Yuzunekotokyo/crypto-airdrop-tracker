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
    """手動管理の注目エアドロップシードデータ (定期的にWeb検索で最新化)。
    2026年8月時点の主要な未確定/進行中エアドロップ案件を反映。"""
    today = datetime.utcnow()
    return [
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "ウォレット",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": (
                "ConsenSysのJoseph Lubin氏が2025年9月に$MASKトークンを正式発表。"
                "利用者3000万人超で史上最大級の配布になる可能性。一部で配布開始の報道があるが、"
                "公式な配布条件・スケジュールは未確定 (最有力視される時期は2026年Q3〜Q4)。"
            ),
            "tasks": [
                "2026年3月1日以前からMetaMaskをアクティブ利用",
                "スワップ/ブリッジの実行",
                "DeFiプロトコルとの連携",
                "ETH/ERC-20トークンの保有",
            ],
            "end_date": "未定",
            "logo": "",
            "url": "https://metamask.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
            "caution": "非公式のクレーム/請求サイトへの接続やシードフレーズ入力は絶対に行わないこと。公式サイト・公式X以外の情報は要注意。",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "ポイント制",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": (
                "PolymarketのCMOが2025年10月にトークン発行とエアドロップ実施を公式に確認。"
                "スナップショット日程・配分方式は未発表だが、コミュニティ予想は2026年後半。"
            ),
            "tasks": [
                "継続的な取引 (一括の大口取引より週次の少額継続が有利とされる)",
                "複数カテゴリ (政治/スポーツ/暗号) の市場で取引を分散",
                "Xアカウントの連携",
                "polymarket.com/rewardsで指値注文による流動性提供",
            ],
            "end_date": "未定",
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
            "category": "NFTマーケットプレイス",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": (
                "OpenSea 2.0のネイティブトークン。コミュニティ配分50%を公約。"
                "当初2026年Q1予定だったTGEはCEO Devin Finzer氏が2026年3月に延期を認め、新日程は未定。"
            ),
            "tasks": [
                "OpenSea上での取引・Treasure Chest (XP) の獲得",
                "過去の利用実績 (レベル・XPが配分に影響)",
                "KYC不要 (米国ユーザーも対象)",
            ],
            "end_date": "未定",
            "logo": "",
            "url": "https://opensea.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-token",
            "name": "Base ネイティブトークン (未発表)",
            "symbol": "?",
            "category": "Layer2",
            "type": "噂・検討段階",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": (
                "CoinbaseのL2「Base」。2025年9月にJesse Pollak氏がトークン発行の検討を示唆し、"
                "従来の「トークン発行予定なし」から方針転換。2026年Q2〜Q4に準備が進む可能性。"
                "公式な発行決定・配布条件はまだ発表されていない。"
            ),
            "tasks": [
                "Baseメインネットでの継続利用 (スワップ/ブリッジ)",
                "DeFiプールへの流動性提供",
                "NFTの作成・収集",
                "Baseアプリ内でのUSDC保有・投稿活動",
            ],
            "end_date": "未定",
            "logo": "",
            "url": "https://base.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "backpack-bp",
            "name": "Backpack Exchange",
            "symbol": "BP",
            "category": "取引所",
            "type": "ポイント制 (Season 4進行中)",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": (
                "Solana系ウォレット/取引所Backpack。トークン供給の25%をコミュニティに配分予定"
                "(24%がポイント保有者、1%がMad Lads NFT保有者向け)。Season 4は2025年11月20日開始で現在も進行中。"
            ),
            "tasks": [
                "Backpack Exchangeでの取引",
                "Backpack Wallet経由でのSolana DeFi活動",
                "Backpack Payでの送金",
                "アクティブトレーダーの紹介",
            ],
            "end_date": "未定 (Season 4進行中)",
            "logo": "",
            "url": "https://backpack.exchange/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "variational-var",
            "name": "Variational (VAR)",
            "symbol": "VAR",
            "category": "DeFi/デリバティブ",
            "type": "ポイント制",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": (
                "Coinbase・Dragonfly Capital・Bain Capital Crypto等が出資するP2P型デリバティブ取引プロトコル。"
                "$VARトークンの詳細とコミュニティ配分計画を公表済み。"
            ),
            "tasks": ["Variational上でのパーペチュアル/オプション取引", "流動性提供", "コミュニティ活動への参加"],
            "end_date": "未定",
            "logo": "",
            "url": "https://variational.io/",
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
