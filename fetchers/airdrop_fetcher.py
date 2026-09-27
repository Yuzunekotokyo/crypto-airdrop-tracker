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
    """手動管理の注目エアドロップシードデータ (2026年9月時点の最新情報で更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "variational-var",
            "name": "Variational (VAR)",
            "symbol": "VAR",
            "category": "デリバティブ/DeFi",
            "type": "ジェネシスエアドロップ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 600,
            "description": "オンチェーン・デリバティブ取引プロトコル。供給量の32%という大規模比率をジェネシスエアドロップに割当てると発表し話題に。Q4 2026にTGE予定。",
            "tasks": ["Genesisキャンペーンに参加してポイント獲得", "デリバティブ取引を実行", "紹介プログラムに参加"],
            "end_date": "2026年Q4 (TGE予定)",
            "logo": "https://assets.coingecko.com/coins/images/39999/small/variational.png",
            "url": "https://variational.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "concrete-ct",
            "name": "Concrete (CT)",
            "symbol": "CT",
            "category": "インフラ/DeFi",
            "type": "ポイント→トークン変換",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 400,
            "description": "2026年9月、ネイティブトークンCTのTGE計画を正式発表。X/Discordでの社会活動やガバナンス参加で貯めた「Bags」がConcrete Pointsに変換されエアドロップ配分の基準となる。",
            "tasks": ["X/Discordでの社会的タスクでBagsを獲得", "ガバナンス・テストネットに参加", "ストリーク継続でマルチプライヤー獲得"],
            "end_date": (today + timedelta(days=75)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/40501/small/concrete.png",
            "url": "https://concrete.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "saturn-strn",
            "name": "Saturn Credit (STRN)",
            "symbol": "STRN",
            "category": "レンディング/クレジット",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 350,
            "description": "オンチェーン信用プロトコル。2026年9月25日、STRNトークンのTGEをQ4 2026に実施すると発表。Season 2は供給量の最大5%を配分予定。",
            "tasks": ["Saturnでポジションを維持しSeason 2ポイントを蓄積", "スナップショットまで条件を満たし続ける", "追加アクションは現時点で不要"],
            "end_date": "2026年Q4 (TGE予定)",
            "logo": "https://assets.coingecko.com/coins/images/40602/small/saturn.png",
            "url": "https://saturn.credit/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-hype",
            "name": "Hyperliquid (HYPE) Season 2",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "取引所トークン",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1000,
            "description": "高速オンチェーン永久先物DEX。Season 2が供給量38.888%のプールで進行中。2026年2月開始のHyperEVM層はまだ参加者が少なくポイント効率が高い狙い目。スナップショット日未発表。",
            "tasks": ["Hyperliquidで先物/スポット取引を実行", "HYPEをステーキング (1トークンあたり1日8ポイント)", "HyperEVM上のdAppsを利用", "$10k取引達成後リファラルコードを発行"],
            "end_date": "未定 (スナップショット未発表)",
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "doma-protocol-d3",
            "name": "Doma Protocol (D3)",
            "symbol": "D3",
            "category": "RWA/DomainFi",
            "type": "ポイントキャンペーン",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 250,
            "description": "ドメイン資産をオンチェーン化するDomainFiプロトコル。Frontierプログラムは新規登録だけで無料10,000ポイントを付与する無料参入ルートあり。5段階のティア制 (Landlord〜Baron)。",
            "tasks": ["Frontierに無料登録 (デポジット不要で10,000pt)", "ドメインをミント・トレード", "リファラルリンクで追加ポイント獲得"],
            "end_date": "未定 (Season 1進行中)",
            "logo": "https://assets.coingecko.com/coins/images/40711/small/doma.png",
            "url": "https://doma.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場/DeFi",
            "type": "トークン未上場",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 500,
            "description": "世界最大級の予測市場プラットフォーム。CMOが「トークンとエアドロップは確実に実施する」と明言済みだが、スナップショット日・供給量は未発表。取引量の多様性・継続性が有利と噂される。",
            "tasks": ["予測市場で取引を継続", "複数カテゴリの市場に参加", "Xアカウントをリンク", "勝ち分を再投資"],
            "end_date": "未定 (2026年後半に期待)",
            "logo": "https://assets.coingecko.com/coins/images/39812/small/polymarket.png",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "abstract-chain",
            "name": "Abstract",
            "symbol": "—",
            "category": "Layer2/コンシューマー",
            "type": "XPポイント",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 200,
            "description": "Pudgy Penguins運営元が手がけるコンシューマー向けL2。XPポイント制度は稼働中だがトークン化・請求方法は未確定 (2026年8月時点)。PENGU/Frame関連ユーザーが有利との噂。",
            "tasks": ["Abstract上のdAppsを利用してXP獲得", "参加バッジを取得", "PENGU保有・Frame利用歴があれば有利の可能性"],
            "end_date": "未定 (エアドロップ未確定)",
            "logo": "https://assets.coingecko.com/coins/images/40877/small/abstract.png",
            "url": "https://abs.xyz/",
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
