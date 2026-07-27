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
    2026年7月時点の最新情報 (Web検索) に基づき随時更新。
    """
    today = datetime.utcnow()
    return [
        {
            "id": "grass-season2",
            "name": "Grass Season 2",
            "symbol": "GRASS",
            "category": "DePIN",
            "type": "クレーム受付中",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 80,
            "description": "未使用の帯域幅を共有してAI学習データ収集に貢献するDePINプロジェクト。Season 2のUSDC報酬クレームが2026年7月22日に開始済み(受付は6ヶ月間)。Epoch1〜19の期間のネットワークポイント・稼働ポイントに応じて配分。",
            "tasks": ["Grassアプリをインストールし帯域幅を共有", "公式アプリ内ウォレット(パスキー/メールOTP)を作成", "対象期間のポイント実績を確認しUSDCをクレーム"],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/38254/small/Grass_200.png",
            "url": "https://www.grass.io/",
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
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 1500,
            "description": "評価額$15Bに達した世界最大の予測市場プラットフォーム。CMOが2025年10月にトークン発行とエアドロップ実施を公式に確認済み。供給量の5〜10%がエアドロップに割当予定だが、スナップショット日・配布条件は2026年7月時点で未発表。",
            "tasks": ["USDCで予測市場に参加・取引", "継続的な取引ボリュームを積み上げる", "公式Xとアナウンスを定期チェック"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/44870/small/polymarket.png",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "megaeth-mega",
            "name": "MegaETH (MEGA)",
            "symbol": "MEGA",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 600,
            "description": "$107M超を調達した超高速リアルタイムEVM互換L2。2026年2月9日にメインネットが稼働開始。トークン配布時期は未発表だが、オンチェーン活動の実績が引き続き重要視されている。",
            "tasks": ["MegaETHメインネットへブリッジ", "対応dAppsでのスワップ・取引", "継続的なオンチェーンアクティビティ"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39306/small/megaeth.png",
            "url": "https://megaeth.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-hype-s2",
            "name": "Hyperliquid Season 2",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "ポイント報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "高速オンチェーン永久先物DEX。独自L1上で動作し、Season 1で最大級のエアドロップを実施済み。Season 2のポイントプログラムが継続中で、取引量に応じた追加報酬が期待されている。",
            "tasks": ["Hyperliquid上での先物取引", "流動性提供 (HLP)", "紹介プログラム参加"],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "katana-network",
            "name": "Katana Network (KAT)",
            "symbol": "KAT",
            "category": "DeFi/Layer2",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 200,
            "description": "Polygon Labsが後援するDeFi特化型L2。断片化した流動性を統合し持続的な利回りを提供。総供給100億KATのうち15%をPOLステーカー等へのエアドロップに割当予定。",
            "tasks": ["Katana上でのオンチェーン活動", "対応dAppsの利用", "KAT事前ステーク・クエスト参加"],
            "end_date": (today + timedelta(days=75)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39619/small/katana.png",
            "url": "https://airdrops.io/katana-network/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "xstocks",
            "name": "xStocks (xPoints)",
            "symbol": "xStocks",
            "category": "RWA/トークン化株式",
            "type": "ポイント報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 100,
            "description": "Kraken傘下(旧Backed Finance)によるトークン化株式プラットフォーム(Solana上)。NVDAx・AAPLx等が1:1裏付け。正式なトークン/エアドロップ未発表だが、xPointsプログラムで参加実績を計測中。",
            "tasks": ["xStocks対応DEXでの取引", "xPointsプログラムに参加", "対象銘柄の保有・取引実績を積む"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/39955/small/xstocks.png",
            "url": "https://airdrops.io/xstocks/",
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
