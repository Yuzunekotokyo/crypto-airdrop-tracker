"""
Airdrop情報をWeb/APIから収集するモジュール。
現在はairdrops.ioのパブリックページとCoinGeckoトレンドを組み合わせて使用。
"""

import requests
import logging
from datetime import datetime
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
    """手動管理の注目エアドロップシードデータ (毎日のスケジュール実行時にWeb検索した最新情報で更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "grass-grass-s2",
            "name": "Grass (GRASS) Season 2",
            "symbol": "GRASS",
            "category": "DePIN",
            "type": "クレーム開始 (Stage 2)",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "分散型帯域幅ネットワークGrassのSeason 2クレームが2026年7月22日に開始。2024年10月〜2026年6月に貯めたNetwork Points/Uptime Pointsに応じてUSDCで報酬が支払われる。未クレーム分は2027年1月22日で失効するため早めの確認が必要。",
            "tasks": ["公式ダッシュボードでウォレットを接続しクレーム対象か確認", "対象期間中にポイントを保有していれば追加タスクなしで即クレーム可能", "フィッシング注意: 公式はDMで秘密鍵やシードフレーズを聞かない"],
            "end_date": "2027-01-22",
            "logo": "",
            "url": "https://airdrops.io/grass/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-hype-s2",
            "name": "Hyperliquid Season 2 (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "ポイントプログラム",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1000,
            "description": "オンチェーン永久先物DEX Hyperliquidの第2弾ポイントプログラムが進行中。取引・ステーキング・HyperEVM上でのDeFi活動でポイント獲得。Season 1では100万ドル超を獲得したウォレットが1,589件以上と報じられており、Season 2も高額配布が期待されているがスナップショット時期は未発表。",
            "tasks": ["Hyperliquidでの先物/現物取引", "HYPEステーキング", "HyperEVM上のDeFiアプリ利用・流動性提供"],
            "end_date": "未定 (スナップショット未発表)",
            "logo": "",
            "url": "https://app.hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "エアドロップ予定",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "Polymarketのマーケティング責任者が「トークンとエアドロップは必ず実施する」と公式に明言。米国アプリのローンチ後、2026年後半にPOLYトークンをローンチする見込みで、供給の5〜10%がエアドロップに充てられると報じられている。配布条件はまだ未確定。",
            "tasks": ["継続的な取引量の積み上げ", "多様なマーケットへの参加", "Polymarketアカウントと公式Xアカウントの連携"],
            "end_date": "2026年後半 (未定)",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperlynx-lynx",
            "name": "Hyperlynx (LYNX)",
            "symbol": "LYNX",
            "category": "DeFi/DEX (HyperEVM)",
            "type": "ポイントプログラム (The Hunt)",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "HyperEVM上のスポットDEX/トレーディング端末Hyperlynxが、供給の30% (3億LYNX) を「The Hunt」ポイントプログラムで配布予定。ポイント配分は取引30%・流動性提供70%でTGE時に按分配布される見込み (TGEは2026年10〜11月予定)。Genesis期間中は全操作にポイント2倍ボーナスが付与中。",
            "tasks": ["HyperEVM対応ウォレットを接続", "Hyperlynx上でのトレード", "流動性提供でポイント獲得 (Genesis期間は2倍)"],
            "end_date": "2026年10-11月頃 (TGE予定)",
            "logo": "",
            "url": "https://usethebitcoin.com/airdrop/hyperlynx/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "katana-kat",
            "name": "Katana Network (KAT)",
            "symbol": "KAT",
            "category": "DeFi/L2",
            "type": "コンテンツ/流動性キャンペーン",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "KATトークンは2026年3月18日にローンチ済み (POLステーカー向けに供給の15%を配布済み)。現在はKaito連携のコンテンツキャンペーンや流動性提供による継続インセンティブが進行中。",
            "tasks": ["公式アプリ (app.katana.network) でUSDC/WETH/WBTCボールトに流動性を預け入れ", "Katana×Kaitoキャンペーンで公式Xにオリジナルコンテンツを投稿しYaps獲得", "偽サイトに注意し公式ドメインのみ利用"],
            "end_date": "継続中",
            "logo": "",
            "url": "https://katana.network/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "spicenet",
            "name": "Spicenet",
            "symbol": "",
            "category": "インフラ/DeFi",
            "type": "ポイントプログラム",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "マルチチェーンDeFiアクセスを提供するSpicenetのポータルが稼働中。デイリーチェックイン・リファラル・クエストでSpice Pointsを獲得しリーダーボードを上昇。将来のトークンエコシステム開始時に報酬へ転換される可能性がある。Spice Flow×Reppoのプライベートベータキャンペーンも実施中。",
            "tasks": ["ポータル (portal.spicenet.io) にEVM対応ウォレットを接続", "デイリーチェックイン", "リファラルプログラム・クエスト参加"],
            "end_date": "継続中 (トークンローンチ未定)",
            "logo": "",
            "url": "https://portal.spicenet.io/",
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
