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
    """手動管理の注目エアドロップシードデータ (定期的に更新)。推定価値は目安であり保証ではない。"""
    today = datetime.utcnow()
    added = today.strftime("%Y-%m-%d")

    def item(id_, name, symbol, category, type_, status, difficulty, value, desc, tasks, url, hot, end="未定"):
        return {
            "id": id_, "name": name, "symbol": symbol, "category": category, "type": type_,
            "status": status, "difficulty": difficulty, "estimated_value_usd": value,
            "description": desc, "tasks": tasks, "end_date": end, "logo": "", "url": url,
            "is_hot": hot, "added_date": added, "source": "curated",
        }

    return [
        item("polymarket-poly", "Polymarket (POLY)", "POLY", "予測市場", "公式確認済み", "active", "easy", 1000,
             "トークンとエアドロップを公式が確認済み。スナップショット未実施で参加窓は開いたまま。米国版再ローンチ後(2026年後半見込み)にTGE予定。",
             ["予測市場で継続的に取引", "複数カテゴリーで取引・流動性提供", "取引量と利用期間を積み上げる"],
             "https://polymarket.com/", True),
        item("arc-network", "Arc Network (ARC)", "ARC", "Layer1", "未確認(期待先行)", "active", "easy", 500,
             "CircleのステーブルコインL1。2026/9/16にメインネット開始、BlackRock/Visa等がバリデータ。エアドロップは未発表だがテストネット・Arc House実績が対象候補。",
             ["Arc上でUSDC送金・dApp利用", "Arc Housesでポイント獲得", "主要ウォレットで継続利用"],
             "https://www.arc.network/", True),
        item("canopy-cnpy", "Canopy (CNPY)", "CNPY", "インフラ", "ポイント変換", "active", "medium", 400,
             "$CNPYが確認済み。ポイントがトークンに変換され、供給の50%がコミュニティ/利用者へ。",
             ["Canopyのポイントプログラムに参加", "プロダクトを継続利用"],
             "https://www.canopynetwork.org/", True),
        item("ekiden", "Ekiden", "", "DeFi/DEX", "ポイント報酬", "upcoming", "medium", 500,
             "メインネットに合わせた報酬プログラムを確認済み。取引でポイント獲得。トップテストネットトレーダーに招待制の早期アクセス。",
             ["テストネットで取引ボリュームを積む", "招待枠を狙う"],
             "https://ekiden.fi/", False),
        item("backpack", "Backpack", "", "取引所", "ポイント", "active", "medium", 600,
             "Solana発の規制準拠取引所。トークンの25%をコミュニティへ、うち24%がポイント保有者向けと報じられ、実施可能性が高い。",
             ["Backpackで取引", "ポイントを貯める"],
             "https://backpack.exchange/", False),
        item("metamask", "MetaMask", "", "ウォレット", "未確認(公式示唆)", "upcoming", "easy", 500,
             "ConsenSys幹部がネイティブトークン発行を公言。ユーザー活動が配布に影響する見込み。",
             ["MetaMaskでスワップ/ブリッジ/パーペチュアル利用", "MetaMask Rewardsに参加"],
             "https://metamask.io/", False),
        item("apyx-pips", "Apyx (APYX)", "APYX", "DeFi", "ポイント", "active", "medium", 200,
             "Pipsキャンペーンを2026/2月から実施中。apxUSD保有またはCurve/Pendleで流動性提供でPips獲得、2026年10月までブースト延長。",
             ["apxUSDを保有", "Curve/Pendleで流動性提供"],
             "https://apyx.fi/", False, "2026-10-31"),
        item("concrete-ct", "Concrete (CT)", "CT", "DeFi", "TGE予定", "upcoming", "medium", 300,
             "2026年9月にネイティブトークンCTとTGE計画を公式発表。",
             ["Concreteの利用履歴・ポイントを確認"],
             "https://concrete.xyz/", False),
        item("base", "Base", "", "Layer2", "未確認(期待先行)", "upcoming", "easy", 400,
             "Coinbase発L2。トークン発行は未確定だが期待が高い。",
             ["Base上でDeFi/アプリを継続利用"],
             "https://base.org/", False),
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
