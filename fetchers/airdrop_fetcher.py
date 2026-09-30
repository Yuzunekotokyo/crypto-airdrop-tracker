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
    """手動管理の注目エアドロップシードデータ (毎日更新: 2026-09-30時点)"""
    today = datetime.utcnow()
    added = today.strftime("%Y-%m-%d")

    def item(id_, name, symbol, category, type_, status, difficulty, value, desc, tasks, end, url, hot):
        return {
            "id": id_, "name": name, "symbol": symbol, "category": category,
            "type": type_, "status": status, "difficulty": difficulty,
            "estimated_value_usd": value, "description": desc, "tasks": tasks,
            "end_date": end, "logo": "", "url": url, "is_hot": hot,
            "added_date": added, "source": "curated",
        }

    return [
        item("variational-var", "Variational (VAR)", "VAR", "DeFi/デリバティブ", "ポイント→TGE",
             "active", "medium", 1000,
             "オンチェーンデリバティブDEX。2026年Q4にTGE予定、総供給の32%をポイント保有者へGenesis Airdrop(TGE時100%アンロック)。毎週150,000ポイント配布。",
             ["Variationalで取引しポイントを獲得", "利用規約に署名 (1ポイント以上が対象)", "毎週金曜0:00 UTCのポイント配布を確認"],
             "2026-12-31", "https://variational.io/", True),
        item("nado-ink", "Nado (INK)", "INK", "DeFi/DEX", "ポイント→TGE",
             "active", "easy", 500,
             "Kraken系Ink上のDEX。ポイントはTGE時に$INKへ変換予定 (Q3〜Q4見込み、日程未公表)。週$100,000のトレーダー報酬プールあり。",
             ["Nadoで取引", "Rewardsページから週次報酬を請求", "ポイントを積み上げる"],
             "2026-12-31", "https://airdrops.io/ink-chain/", True),
        item("concrete-ct", "Concrete (CT)", "CT", "DeFi/利回り", "ソーシャル+利用",
             "active", "easy", 300,
             "2026年9月にCTトークンとTGE計画を正式発表。Social Bagsキャンペーンでポイント獲得可能。",
             ["SNSフォロー・Discord参加", "投稿シェアでBags獲得", "Concreteのvaultを利用"],
             "2026-12-31", "https://www.bitrue.com/blog/concrete-airdrop-guide", True),
        item("bulk", "BULK", "BULK", "DeFi/パッシブ", "ポイント(AURA)",
             "active", "hard", 600,
             "供給の30%をユーザーへ配布。メインネットは2026-09-05にローンチしSeason1事前入金は終了、現在は招待制。",
             ["招待コードを入手", "メインネットで資産を預ける (AURAは預入期間で加重)", "SOLステーキング 約5.1% APY"],
             "2026-12-31", "https://airdrops.io/blog/best-crypto-airdrops/", False),
        item("backpack", "Backpack", "", "取引所/ウォレット", "ポイント→TGE",
             "active", "medium", 400,
             "TGE計画公表済み(2026-02-09): 25%をコミュニティへ、うち24%がポイント保有者、1%がMad Lads保有者。ポイントはシーズン制。",
             ["Backpackで取引・利用しポイントを獲得", "Mad Lads保有でボーナス"],
             "2026-12-31", "https://backpack.exchange/", False),
        item("hertzflow", "HertzFlow", "", "DeFi/デリバティブ", "ポイント(Merits)",
             "active", "easy", 200,
             "TGEとエアドロップが確定。Season1のMerits(ポイント)でTGE時の配分が決まる。",
             ["HertzFlowを利用しMeritsを獲得"],
             "2026-12-31", "https://airdrops.io/", False),
        item("opensea-sea", "OpenSea (SEA)", "SEA", "NFT/マーケットプレイス", "推測(未確定)",
             "upcoming", "easy", 300,
             "有力な期待銘柄。詳細は未公表のため、OpenSea利用実績を積むのが定石。",
             ["OpenSeaでNFT売買", "継続的な利用実績を作る"],
             "未定", "https://opensea.io/", False),
        item("polymarket-poly", "Polymarket", "", "予測市場", "推測(トークン方向性確認済)",
             "upcoming", "easy", 500,
             "トークン/エアドロップの方向性は公表済みだが、配布条件は未公表。",
             ["Polymarketで継続的に取引", "複数市場に参加"],
             "未定", "https://polymarket.com/", False),
        item("base-token", "Base", "", "Layer2", "推測(未確定)",
             "upcoming", "easy", 500,
             "Coinbase発L2。ネットワークトークンを検討中と公言。確定情報はなし。",
             ["Base上でDeFi/NFT/ブリッジを継続利用"],
             "未定", "https://base.org/", False),
        item("layerzero-zro", "LayerZero (追加配布の可能性)", "ZRO", "インフラ", "推測(未確定)",
             "upcoming", "medium", 200,
             "有力な期待銘柄の一つ。追加ラウンドは未確定のため要注意。",
             ["LayerZero対応ブリッジ/dApps利用"],
             "未定", "https://layerzero.network/", False),
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
