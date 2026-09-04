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
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場/DeFi",
            "type": "レトロアクティブ (未確定)",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 1500,
            "description": "世界最大級の分散型予測市場プラットフォーム。CMOがトークン発行とエアドロップ実施を公式に表明済みだが、配布時期・条件は未確定。米国向けプラットフォーム再稼働後、2026年後半のローンチが有力視されている。",
            "tasks": ["Polymarketでの継続的な予測市場取引", "多様なマーケットへの分散投資", "獲得した賞金の再投資", "公式SNSアカウントとの連携"],
            "end_date": "未定 (2026年後半見込み)",
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
            "category": "ウォレット/インフラ",
            "type": "レトロアクティブ (未確定)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 1000,
            "description": "Consensys CEOがMASKトークン発行を示唆したが、MetaMask公式は現時点で正式なトークン計画を発表していない。非公式の請求サイトやチェッカーは詐欺の可能性が高いため要注意。MetaMask Rewards (スワップ/ブリッジ/Perps取引でポイント獲得) が将来の配布基準になる可能性が高い。",
            "tasks": ["MetaMask Rewardsでポイント獲得 (スワップ/ブリッジ/Perps)", "MetaMaskウォレットの継続利用", "公式アカウント以外の請求案内には注意"],
            "end_date": "未定 (公式未発表・詐欺に注意)",
            "logo": "",
            "url": "https://metamask.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-app-rewards",
            "name": "Base App / Baseエコシステム",
            "symbol": "—",
            "category": "Layer2/インフラ",
            "type": "レトロアクティブ (未確定)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 500,
            "description": "Coinbase発のEthereum L2「Base」。独自トークンやBase Appでの報酬プログラムが2026年の有力エアドロップ候補として市場から注目されているが、公式発表はまだない。",
            "tasks": ["Base App / Baseチェーン上でのオンチェーン活動", "Base上のdApps利用", "公式アナウンスの継続確認"],
            "end_date": "未定",
            "logo": "",
            "url": "https://base.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "opensea-sea",
            "name": "OpenSea (SEA)",
            "symbol": "SEA",
            "category": "NFT/マーケットプレイス",
            "type": "レトロアクティブ (未確定)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "NFTマーケットプレイス最大手。SEAトークンの発行自体は既定路線とされているが、正式なローンチ日程は未発表。OS2新プラットフォームでの利用実績が対象になる可能性。",
            "tasks": ["OpenSeaでのNFT売買", "OS2新プラットフォームの利用", "公式アナウンスの継続確認"],
            "end_date": "未定",
            "logo": "",
            "url": "https://opensea.io/",
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
            "estimated_value_usd": 600,
            "description": "Ethereumのリステーキングプロトコル。ETHをリステーキングし追加報酬を獲得できる継続プログラム。",
            "tasks": ["ETHをリステーキング", "LST (stETH等) をデポジット", "AVSへの参加"],
            "end_date": "未定 (継続中)",
            "logo": "https://assets.coingecko.com/coins/images/33751/small/eigen.png",
            "url": "https://eigenlayer.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "perp-dex-points-2026",
            "name": "新興Perps DEXポイントプログラム (Lighter/EdgeX/Aster/Paradex)",
            "symbol": "—",
            "category": "DeFi/Perps DEX",
            "type": "ポイント→トークン (未確定)",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 300,
            "description": "無期限先物DEX各社がポイントプログラムを運営中。段階は各社異なるが、2026年中の追加トークン配布が期待されている。詳細な配布条件は各プロジェクトの発表待ち。",
            "tasks": ["各DEXでのPerps取引によるポイント獲得", "流動性提供", "リファラルプログラム参加"],
            "end_date": "未定 (継続中)",
            "logo": "",
            "url": "https://airdrops.io/",
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
