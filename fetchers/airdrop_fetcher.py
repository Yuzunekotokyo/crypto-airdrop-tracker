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
            "id": "hot-protocol-hot",
            "name": "HOT Protocol",
            "symbol": "HOT",
            "category": "インフラ/ウォレット",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "100以上のチェーンを横断操作できるチェーン抽象化MPCウォレット。Telegramミニアプリ/専用アプリでのマイニングでポイントを積み上げ中。TGEは2026年Q3を見込む(未確定)。",
            "tasks": ["HOTウォレットアプリ or Telegramミニアプリでマイニング開始", "毎日のマイニングストリークを継続", "インフラ/ブースターのアップグレード"],
            "end_date": "2026年Q3予定(未確定)",
            "logo": "",
            "url": "https://blog.mexc.com/news/hot-protocol-airdrop-2026-how-to-participate-eligibility-tge-details/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "aster-dex-aster",
            "name": "Aster (ASTER)",
            "symbol": "ASTER",
            "category": "DeFi/DEX",
            "type": "ポイントプログラム",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "Binance系永久先物DEX。Rhポイントを複数シーズンにわたり配布中。USDF/asBNBなどプラットフォーム資産の利用でボーナス倍率。",
            "tasks": ["ウォレット接続 (ETH/BNB Chain/Arbitrum/Solana)", "USDT/ETHを入金しUSDFへオートミント", "Aster Proで取引しRhポイントを獲得", "紹介コード利用で倍率アップ"],
            "end_date": "継続中(複数シーズン制)",
            "logo": "",
            "url": "https://airdropalert.com/airdrops/aster-dex-stage-6/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ(未確定)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "世界最大の予測市場プラットフォーム。CMOがトークン/エアドロップの存在を公言し、2026年2月にPOLY商標を出願済み。配布基準は未公表だが取引量・取引の多様性・継続性が有力視される。",
            "tasks": ["Polymarketで実際にマーケットに参加", "複数カテゴリのマーケットで取引", "継続的な取引実績を積む", "Xアカウントをリンク"],
            "end_date": "2026年後半予定(未確定)",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-l2",
            "name": "Base",
            "symbol": "—",
            "category": "Layer2",
            "type": "投機的(未確定)",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "Coinbase運営のEthereum L2。独自トークン発行の噂が継続的に浮上しているが公式発表はまだ無い。オンチェーン利用実績が将来的な資格に有利との見方。",
            "tasks": ["Base上でのブリッジ・スワップ", "Base上のdApps利用", "継続的なオンチェーン活動"],
            "end_date": "未定",
            "logo": "",
            "url": "https://base.org/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "pengu-clash",
            "name": "Pengu Clash",
            "symbol": "PENGU",
            "category": "ゲーム/NFT",
            "type": "SBT/将来のトークン化(未確定)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Pudgy PenguinsチームによるTON/Abstract Chain上のスキルベース対戦ゲーム。SBT配布の主要フェーズは終了済みだが、将来的な$PENGUトークン化が噂されている。",
            "tasks": ["@PenguClashをXでフォロー", "Telegramチャンネルに参加", "ゲーム内チェストのアップグレード"],
            "end_date": "SBTフェーズ終了、トークン化時期未定",
            "logo": "",
            "url": "https://airdrops.io/pengu-clash/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "monad-mon",
            "name": "Monad (MON)",
            "symbol": "MON",
            "category": "Layer1",
            "type": "レトロアクティブ(配布終了)",
            "status": "ended",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "高速並列EVM互換L1。2025年10月にクレーム開始、28.9万ウォレットに配布済み。2025年11月24日にメインネット稼働。新規の獲得機会は無し(参考情報)。",
            "tasks": [],
            "end_date": "配布終了(2025年10月14日クレーム完了)",
            "logo": "",
            "url": "https://airdrops.io/monad/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "lighter-lit",
            "name": "Lighter (LIT)",
            "symbol": "LIT",
            "category": "DeFi/DEX",
            "type": "ポイントプログラム(配布終了)",
            "status": "ended",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "パーペチュアルDEX。2025年12月31日のTGEで供給の25%(2.5億LIT)をポイント2シーズン参加者に配布済み。Season3は2026年8月時点で未発表(参考情報)。",
            "tasks": [],
            "end_date": "配布終了(2025年12月31日TGE)",
            "logo": "",
            "url": "https://airdrops.io/lighter/",
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
