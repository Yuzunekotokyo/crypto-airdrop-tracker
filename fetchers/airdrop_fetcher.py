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
    """手動管理の注目エアドロップシードデータ (毎日のリサーチに基づき更新)"""
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
            "estimated_value_usd": 800,
            "description": "CMOがトークン発行とエアドロップ実施を公式に認めた予測市場最大手。配布条件は未発表だが、継続的な取引実績が有力な条件になる見込み。",
            "tasks": ["複数カテゴリ(政治・スポーツ・経済等)で継続的に取引する", "X(Twitter)アカウントを連携する", "Rewardsプログラムに参加し利益を再投資する"],
            "end_date": "2026年後半予定 (米国正式ローンチ後)",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "grass-season2",
            "name": "Grass Season 2",
            "symbol": "GRASS",
            "category": "DePIN/AI",
            "type": "報酬クレーム(USDC)",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 100,
            "description": "未使用の通信帯域を提供するDePINプロジェクト。Season2は300万ドル相当のUSDC報酬プールが7/22よりクレーム開始済み、今すぐ請求可能。",
            "tasks": ["Grassブラウザ拡張機能をインストールし稼働させる", "公式サイトでウォレットを接続し対象エポックの報酬を確認", "2027年1月22日の請求期限までにクレームを実行"],
            "end_date": "2027-01-22",
            "logo": "",
            "url": "https://www.grass.io/",
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
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "最大手NFTマーケットプレイス。2026年Q1にSEAトークンを発行し、OGユーザーとOS2でのXPクエスト参加者に段階配布中。",
            "tasks": ["OS2プラットフォームでのNFT売買・スイープ", "Voyagesプログラムのクエストを完了しXPを獲得", "既存ウォレットでの過去の取引実績確認"],
            "end_date": "順次配布中 (新規ファーミングは対象外)",
            "logo": "",
            "url": "https://opensea.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "backpack-token",
            "name": "Backpack (BACKPACK)",
            "symbol": "BACKPACK",
            "category": "取引所/Solana",
            "type": "ポイントプログラム",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 350,
            "description": "Solana系の規制準拠型取引所。供給の25%をコミュニティ配布するTGE計画を発表済み。Mad Ladsホルダーにも1%配分。",
            "tasks": ["現物・無期限先物のトレーディングでポイント獲得", "レンディング・紹介プログラムに参加", "Mad Lads NFTを保有する"],
            "end_date": "シーズン継続中 (次回スナップショット未定)",
            "logo": "",
            "url": "https://backpack.exchange/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "aster-aster",
            "name": "Aster (ASTER)",
            "symbol": "ASTER",
            "category": "DeFi/Perp DEX",
            "type": "トレーディングマイニング",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 300,
            "description": "オンチェーン無期限先物DEX。供給の53.5%をコミュニティ配分する多段階ポイントプログラムを継続実施中。",
            "tasks": ["Asterで先物取引を行い出来高を積み上げる", "ポジション保有・流動性提供でポイント加算", "紹介プログラムで追加ポイント獲得"],
            "end_date": "2026-11-28 (ベスティング分クレーム期限)",
            "logo": "",
            "url": "https://asterdex.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-token",
            "name": "Base ネットワークトークン",
            "symbol": "—",
            "category": "Layer2",
            "type": "未確認 (投機的)",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "Coinbase開発のL2。開発者が「ネットワークトークンを検討中」と発言したのみで、正式な発行・配布計画は未確定。投機段階のため過度な期待は禁物。",
            "tasks": ["Base上でのブリッジ・スワップ・NFT等の継続的なオンチェーン活動", "複数のdAppsを利用する", "onchainscore.xyz等でスコアを確認する"],
            "end_date": "未定 (2026年Q2〜Q4に検討との観測)",
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
