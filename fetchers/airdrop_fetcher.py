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
            "id": "ink-chain-ink",
            "name": "Ink Chain (INK)",
            "symbol": "INK",
            "category": "Layer2/DeFi",
            "type": "ポイントプログラム",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Krakenが支援するSuperchain L2。Nado(永久先物DEX)とTydro(レンディング)の利用実績に応じてINKエアドロップが確定。TVLは数ヶ月で$7M→$450Mに急増中の最注目案件。",
            "tasks": ["Kraken Proで取引実績を積む", "Nado(永久先物DEX)を利用", "Tydro(レンディング)で預入/借入", "流動性提供(LP)ポジションを保有"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d") + " 頃 (配布予定)",
            "logo": "",
            "url": "https://inkonchain.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-season2-hype",
            "name": "Hyperliquid Season 2 (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "ポイントプログラム(第2期)",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "2024年の初回HYPE配布とは別の新シーズン。ハードキャップの42%(約4.2億HYPE)を新規プールとして確保。スナップショット時期は事前予告なしのため注意。",
            "tasks": ["HYPEをステーキング(1日1トークンあたり8pt)", "取引量を積む(1ドルあたり1pt)", "新規上場ペアで取引(1.5倍ボーナス)", "HyperEVM上のdAppsを利用"],
            "end_date": "未定 (事前予告なし)",
            "logo": "",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "米国再上陸後、CMOがトークン発行とエアドロップ実施を公式に確認。ICEから20億ドル規模の出資を受け評価額は約90億ドル。日付は未定だが本命候補。",
            "tasks": ["複数の予測マーケットで取引", "X(Twitter)アカウントを連携したまま維持", "継続的な取引アクティビティを積む", "勝利金を出金せず再投資"],
            "end_date": "未定 (2026年後半予想)",
            "logo": "",
            "url": "https://polymarket.com/airdrop",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-l2",
            "name": "Base (Coinbase L2)",
            "symbol": "-",
            "category": "Layer2/インフラ",
            "type": "投機的レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Coinbase運営のL2。2025年9月にネイティブトークン検討を公式表明(発行確約はまだ無し)。JPMorganはネットワーク評価額を120億〜340億ドルと試算。",
            "tasks": ["Baseへブリッジ", "Base上のdAppsを継続利用", "定期的な取引履歴を積む", "スナップショット関連ニュースを注視"],
            "end_date": "未定 (年内発表確率69%との予測市場オッズ)",
            "logo": "",
            "url": "https://base.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "インフラ/ウォレット",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "ConsenSysがMASKトークン発行を確認済み。スナップショットは2024〜2026年のウォレット利用実績、特にLinea利用に比重。「暗号資産史上最大級」と期待されるが延期が続いている。",
            "tasks": ["MetaMaskウォレットで定期的にスワップ", "Lineaネットワークを利用", "MetaMask Rewardsプログラムに参加", "ウォレットをアクティブに保つ"],
            "end_date": "未定 (2026年Q3〜Q4に延期)",
            "logo": "",
            "url": "https://metamask.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "extended-perp",
            "name": "Extended (旧X10)",
            "symbol": "-",
            "category": "DeFi/永久先物DEX",
            "type": "ポイントプログラム",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "元Revolutチームが開発する高性能永久先物DEX。TVL1億ドル超、累計取引高920億ドル超。トークン供給の30%をエアドロップに充当することを確認済み。",
            "tasks": ["入金して取引量を積む", "流動性提供(LPで+20%ポイント)", "$10,000取引達成で紹介プログラム解放", "継続的な取引アクティビティを維持"],
            "end_date": "未定",
            "logo": "",
            "url": "https://extended.exchange/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "abstract-chain-abs",
            "name": "Abstract Chain (ABS)",
            "symbol": "ABS",
            "category": "Layer2/コンシューマー",
            "type": "XPプログラム",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Pudgy Penguins関連のコンシューマー向けL2。トークン未発行だがXPが将来的な配分に変換される見込み。ゲーム・NFT連携が特徴。",
            "tasks": ["メインネットでブリッジ/スワップ", "ドメインをミント", "デイリーログイン/投票ストリークを維持", "PENGUを保有"],
            "end_date": "未定",
            "logo": "",
            "url": "https://abs.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "perceptron-network-perc",
            "name": "Perceptron Network (PERC)",
            "symbol": "PERC",
            "category": "AI/DePIN",
            "type": "ポイント/ロイヤリティプログラム",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "AI関連の分散型データ/インセンティブネットワーク(旧BlockMesh)。「Minder」NFT保有による信頼度ベースの報酬階層制度。正式上場は2026年Q2〜Q3の噂。",
            "tasks": ["アプリ/ノードを稼働", "クエストを完了", "PERC NFTを保有", "友人を紹介"],
            "end_date": "未定",
            "logo": "",
            "url": "https://airdrops.io/perceptron-network/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "teneo-protocol-teneo",
            "name": "Teneo Protocol (TENEO)",
            "symbol": "TENEO",
            "category": "DePIN/AIデータ",
            "type": "ポイントプログラム",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "ブラウザ拡張機能/ノードベースのデータネットワーク。Season 0終了(2026年4月25日)を経てSeason 1が進行中。USDC/TENEOポイントを定期配布。",
            "tasks": ["Teneoビーコン/拡張機能を稼働", "マイルストーンを達成", "友人を紹介"],
            "end_date": "未定 (2026年Q2〜Q3にTGE予想)",
            "logo": "",
            "url": "https://airdrops.io/teneo-protocol/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "pear-protocol-season3",
            "name": "Pear Protocol — Hypear Season 3",
            "symbol": "PEAR",
            "category": "DeFi/ペアトレーディング",
            "type": "ポイントプログラム(第2弾)",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "Hyperliquidのエンジン上で動くペアトレーディングDEX。PEARトークンは既に上場済みだが、継続中のセカンダリーポイントシーズンが進行中。",
            "tasks": ["PARA/ペアマーケットで取引", "友人を紹介", "週次ポイントを積み上げ"],
            "end_date": "毎週更新 (明確な終了日なし)",
            "logo": "",
            "url": "https://www.pear.garden/",
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
