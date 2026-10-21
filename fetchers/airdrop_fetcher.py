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
    """手動管理の注目エアドロップシードデータ (毎日の更新で見直す)。最終見直し: 2026-10-21"""
    def item(**kw):
        base = {"symbol": "", "tasks": [], "logo": "", "is_hot": False,
                "added_date": "2026-10-21", "source": "curated", "estimated_value_usd": 0}
        base.update(kw)
        return base

    return [
        item(
            id="polymarket-poly", name="Polymarket (POLY)", symbol="POLY",
            category="予測市場", type="ポイント/取引量", status="upcoming", difficulty="medium",
            estimated_value_usd=1000, is_hot=True,
            description="CMOがトークンとエアドロップを公式に認めた最大級の本命。米国再ローンチ後に実施見込みで、配布条件・日程は未公開。",
            tasks=["実際の取引を継続 (取引量・市場数・期間が評価されると予想)", "複数カテゴリの市場に参加", "公式発表を随時確認 (スナップショット未告知)"],
            end_date="未定", url="https://polymarket.com/",
        ),
        item(
            id="ekiden-points", name="Ekiden (ポイント)", symbol="",
            category="DeFi/DEX", type="ポイント", status="upcoming", difficulty="medium",
            estimated_value_usd=300,
            description="オーダーブック型デリバティブDEX。メインネットと連動したポイントプログラムを予告。早期アクセスはテストネット上位トレーダーへの招待制。シード調達$2M。",
            tasks=["テストネットで取引・XP獲得", "紹介プログラム参加", "メインネット開始後のポイント獲得"],
            end_date="未定", url="https://ekiden.fi/",
        ),
        item(
            id="pharos-pros", name="Pharos (PROS)", symbol="PROS",
            category="Layer1", type="クレーム期限", status="active", difficulty="easy",
            estimated_value_usd=200,
            description="エアドロ受取期限が2026-10-25 (180日窓)。対象: テストネット参加者・Stake Before the Stake・Discordロール・OKX Walletキャンペーン。未請求分は財団へ返却。偽サイト(claim.pharos.sbs等)に注意。",
            tasks=["claim.pharos.xyz で資格を確認", "期限(10/25)までに請求"],
            end_date="2026-10-25", url="https://claim.pharos.xyz/",
        ),
        item(
            id="standx-dusd", name="StandX (DUSD)", symbol="DUSD",
            category="DeFi/DEX", type="クレーム", status="upcoming", difficulty="easy",
            estimated_value_usd=100,
            description="StandXはTGE中止・事業終了を発表。代わりにロックアップ無しのDUSDを配布。資格チェッカー 10/26、請求 11/1〜12/31。ポジション自動決済 2027-01-15、出金期限 2027-01-31。",
            tasks=["10/26以降に公式サイトで資格確認", "StandXで使ったウォレットから請求 (BNB Chain/Solana)", "資金を2027-01-31までに引き出す"],
            end_date="2026-12-31", url="https://standx.com/",
        ),
        item(
            id="opensea-sea", name="OpenSea (SEA)", symbol="SEA",
            category="NFT", type="レトロアクティブ", status="upcoming", difficulty="easy",
            estimated_value_usd=500,
            description="SEAトークン計画は供給の50%をコミュニティ配分と説明。当初2026年Q1予定が延期され、新しい日程は未確認。",
            tasks=["OpenSea/Seaportでの取引・利用履歴を維持", "公式発表の確認"],
            end_date="未定", url="https://opensea.io/",
        ),
        item(
            id="metamask-mask", name="MetaMask (MASK)", symbol="MASK",
            category="ウォレット", type="ポイント", status="upcoming", difficulty="easy",
            estimated_value_usd=300,
            description="MetaMaskポイントプログラム経由のトークン配布が噂される。公式の日程は未確認(流出情報は『プロトタイプ』と説明)。",
            tasks=["MetaMaskでスワップ・ブリッジ・Perps等を利用", "ポイントプログラムの状況を確認"],
            end_date="未定", url="https://metamask.io/",
        ),
        item(
            id="layerzero-points", name="LayerZero パートナーアプリ", symbol="ZRO",
            category="インフラ", type="パートナーポイント", status="active", difficulty="medium",
            estimated_value_usd=100,
            description="ZROは既に上場済み。コミュニティ向け配分が残っており、LayerZero連携アプリごとのポイント施策が継続中 (情報は要検証)。",
            tasks=["連携dAppでクロスチェーン取引を実行"],
            end_date="未定", url="https://layerzero.network/",
        ),
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
