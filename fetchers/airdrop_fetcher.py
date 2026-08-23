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
    """手動管理の注目エアドロップシードデータ (定期的に更新)

    最終リサーチ更新: 2026-08-23 (Web検索による最新情報反映)
    """
    today = datetime.utcnow()
    return [
        {
            "id": "flop-labs-flop",
            "name": "FLOP (Flop Labs)",
            "symbol": "FLOP",
            "category": "AI/インフラ",
            "type": "エアドロップ（フェアローンチ）",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "BitMEX共同創業者Arthur HayesがCEOに復帰して主導する新プロジェクト。AIエージェント経済向けの決済ネットワークを構築中で、VC・プレセールなしの「100%フェアローンチ」を公言。2026年Q4に大規模エアドロップ、ブロックチェーン本体のGenesisは2027年Q1予定という異例のスケジュール。配布条件・スナップショット方式は未発表。",
            "tasks": ["公式アナウンス（X/公式サイト）を継続的にフォロー", "配布条件は未公表のため詐欺・偽サイトに要注意", "テストネット参加条件が出た場合に備え準備"],
            "end_date": "2026年Q4予定（詳細未定）",
            "logo": "",
            "url": "https://crypto.news/arthur-hayes-returns-to-lead-flop-labs-ai-network/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "web-research",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ（未確定）",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "分散型予測市場プラットフォームの最大手。米国ローンチ後にPOLYトークン配布が予定されているが、2026年8月時点でスナップショット日・配布条件・供給量は未発表。継続的な取引実績が有利になると見られる。",
            "tasks": ["複数カテゴリの市場で継続的に取引", "設定画面でX(Twitter)アカウントを連携", "同一人物による複数ウォレット作成を避ける（除外リスク）", "Rewardsプログラムに参加してUSDC獲得と実績を両立"],
            "end_date": "未定（2026年後半 米国ローンチ後の見込み）",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "web-research",
        },
        {
            "id": "hyperliquid-hype",
            "name": "Hyperliquid (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "継続インセンティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 300,
            "description": "高速オンチェーン永久先物DEX。独自L1チェーン上で稼働。初回配布後も取引量・流動性提供に応じた追加インセンティブ配布が継続中で、2026年8月時点でも注目度の高い案件として言及される。",
            "tasks": ["Hyperliquid上での先物取引を継続", "流動性提供 (HLP)", "紹介プログラム参加"],
            "end_date": "継続プログラム（期限未定）",
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "web-research",
        },
        {
            "id": "midnight-night",
            "name": "Midnight (NIGHT)",
            "symbol": "NIGHT",
            "category": "プライバシー/サイドチェーン",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "Cardano系のプライバシー特化サイドチェーン。大型エアドロップが進行中で、直近週（2026年第33週）に請求期限を迎える対象があるため要注意。",
            "tasks": ["対象スナップショットの保有・対象条件を確認", "公式クレームサイトから期限内に申請手続きを完了"],
            "end_date": "2026年8月内（期限間近・要公式確認）",
            "logo": "",
            "url": "https://cryptoticker.io/en/crypto-airdrops-week-33-2026-deadlines/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "web-research",
        },
        {
            "id": "plume-network",
            "name": "Plume Network (PLUME)",
            "symbol": "PLUME",
            "category": "RWA/Layer2",
            "type": "レトロアクティブ（複数フェーズ）",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "実世界資産(RWA)特化のモジュラーL2。複数フェーズに分けたエアドロップを実施中で、直近週に一部フェーズの請求期限が到来。",
            "tasks": ["Plumeエコシステム内でのRWAトークン取引・ステーキング", "対象フェーズのクレーム期限を公式で確認"],
            "end_date": "2026年8月内（フェーズにより期限間近）",
            "logo": "",
            "url": "https://cryptoticker.io/en/crypto-airdrops-week-33-2026-deadlines/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "web-research",
        },
        {
            "id": "grass",
            "name": "Grass (GRASS)",
            "symbol": "GRASS",
            "category": "DePIN",
            "type": "レトロアクティブ/継続配布",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "未使用の帯域幅を提供してAI学習データ収集に貢献するDePINプロジェクト。ポイント制の継続的なエアドロップを実施中。",
            "tasks": ["Grassアプリ/ブラウザ拡張機能をインストールし帯域を共有", "GRASS Pointsを蓄積"],
            "end_date": "継続中（期限未定）",
            "logo": "",
            "url": "https://www.grass.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "web-research",
        },
        {
            "id": "base-l2",
            "name": "Base",
            "symbol": "-",
            "category": "Layer2",
            "type": "エアドロップ（噂・未確定）",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Coinbaseが開発するEthereum L2。独自トークン発行は正式発表されていないが、将来的な配布があればオンチェーン活動実績が評価対象になると見られている。",
            "tasks": ["Base上でのブリッジ・スワップを実行", "Base上のdApps利用実績を積む"],
            "end_date": "未定",
            "logo": "",
            "url": "https://base.org/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "web-research",
        },
        {
            "id": "opensea",
            "name": "OpenSea",
            "symbol": "-",
            "category": "NFTマーケットプレイス",
            "type": "エアドロップ（噂・未確定）",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "大手NFTマーケットプレイス。将来的なトークン配布が市場で期待されている大型案件の一つだが、公式発表はまだ確認されていない。",
            "tasks": ["OpenSea上でのNFT売買・取引を継続", "公式アナウンスを注視"],
            "end_date": "未定",
            "logo": "",
            "url": "https://opensea.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "web-research",
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
