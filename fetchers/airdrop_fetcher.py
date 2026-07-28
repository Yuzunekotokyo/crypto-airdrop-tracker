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
    """手動管理の注目エアドロップシードデータ。
    毎日の自動更新ジョブがWeb検索結果を元にこの関数を書き換え、
    実在する最新の案件に差し替える運用を想定 (最終更新: 2026-07-28)。
    """
    today = datetime.utcnow()
    return [
        {
            "id": "aiw3-genesis",
            "name": "AIW3 Genesis Airdrop",
            "symbol": "AIW3",
            "category": "AI/トレーディング",
            "type": "ジェネシスエアドロップ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Solana上のAI戦略トレーディングプラットフォーム。7/28にジェネシス・スナップショットを実施済みだが、獲得済みポイントは今後の月次配布にも持ち越される。資格確認ツールは7/29公開、TGE・claimは8/3予定。推定価値は未公表。",
            "tasks": ["aiw3.aiでウォレット接続", "プラットフォーム上のタスク/戦略作成でポイント獲得", "7/29公開の資格確認ツールでチェック"],
            "end_date": "2026-08-03",
            "logo": "",
            "url": "https://aiw3.ai/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-season2",
            "name": "Hyperliquid Season 2 (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "ポイントファーミング",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 600,
            "description": "オンチェーン永久先物DEX。HYPE総供給の38.888%がシーズン制で配布予定で、Season2向けに428M HYPEが未配布のまま。ステーキング・取引・2026/2/18ローンチのHyperEVM活用でポイントを積み上げられる。Season2のスナップショット日は未発表。",
            "tasks": ["HYPEをステーキング(1日あたり約8pt/HYPE)", "Perps/Spotで取引しポイント獲得", "HyperEVMにブリッジしDeFiアプリを利用"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://app.hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket-poly-rumor",
            "name": "Polymarket (POLY・トークン噂)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "噂・未確定",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "CMOがポッドキャストでトークンとエアドロップの存在を認めたが、正式発表・配布条件はまだ非公開。米国リローンチ完了を優先しており、コミュニティでは2026年後半のローンチが有力視されている。取引量・多様なマーケット参加が資格の目安になると推測されている。",
            "tasks": ["Polymarketで実際に取引する", "複数の異なるマーケットに参加する", "獲得した利益を再投資する"],
            "end_date": "未定",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "spicenet-points",
            "name": "Spicenet ポイントファーミング",
            "symbol": "",
            "category": "Solana/DeFi",
            "type": "ポイントファーミング",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Celestiaのデータ可用性層を使うDeFiブローカレッジネットワーク。Portalでクエスト・デイリーチェックイン・紹介プログラムを通じてSpice Pointsを獲得可能。トークン配布(TGE)は公式には未確定だが、ポイントは将来の配布に繋がるとアナウンスされている。",
            "tasks": ["portal.spicenet.ioでウォレット接続", "デイリーチェックイン", "友人紹介(招待者が1,000pt達成で200ptボーナス)"],
            "end_date": "未定",
            "logo": "",
            "url": "https://portal.spicenet.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-network-token-rumor",
            "name": "Base ネットワークトークン(噂)",
            "symbol": "",
            "category": "Layer2",
            "type": "噂・未確定",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "CoinbaseのBaseがネットワークトークンの検討を公式に認めたが、時期・配布方法は未確定(2026年Q2〜Q4を検討中との報道)。⚠️「公式クレームサイト」を名乗るものは全て詐欺だと明言されている。base.org以外のリンクからウォレットを接続しないこと。",
            "tasks": ["base.orgで通常のオンチェーン活動を積む", "非公式の『クレームサイト』には絶対にウォレットを接続しない"],
            "end_date": "未定",
            "logo": "",
            "url": "https://base.org/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "metamask-mask-caution",
            "name": "⚠️ MetaMask (MASK) 配布詐欺に注意",
            "symbol": "",
            "category": "詐欺警戒",
            "type": "フィッシング注意喚起",
            "status": "upcoming",
            "difficulty": "",
            "estimated_value_usd": 0,
            "description": "ConsenSys CEOがMASKトークン構想を認めたのみで、公式な配布開始のアナウンスはまだない。にもかかわらず「mskfndt.info」など非公式ドメインで『配布開始・今すぐclaim』を騙るフィッシングサイトが既に出回っている。シードフレーズの入力やウォレット接続は絶対に行わないこと。",
            "tasks": ["metamask.io / consensys.io以外の『claim』案内は信用しない", "SNSやメールで届く緊急性を煽るリンクは開かない"],
            "end_date": "未定",
            "logo": "",
            "url": "https://metamask.io/",
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
