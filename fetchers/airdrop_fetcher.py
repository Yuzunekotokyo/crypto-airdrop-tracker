"""
Airdrop情報をWeb/APIから収集するモジュール。
複数ソース: airdrops.io スクレイピング + curated シードデータ
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
        # 複数のCSSセレクタパターンを試す (サイト構造変化に対応)
        selectors = [".airdrop-item", ".airdrop-card", "article.airdrop", ".listing-item"]
        cards = []
        for sel in selectors:
            cards = soup.select(sel)
            if cards:
                break

        for card in cards[:30]:
            name_el = (card.select_one(".airdrop-title") or card.select_one("h3")
                       or card.select_one("h2") or card.select_one(".title"))
            link_el = card.select_one("a[href]")
            value_el = (card.select_one(".airdrop-value") or card.select_one(".value")
                        or card.select_one(".reward"))
            end_el = (card.select_one(".airdrop-end") or card.select_one(".end-date")
                      or card.select_one(".deadline"))
            img_el = card.select_one("img")

            if not name_el:
                continue

            href = link_el["href"] if link_el else "https://airdrops.io/"
            if href and not href.startswith("http"):
                href = "https://airdrops.io" + href

            items.append({
                "name": name_el.get_text(strip=True),
                "url": href,
                "estimated_value": value_el.get_text(strip=True) if value_el else "不明",
                "end_date": end_el.get_text(strip=True) if end_el else "未定",
                "logo": img_el.get("src", "") if img_el else "",
                "source": "airdrops.io",
            })
        logger.info(f"airdrops.io: {len(items)}件取得")
        return items
    except Exception as e:
        logger.warning(f"airdrops.io scrape failed: {e}")
        return []


def _scrape_defi_airdrops() -> list[dict]:
    """追加ソース: DeFiLlamaのエアドロップリストを取得"""
    try:
        r = requests.get("https://defillama.com/airdrops", headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        for row in soup.select("table tr")[1:20]:
            cells = row.select("td")
            if len(cells) < 2:
                continue
            name_el = cells[0].select_one("a") or cells[0]
            name = name_el.get_text(strip=True)
            href = name_el.get("href", "") if name_el.name == "a" else ""
            if href and not href.startswith("http"):
                href = "https://defillama.com" + href
            items.append({
                "name": name,
                "url": href or "https://defillama.com/airdrops",
                "estimated_value": "不明",
                "end_date": "未定",
                "logo": "",
                "source": "defillama",
            })
        logger.info(f"DeFiLlama: {len(items)}件取得")
        return items
    except Exception as e:
        logger.warning(f"defillama scrape failed: {e}")
        return []


def _build_seed_airdrops() -> list[dict]:
    """注目エアドロップ curated データ (定期的に更新)"""
    today = datetime.utcnow()

    def days(n):
        return (today + timedelta(days=n)).strftime("%Y-%m-%d")

    return [
        {
            "id": "hyperliquid-hype",
            "name": "Hyperliquid (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "取引所トークン",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 2000,
            "description": "高速オンチェーン永久先物DEX。独自L1で動作。取引量によるポイント報酬が高額で注目度No.1。",
            "tasks": ["Hyperliquid上での先物取引", "取引量を積み上げる (毎日推奨)", "流動性提供 (HLP Vault)", "紹介プログラム参加"],
            "end_date": days(30),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
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
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 1500,
            "description": "EVM互換高速Layer1。テストネットが活発。早期参加者への大規模エアドロップが期待される最注目L1。",
            "tasks": ["テストネットに接続", "テストトークンをFaucetで入手", "DEXでスワップ実行", "NFTのMint実行", "Discordでロール取得"],
            "end_date": days(45),
            "logo": "https://assets.coingecko.com/coins/images/34183/small/monad.jpg",
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
            "type": "新規上場",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1200,
            "description": "Proof of Liquidity (PoL) を採用したEVM Layer1。BGT/HENEYトークンエコシステムで利回り獲得可能。",
            "tasks": ["BEXでスワップ", "BGTをステーキング", "Honey借入 (BEND)", "BeraChainのNFT参加"],
            "end_date": days(60),
            "logo": "https://assets.coingecko.com/coins/images/34535/small/bera.png",
            "url": "https://berachain.com/",
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
            "estimated_value_usd": 1000,
            "description": "Ethereumのリステーキングプロトコル。ETHをステーキングし追加報酬を獲得。AVS参加で報酬が増加。",
            "tasks": ["ETHをリステーキング (最低0.1ETH推奨)", "LST (stETH等) をデポジット", "AVSへの参加"],
            "end_date": days(120),
            "logo": "https://assets.coingecko.com/coins/images/33751/small/eigen.png",
            "url": "https://eigenlayer.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "megaeth-meth",
            "name": "MegaETH",
            "symbol": "METH",
            "category": "Layer2",
            "type": "テストネット",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 800,
            "description": "超高速EVM L2 (100,000 TPS目標)。テストネット活動中。early adopter向けエアドロップ確実視。",
            "tasks": ["パブリックテストネットに参加", "テストETHをFaucetで入手", "dAppsを利用 (スワップ・NFT Mint)", "Discordコミュニティ参加"],
            "end_date": days(40),
            "logo": "https://assets.coingecko.com/coins/images/52600/small/MegaETH.png",
            "url": "https://megaeth.systems/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "layerzero-zro",
            "name": "LayerZero (ZRO)",
            "symbol": "ZRO",
            "category": "インフラ",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 500,
            "description": "クロスチェーンメッセージングプロトコル。ブリッジ・DeFi利用者向けエアドロップ。継続的な利用が有効。",
            "tasks": ["Stargate経由でブリッジを実行", "複数チェーンでのトランザクション", "LayerZero対応dApps利用"],
            "end_date": days(60),
            "logo": "https://assets.coingecko.com/coins/images/28206/small/ftxG9_TJ_400x400.jpeg",
            "url": "https://layerzero.network/",
            "is_hot": False,
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
            "end_date": days(90),
            "logo": "https://assets.coingecko.com/coins/images/25734/small/scroll.png",
            "url": "https://scroll.io/",
            "is_hot": False,
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
            "description": "Matter Labsが開発するZK-Rollup。エコシステムが急拡大中。継続的な利用推奨。",
            "tasks": ["Era上でのスワップ", "Syncswap/Mute利用", "zkSync公式ブリッジ利用"],
            "end_date": days(45),
            "logo": "https://assets.coingecko.com/coins/images/38043/small/ZKTokenBlack.png",
            "url": "https://zksync.io/",
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
            "end_date": days(20),
            "logo": "https://assets.coingecko.com/coins/images/39619/small/MOVE_color.png",
            "url": "https://movementlabs.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
    ]


def fetch_all_airdrops() -> tuple[list[dict], list[str]]:
    """
    全ソースからエアドロップデータを収集。
    Returns: (airdrops_list, new_scraped_names)
    """
    curated = _build_seed_airdrops()
    scraped_io = _scrape_airdrops_io()
    scraped_defi = _scrape_defi_airdrops()
    scraped = scraped_io + scraped_defi

    seen_names = {a["name"].lower() for a in curated}
    new_items = []

    for s in scraped:
        name_lower = s["name"].lower().strip()
        if not name_lower or name_lower in seen_names:
            continue
        curated.append({
            "id": name_lower.replace(" ", "-").replace("/", "-")[:50],
            "name": s["name"],
            "symbol": "",
            "category": "その他",
            "type": "エアドロップ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": f"{s.get('source','Web')}より取得: {s.get('estimated_value', '')}",
            "tasks": [],
            "end_date": s.get("end_date", "未定"),
            "logo": s.get("logo", ""),
            "url": s.get("url", ""),
            "is_hot": False,
            "added_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "source": s.get("source", "web"),
        })
        new_items.append(s["name"])
        seen_names.add(name_lower)

    # ソート: is_hot → estimated_value_usd
    curated.sort(key=lambda x: (not x.get("is_hot"), -x.get("estimated_value_usd", 0)))

    return curated, new_items
