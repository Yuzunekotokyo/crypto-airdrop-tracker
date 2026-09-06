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
    """手動管理の注目エアドロップシードデータ (2026年9月時点の状況に更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "世界最大の予測市場プラットフォーム。CMOがトークン発行とエアドロップ実施を公式に明言済みだが、スナップショット日・配布条件は未発表。米国事業の本格展開完了が前提とされる。",
            "tasks": ["Polymarketで予測マーケットに参加(ベット)", "USDC入金・出金の利用実績を作る", "早期アカウント作成・継続利用"],
            "end_date": "未定",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "giwa-l2",
            "name": "GIWA",
            "symbol": "-",
            "category": "Layer2",
            "type": "テストネット",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "韓国最大手取引所Upbit運営元が手がけるOP Stack採用のEthereum L2。2025年9月のテストネット開始以来、1秒ブロックタイムで既に約1億件のトランザクションを処理。取引所公式支援という後ろ盾の強さが注目材料。",
            "tasks": ["GIWAテストネットへの接続・ブリッジ", "対応dAppsでのスワップ等の操作", "継続的なオンチェーン活動の記録"],
            "end_date": "未定",
            "logo": "",
            "url": "https://www.giwa.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "fuel-network",
            "name": "Fuel Network",
            "symbol": "FUEL",
            "category": "インフラ/モジュラー",
            "type": "テストネット",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "並列実行に特化したモジュラー実行レイヤー。開発者向けタスク(コントラクトデプロイ等)を含む幅広い参加方法があり、テストネット主要プロジェクトとして継続的に名前が挙がる。",
            "tasks": ["Fuelテストネットでのトランザクション実行", "FuelVM対応dAppsの利用", "スマートコントラクトのデプロイ(上級者向け)"],
            "end_date": "未定",
            "logo": "",
            "url": "https://fuel.network/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "zetachain",
            "name": "ZetaChain",
            "symbol": "ZETA",
            "category": "インターオペラビリティ",
            "type": "テストネット/エコシステム参加",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "オムニチェーンのクロスチェーンメッセージング・スマートコントラクトプラットフォーム。複数チェーンをまたぐ資産移動・操作の実績が評価対象になりやすい。",
            "tasks": ["ZetaChain経由でのクロスチェーン送金", "対応dAppsの利用", "コミュニティ参加(Discord/Galxeクエスト)"],
            "end_date": "未定",
            "logo": "",
            "url": "https://www.zetachain.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "zeko-labs",
            "name": "Zeko",
            "symbol": "-",
            "category": "DeFi/L2 (zk)",
            "type": "テストネット",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Mina関連のzkロールアップ。テストネットが活発に稼働しており、スワップ・流動性提供・ブリッジなど日次タスクでポイントを積み上げる方式。",
            "tasks": ["毎日のスワップ操作", "流動性提供(LP)", "ブリッジ操作の実施"],
            "end_date": "未定",
            "logo": "",
            "url": "https://zeko.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "linea-future-airdrop",
            "name": "Linea (Future Airdrop / Ignition)",
            "symbol": "LINEA",
            "category": "Layer2",
            "type": "エコシステム参加",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "2025年9月の本エアドロップ(LXP/LXP-L対象)は既に配布・請求終了済み。ただし総供給の5%(約36億LINEA)がLinea Consortiumによる「将来のエアドロップ」枠として温存されており、Linea Ignition等の継続プログラムでの参加実績が今後の対象になる可能性。",
            "tasks": ["Linea上でのDeFi利用を継続", "Linea Ignition等の公式キャンペーンに参加", "エコシステムdAppsの新規利用"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/52063/small/Linea.png",
            "url": "https://linea.build/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "monad-mon",
            "name": "Monad (MON)",
            "symbol": "MON",
            "category": "Layer1",
            "type": "レトロアクティブ(終了)",
            "status": "ended",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "2025年11月にメインネット・トークン共に稼働開始済み。エアドロップは約76,000ウォレットに総額約1.05億ドル相当のMONを配布し終了。新規の参加余地は無し(参考掲載)。",
            "tasks": [],
            "end_date": "2025-11-24 (終了済み)",
            "logo": "",
            "url": "https://www.monad.xyz/",
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
