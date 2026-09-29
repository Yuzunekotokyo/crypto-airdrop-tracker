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
            "id": "ink-kraken",
            "name": "Ink (Kraken L2 / INK)",
            "symbol": "INK",
            "category": "Layer2",
            "type": "ポイント",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 500,
            "description": "Kraken公式のEthereum L2。KrakenがKraken Dropsでの配布を公式に確認済み。TGE日・配分式は未発表。",
            "tasks": ['Ink上でDeFi/ブリッジ利用（ポイント獲得）', 'Kraken Pro取引もポイント対象', 'NadoやTydroの利用'],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://inkonchain.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "czr-genesis",
            "name": "CZR Genesis Airdrop",
            "symbol": "CZR",
            "category": "新規上場",
            "type": "キャンペーン",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 200,
            "description": "最大500万CZRを配布。最終スナップショット9/30 23:59 UTC、TGEは10/1予定。締切間近。",
            "tasks": ['キャンペーンに登録', '指定タスクを完了', 'スナップショットまでに条件維持'],
            "end_date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://usethebitcoin.com/airdrop/czr/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket-token",
            "name": "Polymarket (トークン)",
            "symbol": "",
            "category": "予測市場",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 1000,
            "description": "Polymarketがトークン発行とエアドロップを公式示唆。TGE日・配分ルールは未発表。",
            "tasks": ['Polymarketで継続的に取引', '複数の市場で流動性提供', 'アクティビティを月次で維持'],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
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
            "category": "NFT",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "SEAトークンは市況を理由に延期（当初3/30）。新しい日程は未発表。",
            "tasks": ['OpenSeaでNFT売買', 'OpenSea上で継続的に活動'],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://opensea.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-token",
            "name": "Base (トークン)",
            "symbol": "",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 700,
            "description": "Coinbase L2。トークン検討中との報道。公式確定なし・要注意。",
            "tasks": ['Base上でDeFi/NFT利用', '定期的なオンチェーン活動'],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://base.org/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "layerzero-zro",
            "name": "LayerZero (ZRO)",
            "symbol": "ZRO",
            "category": "インフラ",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 300,
            "description": "クロスチェーンメッセージング。追加プログラムの可能性を継続監視。",
            "tasks": ['Stargate経由でブリッジ', '複数チェーンでTX実行'],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://layerzero.network/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "nado-rewards",
            "name": "Nado 週次報酬",
            "symbol": "",
            "category": "DeFi/DEX",
            "type": "トレード報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 100,
            "description": "Nadoは週10万ドルのトレーダー報酬プールを実施。Ink関連ポイント対象の可能性。",
            "tasks": ['Nadoで取引', 'Rewardsページから毎週請求'],
            "end_date": (today + timedelta(days=7)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://www.nado.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "ekiden",
            "name": "Ekiden",
            "symbol": "",
            "category": "DeFi/DEX",
            "type": "ポイント",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "メインネット公開に合わせたリワード確定。取引でポイント獲得。",
            "tasks": ['メインネットで取引', 'ポイントを積み上げ'],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://ekiden.fi/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "variational-var",
            "name": "Variational (VAR)",
            "symbol": "VAR",
            "category": "DeFi/DEX",
            "type": "ポイント",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 600,
            "description": "TGEは2026年Q4予定、ジェネシス配分32%。",
            "tasks": ['Variationalで取引', 'ポイントを獲得'],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://variational.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "concrete-ct",
            "name": "Concrete (CT)",
            "symbol": "CT",
            "category": "DeFi",
            "type": "ポイント",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "9月にCTトークンとTGE計画を発表。",
            "tasks": ['Concreteにデポジット', 'ポイント獲得'],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://concrete.xyz/",
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
