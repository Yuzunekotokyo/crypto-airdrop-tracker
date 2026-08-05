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
    """手動管理の注目エアドロップシードデータ (2026年8月時点の最新情報に基づき更新)"""
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
            "estimated_value_usd": 1500,
            "description": "世界最大の分散型予測市場。CMOがネイティブトークンとエアドロップ実施を公式に示唆。ICEによる大型出資も背景に本命視されている。スナップショット日・配布条件は未確定。",
            "tasks": ["Polymarketで予測市場に参加・取引", "多様なマーケットへの分散投資", "ウォレットをXアカウントと連携"],
            "end_date": "未定 (2026年後半見込み)",
            "logo": "https://assets.coingecko.com/coins/images/prediction-market/small/polymarket.png",
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
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 1200,
            "description": "Consensys CEOがトークン発行を認めている最大級の注目案件。Season1のポイントはSeason2に繰越。ウォレットの活動スコアに応じ250〜15,000MASKの配布が見込まれる。",
            "tasks": ["MetaMaskウォレットを日常的に使用", "Linea等Consensysエコシステムを利用", "Season 2ポイントプログラムに参加"],
            "end_date": "未定 (2026年Q3-Q4見込み)",
            "logo": "https://assets.coingecko.com/coins/images/metamask/small/metamask.png",
            "url": "https://metamask.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-token",
            "name": "Base",
            "symbol": "BASE",
            "category": "Layer2",
            "type": "新規トークン",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 900,
            "description": "Coinbase運営のEthereum L2。独自ネットワークトークンの発行を公に検討中と報じられ、早期利用者への還元が期待されている。",
            "tasks": ["BaseチェーンへETHをブリッジ", "Base上のDeFi/dAppsを利用", "継続的なオンチェーン活動"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/base/small/base.png",
            "url": "https://base.org/",
            "is_hot": True,
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
            "estimated_value_usd": 450,
            "description": "クロスチェーンメッセージングプロトコル。初回配布後も大規模なコミュニティ向け将来配分枠が残っており、継続利用者への追加還元が見込まれる。",
            "tasks": ["Stargate経由でブリッジを実行", "複数チェーンでのトランザクション", "LayerZero対応dApps利用"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/28206/small/ftxG9_TJ_400x400.jpeg",
            "url": "https://layerzero.network/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "grass",
            "name": "Grass",
            "symbol": "GRASS",
            "category": "DePIN",
            "type": "ポイント→報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 250,
            "description": "未使用の帯域幅を共有してAI学習データ収集に貢献するDePINプロジェクト。Stage2の報酬請求が受付中 (2027年1月22日締切)。現在はUSDCで報酬が支払われている。",
            "tasks": ["Grass拡張機能/アプリをインストール", "常時接続を維持してアップタイムを稼ぐ", "Rewards Checkerで請求"],
            "end_date": "2027-01-22",
            "logo": "https://assets.coingecko.com/coins/images/grass/small/grass.png",
            "url": "https://www.grass.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "teneo",
            "name": "Teneo",
            "symbol": "TENEO",
            "category": "DePIN/AI",
            "type": "ポイント→TGE",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 180,
            "description": "ブラウザを分散型AIエージェント化するDePINプロジェクト。コミュニティノードを稼働させてポイントを貯め、TGE後にTENEOトークンへ変換予定。",
            "tasks": ["Teneo Community Node拡張機能を導入", "メール認証を完了", "ノードを稼働させポイント獲得"],
            "end_date": "未定 (TGE前)",
            "logo": "https://assets.coingecko.com/coins/images/teneo/small/teneo.png",
            "url": "https://teneo.pro/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "eigenlayer-eigen",
            "name": "EigenLayer (EIGEN)",
            "symbol": "EIGEN",
            "category": "インフラ",
            "type": "リステーキング",
            "status": "active",
            "difficulty": "hard",
            "estimated_value_usd": 700,
            "description": "Ethereumのリステーキングプロトコル。ETHをステーキングし追加報酬を獲得。継続シーズンで追加配布が続く。",
            "tasks": ["ETHをリステーキング", "LST (stETH等) をデポジット", "AVSへの参加"],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/33751/small/eigen.png",
            "url": "https://eigenlayer.xyz/",
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
