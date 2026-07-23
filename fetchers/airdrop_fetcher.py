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
    """手動管理の注目エアドロップシードデータ (2026年7月の最新情報に基づき更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "orbinum-network-orb",
            "name": "Orbinum Network (ORB)",
            "symbol": "ORB",
            "category": "プライバシー/インフラ",
            "type": "テストネットポイント",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 350,
            "description": "秘匿トランザクション対応のプライバシーチェーン。Season 1「Genesis Community」が2026年3月13日開始、2,000万ORBの報酬プールをクエスト・週次ストリーク・紹介・テストネット操作(シールド送金等)のポイントで山分け。無料テストネットトークンのみで参加可能。",
            "tasks": ["Orbinum Hubでウォレット/X/Discord/Telegramを連携", "Quest Board (Social/Weekly/Refer/Learn) を完了", "テストネットでシールド送金・非シールド化・選択的開示を実行", "紹介プログラムでORBクレジット獲得"],
            "end_date": "未定 (メインネット稼働14日前にスナップショット)",
            "logo": "",
            "url": "https://app.orbinum.network/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "spicenet",
            "name": "Spicenet",
            "symbol": "",
            "category": "DeFi/インフラ",
            "type": "ポイントファーミング",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Celestia上に構築されたソブリンapp-rollup。DeFiアプリ向け統合流動性レイヤーを提供。Spice Portalが稼働中でSpice Pointsを付与中だが、正式なトークン/エアドロップはまだ未発表。Hack VC・Magnus Capitalなどから3.4M資金調達済み。",
            "tasks": ["Spicenet PortalでウォレットとXアカウントを連携", "公式Xをフォロー・ソーシャルクエスト完了", "「Create Spicy Content」でSNS投稿を提出", "友人紹介 (1,000pt到達で200ptボーナス)"],
            "end_date": "未定 (トークン化未確定)",
            "logo": "",
            "url": "https://spicenet.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場/DeFi",
            "type": "レトロアクティブ (発表済・日程未定)",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "世界最大級の予測市場プラットフォーム。CMOのMatthew Modabberが2025年10月にトークン発行とエアドロップ実施を公式確認済み。2026年5月に米国事業を本格展開したが、配布時期・対象条件はまだ未公開。取引量が大きいほど有利になる可能性が高い。",
            "tasks": ["Polymarketで実際に予測市場に参加・取引", "継続的な取引履歴を積む", "公式アナウンスを注視 (配布条件は未公開)"],
            "end_date": "未定 (トークン発行日未発表)",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "fogo-flames-s2",
            "name": "Fogo (FOGO) — Flames Season 2",
            "symbol": "FOGO",
            "category": "Layer1/トレーディング",
            "type": "シーズンポイント",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 150,
            "description": "SVM互換の高速トレーディング特化Layer1。Season 1クレーム(平均6,700FOGO/ウォレット)は2026年4月15日で終了済みだが、2億FOGOを配分するFlames Season 2が進行中。週次(月〜日UTC)でFlamesを稼ぎ毎週水曜にリーダーボード反映。",
            "tasks": ["Flames Season 2ポータルに参加", "対象dApp上で週次アクティビティを実施", "リーダーボード上位を維持"],
            "end_date": "シーズン2進行中 (終了日未定)",
            "logo": "",
            "url": "https://fogo.io/",
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
