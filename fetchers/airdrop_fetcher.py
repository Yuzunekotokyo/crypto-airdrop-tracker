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
    2026年9月時点で実際に確認されている進行中・確度の高い案件に更新。
    (LayerZero/Scroll/zkSync/EigenLayer/Movement/Hyperliquidなど旧世代の
    エアドロップは既にTGE・配布済みのため、現行の候補にローテーション)
    """
    today = datetime.utcnow()
    return [
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": (
                "予測市場最大手PolymarketがCMO自ら『トークンとエアドロップは実施する』と公式表明。"
                "スナップショット日・供給量は未発表だが、供給の5〜10%が対象になる見込み。"
                "政治・スポーツ・暗号など複数カテゴリでの継続的な取引実績が条件になるとみられる。"
            ),
            "tasks": [
                "Polygon対応ウォレット(MetaMask等)を用意しMATICでガス代を確保",
                "複数カテゴリの予測市場で$100〜$200程度の継続的な取引を行う",
                "同一人物による複数ウォレットのウォッシュトレードは対象外になるため避ける",
                "X(Twitter)アカウントをプロフィールに連携",
            ],
            "end_date": "未定 (スナップショット日未発表)",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "ウォレット",
            "type": "ポイント→エアドロップ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": (
                "Consensys CEOのJoseph LubinがMASKトークンの近日投入を示唆し、"
                "MetaMask公式Xも示唆する投稿を行い注目度が急上昇。"
                "MetaMask Rewardsプログラムで貯まるポイントがLinea関連トークンや"
                "手数料割引、将来のエアドロップに変換される設計。"
            ),
            "tasks": [
                "MetaMaskウォレット内のスワップ機能を利用してポイントを貯める",
                "MetaMask Rewardsプログラムに登録",
                "対応dApps・カードなどのMetaMaskエコシステム機能を利用",
            ],
            "end_date": "未定 (トークン発行時期未確定)",
            "logo": "",
            "url": "https://metamask.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-network-token",
            "name": "Base ネイティブトークン (未確定)",
            "symbol": "—",
            "category": "Layer2",
            "type": "投機的",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": (
                "Coinbase傘下のBaseが独自トークンの検討を明らかにし、2026年Q2〜Q4での"
                "投入可能性が報じられている。ただし正式なトークン発行・エアドロップは"
                "まだ公式発表されておらず、あくまで投機段階の情報である点に注意。"
            ),
            "tasks": [
                "Base メインネット上でのブリッジ・スワップなど定期的な利用実績を積む",
                "Base上のDeFiプロトコルへの流動性提供",
                "Base上でのNFTミント等のオンチェーン活動",
            ],
            "end_date": "未定 (トークン自体が未確定)",
            "logo": "",
            "url": "https://base.org/",
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
