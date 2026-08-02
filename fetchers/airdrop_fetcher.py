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
    """手動管理の注目エアドロップシードデータ (2026年8月時点の最新情報に基づき定期更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "hyperliquid-season2",
            "name": "Hyperliquid Season 2 (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "ポイント制/レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1200,
            "description": "分散型パーペチュアル取引所。Season 2ポイントファーミングが進行中。HyperEVM追加で新たなファーミング機会も拡大。スナップショット日は未公表のため要注視。",
            "tasks": ["Perp/Spot取引でボリュームを積む", "HLPボールトへ流動性提供", "5 HYPE以上をHyperEVMにブリッジしDeFi利用"],
            "end_date": "未定(スナップショット日未announced)",
            "logo": "",
            "url": "https://airdrops.io/hyperliquid/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket (POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ(未確定)",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "世界最大の予測市場プラットフォーム。CMOがトークン・エアドロップ実施を公式に示唆(2026年後半予想)。ファーミング不可・実利用者のみが対象と噂されており、いま実際に使うことが最善策。",
            "tasks": ["Polymarketで実際に予測市場に参加", "少額でもポジションを取り利用実績を作る", "公式アナウンスを継続的にチェック"],
            "end_date": "未定",
            "logo": "",
            "url": "https://airdrops.io/polymarket/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "backpack-exchange",
            "name": "Backpack Exchange",
            "symbol": "BACKPACK",
            "category": "取引所/ウォレット",
            "type": "ポイント制",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 500,
            "description": "セルフカストディウォレット+規制対応取引所(VARAライセンス)。2026年2月にTGE計画を発表済み。供給の25%をコミュニティに配分予定(24%ポイント保有者/1%Mad Lads NFT保有者)。Season 4進行中。",
            "tasks": ["Backpack取引所で取引しポイント獲得", "Backpackウォレットを日常使用", "Mad Lads NFT保有で追加配分"],
            "end_date": "未定(TGE計画済み)",
            "logo": "",
            "url": "https://backpack.exchange/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "n1-chain",
            "name": "N1 Chain",
            "symbol": "N1",
            "category": "インフラ/L1",
            "type": "テストネット参加",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 0,
            "description": "トレーディング特化の新興L1ブロックチェーン(Founders Fund出資)。テストネットが稼働中で早期採用者にエアドロップの可能性。2026年8月にメインネット予定と噂されており今が滑り込みのタイミング。",
            "tasks": ["テストネットに接続しトランザクションを実行", "N1 Appでの取引体験", "公式Discord/Xでのコミュニティ参加"],
            "end_date": "未定",
            "logo": "",
            "url": "https://airdrops.io/n1/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "ウォレット",
            "type": "噂/未確定",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "世界最大級のセルフカストディウォレット。MASKトークン発行の噂が継続的に浮上しているが公式発表はまだ無いため過度な期待は禁物。",
            "tasks": ["MetaMaskウォレットを継続利用", "MetaMask Cardなど新機能を試す", "公式アナウンスを注視"],
            "end_date": "未定",
            "logo": "",
            "url": "https://metamask.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-token",
            "name": "Base Token",
            "symbol": "BASE",
            "category": "Layer2",
            "type": "噂/未確定",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": "Coinbaseが開発するEthereum L2。トークン発行観測が根強く2026年の有力候補として繰り返し言及されているが公式確認はまだ無い。",
            "tasks": ["Base上でDeFi/dApp利用実績を積む", "公式Baseブリッジを利用", "エコシステムアプリの利用を継続"],
            "end_date": "未定",
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
