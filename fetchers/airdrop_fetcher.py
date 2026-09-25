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
    """手動管理の注目エアドロップシードデータ (2026年9月時点の最新情報に更新)"""
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
            "estimated_value_usd": 0,
            "description": "米大統領選で一躍有名になった予測市場プラットフォーム。CMOがトークン発行とエアドロップ実施を公式に認めており、2026年後半のトークン化が濃厚。取引量よりも継続的な利用実績が重視される見込み。",
            "tasks": [
                "政治・スポーツ・経済など複数カテゴリで継続的に取引する",
                "X(Twitter)アカウントをプロフィールにリンク",
                "指値注文で流動性提供プログラムに参加",
                "複数ウォレットの併用は避ける(Sybil対策で除外リスク)",
            ],
            "end_date": "未定(2026年後半トークン化予定)",
            "logo": "https://assets.coingecko.com/markets/images/polymarket.png",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "concrete-ct",
            "name": "Concrete (CT)",
            "symbol": "CT",
            "category": "DeFi",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "Blueprint Financeが開発する自動DeFiボールト(TVL約$845M)。Polychain Capital・YZi Labs・VanEckなどから約$17M調達。2026年9月に発行上限10億枚のガバナンストークンCTのTGEを発表し、ソーシャルポイント「Bags」が将来配布の対象に。",
            "tasks": [
                "X・DiscordでのソーシャルポイントキャンペーンでBagsを貯める",
                "Concrete Vaultへ資産をデポジットして利回りを獲得",
                "Binance Walletなど連携先経由での利用も対象",
            ],
            "end_date": "TGE時期未定(2026年Q3〜Q4予定)",
            "logo": "",
            "url": "https://concrete.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-network-token",
            "name": "Base ネットワークトークン",
            "symbol": "—",
            "category": "Layer2",
            "type": "新規トークン(検討中)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Coinbase発のEthereum L2「Base」。開発者Jesse Pollak氏とCoinbase CEOが独自ネットワークトークンの検討を公式に認めた。詳細・時期は未確定だが、早期からのBase上での利用実績が有利に働くとみられる。",
            "tasks": [
                "BaseへETHをブリッジ",
                "Base上のDeFi/dAppsを継続的に利用",
                "公式発表(X/Base公式ブログ)を定期チェック",
            ],
            "end_date": "未定(早ければ2026年内に詳細発表の可能性)",
            "logo": "https://assets.coingecko.com/asset_platforms/images/131/small/base-network.png",
            "url": "https://base.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "yakkamon-flower",
            "name": "Yakkamon (FLOWER / Monster NFT)",
            "symbol": "FLOWER",
            "category": "GameFi/NFT",
            "type": "ポイント制エアドロップ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 150,
            "description": "Roninチェーン上のクリーチャー収集ゲーム。9/14〜18のジェネシスNFT無料ミントは終了したが、Season 0ポイントランキング上位5,000名にMonster NFT(上位1,000名はレジェンダリー)を配布する施策が進行中。",
            "tasks": [
                "Yakkamonでアカウント登録・ウォレット接続",
                "Season 0の各種クエストをこなしポイント(ランク)を稼ぐ",
                "ランキング上位5,000名を目指す",
            ],
            "end_date": "Season 0終了時(早期アクセス開始時に配布)",
            "logo": "",
            "url": "https://yakkamon.com/",
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
