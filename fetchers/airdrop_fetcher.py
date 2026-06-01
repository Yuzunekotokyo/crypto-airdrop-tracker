"""
Airdrop情報を複数のWeb/APIソースから収集するモジュール。
Sources: airdrops.io, CoinMarketCap, DeFiLlama protocols, CoinGecko trending
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
    """airdrops.io からアクティブエアドロップを取得"""
    try:
        r = requests.get("https://airdrops.io/", headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        # 複数のセレクタパターンに対応
        cards = (
            soup.select(".airdrop-item")
            or soup.select(".featured-airdrop")
            or soup.select("article.airdrop")
        )
        for card in cards[:30]:
            name_el = (
                card.select_one(".airdrop-title")
                or card.select_one("h2")
                or card.select_one("h3")
            )
            link_el = card.select_one("a[href]")
            value_el = card.select_one(".airdrop-value") or card.select_one(".value")
            end_el = card.select_one(".airdrop-end") or card.select_one(".end-date")
            img_el = card.select_one("img")
            if not name_el:
                continue
            url = link_el["href"] if link_el else "https://airdrops.io/"
            if url.startswith("/"):
                url = "https://airdrops.io" + url
            items.append({
                "name": name_el.get_text(strip=True),
                "url": url,
                "estimated_value": value_el.get_text(strip=True) if value_el else "",
                "end_date": end_el.get_text(strip=True) if end_el else "未定",
                "logo": img_el.get("src", "") if img_el else "",
                "source": "airdrops.io",
            })
        logger.info(f"airdrops.io: {len(items)}件取得")
        return items
    except Exception as e:
        logger.warning(f"airdrops.io scrape failed: {e}")
        return []


def _scrape_coinmarketcap_airdrops() -> list[dict]:
    """CoinMarketCap Airdrops ページからデータ取得"""
    try:
        r = requests.get(
            "https://coinmarketcap.com/airdrop/",
            headers={**HEADERS, "Accept-Language": "en-US,en;q=0.9"},
            timeout=15,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        # CMCのairdropsテーブル
        rows = soup.select("table tbody tr") or soup.select(".airdrop-row")
        for row in rows[:20]:
            cells = row.select("td")
            if len(cells) < 3:
                continue
            name_el = row.select_one("a") or (cells[0] if cells else None)
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if not name or len(name) < 2:
                continue
            href = name_el.get("href", "")
            url = f"https://coinmarketcap.com{href}" if href.startswith("/") else href
            items.append({
                "name": name,
                "url": url or "https://coinmarketcap.com/airdrop/",
                "estimated_value": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                "end_date": cells[3].get_text(strip=True) if len(cells) > 3 else "未定",
                "logo": "",
                "source": "coinmarketcap",
            })
        logger.info(f"CoinMarketCap: {len(items)}件取得")
        return items
    except Exception as e:
        logger.warning(f"CoinMarketCap scrape failed: {e}")
        return []


def _fetch_defillama_protocols() -> list[dict]:
    """DeFiLlama の新着・注目プロトコルを取得 (エアドロップ候補)"""
    try:
        r = requests.get(
            "https://api.llama.fi/protocols",
            headers={"Accept": "application/json"},
            timeout=15,
        )
        r.raise_for_status()
        protocols = r.json()
        # 直近追加 & TVL高い & トークンなし (エアドロップ未実施候補)
        candidates = [
            p for p in protocols
            if not p.get("symbol") and p.get("tvl", 0) > 10_000_000
        ]
        candidates.sort(key=lambda x: x.get("tvl", 0), reverse=True)
        items = []
        for p in candidates[:10]:
            name = p.get("name", "")
            if not name:
                continue
            items.append({
                "name": f"{name} (未トークン化)",
                "url": p.get("url") or f"https://defillama.com/protocol/{p.get('slug','')}",
                "estimated_value": f"TVL: ${p.get('tvl',0)/1_000_000:.1f}M",
                "end_date": "未定",
                "logo": p.get("logo", ""),
                "source": "defillama",
                "tvl": p.get("tvl", 0),
                "category": p.get("category", "DeFi"),
            })
        logger.info(f"DeFiLlama: {len(items)}件候補取得")
        return items
    except Exception as e:
        logger.warning(f"DeFiLlama fetch failed: {e}")
        return []


def _parse_estimated_value(value_str: str) -> int:
    """'$500' や '500 USD' などを数値に変換"""
    if not value_str:
        return 0
    import re
    m = re.search(r"[\d,]+", value_str.replace(",", ""))
    if m:
        try:
            return int(m.group().replace(",", ""))
        except ValueError:
            pass
    return 0


def _build_seed_airdrops() -> list[dict]:
    """手動管理の注目エアドロップシードデータ"""
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
        {
            "id": "monad-mon",
            "name": "Monad",
            "symbol": "MON",
            "category": "Layer1",
            "type": "テストネット",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 600,
            "description": "EVM互換高性能L1。10,000 TPS超の並列EVM実行。テストネット参加でエアドロップ期待。",
            "tasks": ["テストネット参加", "Faucetでトークン取得", "テストDApps利用", "Discord参加"],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://monad.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "berachain-bera",
            "name": "Berachain (BERA)",
            "symbol": "BERA",
            "category": "Layer1",
            "type": "テストネット",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 700,
            "description": "Proof of Liquidity (PoL) メカニズムを採用するEVM互換L1。流動性提供者が報酬を受け取る。",
            "tasks": ["テストネットに参加", "BGT取得", "流動性提供", "Berachainエコシステム利用"],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "",
            "url": "https://berachain.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
    ]


def fetch_all_airdrops() -> tuple[list[dict], list[str]]:
    """
    全ソースからエアドロップデータを収集し統合する。
    Returns: (airdrops_list, new_items_names)
    """
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    curated = _build_seed_airdrops()
    seen_names = {a["name"].lower(): a for a in curated}

    # 外部ソースから取得
    scraped_sources = [
        _scrape_airdrops_io(),
        _scrape_coinmarketcap_airdrops(),
    ]
    new_items = []

    for source_items in scraped_sources:
        for s in source_items:
            name_lower = s["name"].lower()
            if name_lower in seen_names:
                continue
            # 新規案件として追加
            val = _parse_estimated_value(s.get("estimated_value", ""))
            curated.append({
                "id": name_lower.replace(" ", "-").replace("(", "").replace(")", ""),
                "name": s["name"],
                "symbol": "",
                "category": "その他",
                "type": "エアドロップ",
                "status": "active",
                "difficulty": "easy",
                "estimated_value_usd": val,
                "description": f"{s.get('source','Web')}より取得: {s.get('estimated_value', '')}",
                "tasks": [],
                "end_date": s.get("end_date", "未定"),
                "logo": s.get("logo", ""),
                "url": s.get("url", ""),
                "is_hot": val >= 500,
                "added_date": today_str,
                "source": s.get("source", "web"),
            })
            new_items.append(s["name"])
            seen_names[name_lower] = curated[-1]

    # DeFiLlamaの未トークン化プロトコルを注目候補として追加
    defillama = _fetch_defillama_protocols()
    for dl in defillama[:5]:
        name_lower = dl["name"].lower()
        if name_lower in seen_names:
            continue
        tvl = dl.get("tvl", 0)
        curated.append({
            "id": name_lower.replace(" ", "-").replace("(", "").replace(")", ""),
            "name": dl["name"],
            "symbol": "",
            "category": dl.get("category", "DeFi"),
            "type": "未トークン化",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": min(int(tvl / 100_000), 2000),
            "description": f"DeFiLlamaより: TVL ${tvl/1_000_000:.1f}M。トークン未発行のため将来的なエアドロップ候補。",
            "tasks": ["プロトコル利用", "流動性提供"],
            "end_date": "未定",
            "logo": dl.get("logo", ""),
            "url": dl.get("url", ""),
            "is_hot": tvl > 100_000_000,
            "added_date": today_str,
            "source": "defillama",
        })
        new_items.append(dl["name"])
        seen_names[name_lower] = curated[-1]

    # ソート: is_hot → estimated_value_usd
    curated.sort(key=lambda x: (not x.get("is_hot"), -x.get("estimated_value_usd", 0)))

    return curated, new_items
