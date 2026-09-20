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
    """手動管理の注目エアドロップシードデータ (毎日のリサーチに基づき更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "ウォレット",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 1500,
            "description": (
                "ConsenSys CEOのJoseph Lubin氏が「予想より早く」登場すると明言。3000万ユーザーを抱える"
                "世界最大のウォレットのトークンで、2024〜2026年のアクティブウォレットがスナップショット"
                "対象とされる見込み。ConsenSysのIPOに合わせた2026年Q3〜Q4ローンチが有力視されている。"
            ),
            "tasks": [
                "MetaMaskウォレットを日常的に使用する",
                "MetaMask Rewardsプログラムでポイントを貯める",
                "Swaps/Bridge機能を利用する",
                "Linea上でのアクティビティも対象になる可能性が高い",
            ],
            "end_date": "未定（2026年Q3〜Q4が有力）",
            "logo": "",
            "url": "https://metamask.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 800,
            "description": (
                "CMOが「トークンとエアドロップは確実に実施する」と公式表明済み。スナップショット日・"
                "配布率は未発表だが、供給の5〜10%程度がアクティブトレーダー向けに配分される見込み。"
                "米国事業の本格再開後のローンチが濃厚。"
            ),
            "tasks": [
                "実際に予測市場で取引する",
                "複数カテゴリの市場に継続的に参加する",
                "X(Twitter)アカウントを連携する",
                "スナップショット発表前から活動実績を積んでおく",
            ],
            "end_date": "未定（米国事業再開後を想定）",
            "logo": "",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-season2",
            "name": "Hyperliquid Season 2 (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "ポイント/ステーキング",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1000,
            "description": (
                "コミュニティ報酬ウォレットに4億2800万枚以上のHYPEが未配布のまま残存。2026年2月に"
                "ローンチしたHyperEVMへの参加でSeason 2スナップショットのウェイトが上昇する。"
            ),
            "tasks": [
                "Perps/Spotで取引しポイントを獲得する",
                "HYPEをステーキングしバリデーターに委任する",
                "HyperEVM上のDeFiアプリを利用する(5 HYPE以上をブリッジ)",
                "$10k取引量達成後に紹介コードを発行する",
            ],
            "end_date": "未定（継続中のシーズン）",
            "logo": "",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-network-token",
            "name": "Base ネットワークトークン (未発表)",
            "symbol": "",
            "category": "Layer2",
            "type": "投機的/未確定",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": (
                "CoinbaseがBase向けネットワークトークンを検討中と報道。JPMorganは時価総額120億〜340億"
                "ドルと試算しているが、公式発表・スナップショット基準は一切未確定の段階。"
            ),
            "tasks": [
                "Base上でのトランザクション実績を積んでおく",
                "Base関連dAppsの利用を継続する",
                "公式発表を注視する(現時点で確定タスクなし)",
            ],
            "end_date": "未定（トークン自体が未確定）",
            "logo": "",
            "url": "https://base.org/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "opensea-sea",
            "name": "OpenSea (SEA)",
            "symbol": "SEA",
            "category": "NFT",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": (
                "2026年3月にCEOがローンチ延期を発表(新日程は未発表)。供給の50%をコミュニティに配分し、"
                "初回クレームで全体の約25%を配布する計画自体は維持されている。OGユーザーとRewards"
                "プログラム参加者が対象。"
            ),
            "tasks": [
                "OpenSea Rewardsプログラムに参加する",
                "OGユーザー資格を確認する(過去の取引実績)",
                "延期中の手数料優遇期間を活用して取引を続ける",
                "公式Xで再開発表をチェックする",
            ],
            "end_date": "延期中（新日程未発表）",
            "logo": "",
            "url": "https://opensea.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "backpack-bp",
            "name": "Backpack (BP)",
            "symbol": "BP",
            "category": "取引所/ウォレット",
            "type": "配布済み+ステーキング継続",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 150,
            "description": (
                "2026年3月23日にBPトークンがSolana上でTGE済み。供給の25%(2億4000万枚)がポイント"
                "保有者に、1000万枚がMad Lads NFT保有者に配布済み。現在はステーキングでBackpack "
                "Participant Programの特典・将来的な株式転換オプションを狙うフェーズ。"
            ),
            "tasks": [
                "BPをステーキングしParticipant Programの特典を獲得する",
                "Backpack取引所の継続利用でSeason 4ポイントを蓄積する",
                "Mad Lads NFT保有で追加特典を得る",
            ],
            "end_date": "ステーキング継続中",
            "logo": "",
            "url": "https://backpack.exchange/",
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
