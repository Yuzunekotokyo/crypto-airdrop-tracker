"""
Airdrop情報をWeb/APIから収集するモジュール。
- airdrops.ioのパブリックページをスクレイピング
- DeFiLlamaからトークン未発行の高TVLプロトコルを取得
- CoinGeckoトレンドと組み合わせて使用
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


def _fetch_defi_llama_watchlist() -> list[dict]:
    """
    DeFiLlama: TVL高・時価総額低のプロトコル = エアドロップ有力候補。
    トークン未発行で実際の利用実績があるプロトコルを毎日最新で取得する。
    """
    try:
        r = requests.get("https://api.llama.fi/protocols", headers=HEADERS, timeout=25)
        r.raise_for_status()
        protocols = r.json()

        today = datetime.utcnow()
        candidates = []

        for p in protocols:
            tvl = float(p.get("tvl") or 0)
            mcap = float(p.get("mcap") or 0)
            name = (p.get("name") or "").strip()

            if not name:
                continue
            # TVL $30M+ かつ 時価総額 $5M未満 (トークン未発行 or 極小)
            if tvl < 30_000_000 or mcap > 5_000_000:
                continue

            chains = p.get("chains") or []
            category = p.get("category") or "DeFi"
            symbol = (p.get("symbol") or "").strip()
            slug = p.get("slug") or name.lower().replace(" ", "-")

            # TVLに基づくユーザーあたり推定エアドロップ価値
            # 想定: TVLの1%をエアドロップ総額とし、利用者数でわる
            est_users = max(tvl / 8000, 200)
            per_user = min(int(tvl * 0.01 / est_users), 3000)
            per_user = max(per_user, 30)

            is_hot = tvl > 100_000_000  # $100M+ TVL = HOT

            candidates.append({
                "id": f"llama-{slug[:50]}",
                "name": name,
                "symbol": symbol if (symbol and len(symbol) <= 6) else "未発行",
                "category": category,
                "type": "DeFiLlamaウォッチ",
                "status": "active",
                "difficulty": "easy" if len(chains) <= 2 else "medium",
                "estimated_value_usd": per_user,
                "description": (
                    f"TVL ${tvl / 1e6:.1f}M・{len(chains)}チェーン対応のプロトコル。"
                    f"トークン未発行のため将来エアドロップが期待される注目案件。"
                    f"カテゴリ: {category}"
                ),
                "tasks": [
                    "プロトコルを積極的かつ継続的に利用する",
                    "流動性提供・ステーキングを行う",
                    "定期的なトランザクション活動を維持する",
                    "公式DiscordやXで情報をフォロー",
                ],
                "end_date": (today + timedelta(days=365)).strftime("%Y-%m-%d"),
                "logo": p.get("logo") or "",
                "url": p.get("url") or f"https://defillama.com/protocol/{slug}",
                "is_hot": is_hot,
                "added_date": today.strftime("%Y-%m-%d"),
                "source": "defillama",
                "tvl_usd": int(tvl),
                "mcap_usd": int(mcap),
            })

        # TVL降順ソート、上位10件
        candidates.sort(key=lambda x: x.get("tvl_usd", 0), reverse=True)
        return candidates[:10]

    except Exception as e:
        logger.warning(f"DeFiLlama watchlist fetch failed: {e}")
        return []


def _build_seed_airdrops() -> list[dict]:
    """手動管理の注目エアドロップシードデータ (定期的に更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "layerzero-zro",
            "name": "LayerZero (ZRO)",
            "symbol": "ZRO",
            "category": "インフラ",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 500,
            "description": "クロスチェーンメッセージングプロトコル。ブリッジ・DeFi利用者向けエアドロップ。",
            "tasks": ["Stargate経由でブリッジを実行", "複数チェーンでのトランザクション", "LayerZero対応dApps利用"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/28206/small/ftxG9_TJ_400x400.jpeg",
            "url": "https://layerzero.network/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "scroll-scr",
            "name": "Scroll (SCR)",
            "symbol": "SCR",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "EVM互換ZK-Rollup。Ethereum L2でのトランザクション実績でエアドロップ獲得可能。",
            "tasks": ["ScrollネットワークへETHブリッジ", "Scroll上でのDeFi利用", "複数週にわたるアクティビティ"],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/25734/small/scroll.png",
            "url": "https://scroll.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "zksync-era",
            "name": "zkSync Era",
            "symbol": "ZK",
            "category": "Layer2",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 200,
            "description": "Matter Labsが開発するZK-Rollup。エコシステムが急拡大中。",
            "tasks": ["Era上でのスワップ", "Syncswap/Mute利用", "zkSync公式ブリッジ利用"],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/38043/small/ZKTokenBlack.png",
            "url": "https://zksync.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-hype",
            "name": "Hyperliquid (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "取引所トークン",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1000,
            "description": "高速オンチェーン永久先物DEX。独自L1チェーン上で動作。取引量によるポイント報酬。",
            "tasks": ["Hyperliquid上での先物取引", "流動性提供", "紹介プログラム参加"],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "eigenlayer-eigen",
            "name": "EigenLayer (EIGEN)",
            "symbol": "EIGEN",
            "category": "インフラ",
            "type": "リステーキング",
            "status": "active",
            "difficulty": "hard",
            "estimated_value_usd": 800,
            "description": "Ethereumのリステーキングプロトコル。ETHをステーキングし追加報酬を獲得。",
            "tasks": ["ETHをリステーキング", "LST (stETH等) をデポジット", "AVSへの参加"],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/33751/small/eigen.png",
            "url": "https://eigenlayer.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "movement-move",
            "name": "Movement (MOVE)",
            "symbol": "MOVE",
            "category": "Layer2",
            "type": "新規上場",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "Move VMを使用するEthereum L2。高速・低コストトランザクション。テストネット参加者向けエアドロップ予定。",
            "tasks": ["テストネット参加", "Discordコミュニティ参加", "テストトランザクション実行"],
            "end_date": (today + timedelta(days=20)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39619/small/MOVE_color.png",
            "url": "https://movementlabs.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
    ]


def fetch_all_airdrops() -> tuple[list[dict], list[str]]:
    """
    全ソースからエアドロップデータを収集し、変更点リストと共に返す。
    データソース: キュレート済み + airdrops.ioスクレイプ + DeFiLlamaウォッチリスト
    Returns: (airdrops_list, new_items_names)
    """
    curated = _build_seed_airdrops()
    scraped = _scrape_airdrops_io()
    defi_llama = _fetch_defi_llama_watchlist()

    seen_names = {a["name"].lower() for a in curated}
    new_items = []

    # airdrops.ioのスクレイプ結果を追加
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

    # DeFiLlamaウォッチリストを追加 (毎日最新データを取得)
    for p in defi_llama:
        if p["name"].lower() not in seen_names:
            curated.append(p)
            new_items.append(p["name"])
            seen_names.add(p["name"].lower())

    # 注目度でソート: is_hot → estimated_value_usd
    curated.sort(key=lambda x: (not x.get("is_hot"), -x.get("estimated_value_usd", 0)))

    return curated, new_items
