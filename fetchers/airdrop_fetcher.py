"""
Airdrop情報をWeb/APIから収集するモジュール。
複数ソース: curated手動データ + airdrops.io スクレイピング + CoinGecko新着コイン
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
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

AIRDROP_KEYWORDS = [
    "airdrop", "drop", "claim", "reward", "incentive", "retroactive",
    "testnet", "points", "season", "epoch", "allocation",
]


def _scrape_airdrops_io() -> list[dict]:
    """airdrops.ioのトップページからアクティブエアドロップを取得"""
    try:
        r = requests.get("https://airdrops.io/", headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        items = []
        # 複数のCSSセレクタパターンを試す
        cards = (
            soup.select(".hot-airdrop-item")
            or soup.select(".airdrop-item")
            or soup.select("article.airdrop")
            or soup.select(".card-airdrop")
        )

        for card in cards[:20]:
            name_el = (
                card.select_one(".airdrop-name")
                or card.select_one(".title")
                or card.select_one("h2")
                or card.select_one("h3")
            )
            link_el = card.select_one("a[href]")
            value_el = (
                card.select_one(".worth")
                or card.select_one(".value")
                or card.select_one(".airdrop-value")
            )
            end_el = (
                card.select_one(".end-date")
                or card.select_one(".date")
                or card.select_one(".airdrop-end")
            )
            img_el = card.select_one("img")

            if not name_el:
                continue

            name = name_el.get_text(strip=True)
            url = link_el.get("href", "https://airdrops.io/") if link_el else "https://airdrops.io/"
            if url.startswith("/"):
                url = "https://airdrops.io" + url

            items.append({
                "name": name,
                "url": url,
                "estimated_value": value_el.get_text(strip=True) if value_el else "不明",
                "end_date": end_el.get_text(strip=True) if end_el else "未定",
                "logo": img_el.get("src", "") if img_el else "",
                "source": "airdrops.io",
            })

        if not items:
            # フォールバック: より広いセレクタ
            for card in soup.select("article, .card, .item")[:15]:
                link = card.select_one("a[href*='airdrops.io']") or card.select_one("a[href]")
                title = card.select_one("h2, h3, h4, .title, .name")
                if title and link:
                    items.append({
                        "name": title.get_text(strip=True),
                        "url": link.get("href", "https://airdrops.io/"),
                        "estimated_value": "不明",
                        "end_date": "未定",
                        "logo": "",
                        "source": "airdrops.io",
                    })

        logger.info(f"airdrops.io から {len(items)} 件取得")
        return items
    except Exception as e:
        logger.warning(f"airdrops.io scrape failed: {e}")
        return []


def _scrape_airdrop_alert() -> list[dict]:
    """airdrop-alert.com からのスクレイピング"""
    try:
        r = requests.get("https://airdrop-alert.com/best-airdrops/", headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        items = []
        for card in soup.select(".airdrop-post, article, .post")[:15]:
            title_el = card.select_one("h2, h3, .entry-title, .post-title")
            link_el = card.select_one("a[href]")
            img_el = card.select_one("img")

            if not title_el:
                continue

            name = title_el.get_text(strip=True)
            url = link_el.get("href", "") if link_el else ""
            if not url or not name:
                continue

            items.append({
                "name": name,
                "url": url,
                "estimated_value": "不明",
                "end_date": "未定",
                "logo": img_el.get("src", "") if img_el else "",
                "source": "airdrop-alert.com",
            })

        logger.info(f"airdrop-alert.com から {len(items)} 件取得")
        return items
    except Exception as e:
        logger.warning(f"airdrop-alert.com scrape failed: {e}")
        return []


def _new_coins_as_airdrops() -> list[dict]:
    """CoinGecko新着コインのうちエアドロップ関連と思われるものを抽出"""
    new_coins = get_new_coins()
    airdrops = []
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    for coin in new_coins[:20]:
        name = coin.get("name", "")
        symbol = coin.get("symbol", "").upper()
        coin_id = coin.get("id", "")

        if not name or len(name) < 2:
            continue

        # エアドロップ関連キーワードを名前・symbolで判定
        name_lower = name.lower()
        is_airdrop_like = any(k in name_lower for k in AIRDROP_KEYWORDS)

        if is_airdrop_like or True:  # 新着全件を候補として追加
            airdrops.append({
                "id": f"cg-new-{coin_id}",
                "name": name,
                "symbol": symbol,
                "category": "新着コイン",
                "type": "エアドロップ候補",
                "status": "active",
                "difficulty": "easy",
                "estimated_value_usd": 0,
                "description": f"CoinGeckoに新規上場した注目コイン。エアドロップの可能性あり。",
                "tasks": ["公式サイト確認", "Discordコミュニティ参加", "テストネット参加"],
                "end_date": (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "logo": "",
                "url": f"https://www.coingecko.com/en/coins/{coin_id}",
                "is_hot": False,
                "added_date": today_str,
                "source": "coingecko-new",
            })

    return airdrops[:5]  # 最大5件


def _build_seed_airdrops() -> list[dict]:
    """手動管理の注目エアドロップシードデータ — 2026年最新版"""
    today = datetime.utcnow()

    def future(days):
        return (today + timedelta(days=days)).strftime("%Y-%m-%d")

    return [
        {
            "id": "monad-mon",
            "name": "Monad (MON)",
            "symbol": "MON",
            "category": "Layer1",
            "type": "テストネット報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 2000,
            "description": "高性能EVM互換L1。月1億tx以上を目標とする次世代ブロックチェーン。テストネット参加者に大規模エアドロップ予定。",
            "tasks": [
                "Monadテストネット参加",
                "テストnet上でのトランザクション実行",
                "Discordコミュニティ参加 + 役割取得",
                "バリデータノード運用 (任意)",
            ],
            "end_date": future(90),
            "logo": "https://assets.coingecko.com/coins/images/34688/small/monad.png",
            "url": "https://www.monad.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "berachain-bera",
            "name": "Berachain (BERA)",
            "symbol": "BERA",
            "category": "Layer1",
            "type": "PoL報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1500,
            "description": "Proof-of-Liquidity (PoL) を採用した独自L1。流動性提供でBGT/BERAトークンを獲得可能。",
            "tasks": [
                "Berachain mainnetへの流動性提供",
                "BGTトークンの獲得と管理",
                "BEX/Beraswapでのスワップ",
                "Honeyコインのmint",
            ],
            "end_date": future(60),
            "logo": "https://assets.coingecko.com/coins/images/35498/small/BERA.png",
            "url": "https://www.berachain.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "megaeth-l2",
            "name": "MegaETH",
            "symbol": "MEGA",
            "category": "Layer2",
            "type": "テストネット報酬",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 1200,
            "description": "100,000 TPS超えを目標とするEthereum L2。リアルタイムブロックチェーン。テストネット参加者向け大規模エアドロップ予定。",
            "tasks": [
                "MegaETHテストネット参加",
                "公式Faucetからテストトークン取得",
                "テストnetでのDApp利用",
                "コミュニティイベント参加",
            ],
            "end_date": future(45),
            "logo": "",
            "url": "https://www.megaeth.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-hype",
            "name": "Hyperliquid (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "取引報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1000,
            "description": "高速オンチェーン永久先物DEX。独自HyperEVM L1チェーン上で動作。取引量によるポイント報酬継続中。",
            "tasks": [
                "Hyperliquid上での先物・スポット取引",
                "流動性提供 (HLP Vault)",
                "紹介プログラム参加",
                "HyperEVMエコシステム利用",
            ],
            "end_date": future(30),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "fuel-network",
            "name": "Fuel Network",
            "symbol": "FUEL",
            "category": "Layer2",
            "type": "テストネット報酬",
            "status": "active",
            "difficulty": "hard",
            "estimated_value_usd": 800,
            "description": "UTXO型アーキテクチャを採用した高性能Ethereum L2。独自VMでスマートコントラクトを並列実行。",
            "tasks": [
                "Fuel testnetでのDeploy/利用",
                "Swayプログラミング言語学習",
                "Fuelエコシステムプロジェクト利用",
                "コントリビューション (Issue/PR)",
            ],
            "end_date": future(75),
            "logo": "",
            "url": "https://fuel.network/",
            "is_hot": False,
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
            "description": "クロスチェーンメッセージングプロトコル。シーズン2のポイントプログラムが進行中。",
            "tasks": [
                "Stargate経由でブリッジを実行",
                "複数チェーンでのトランザクション",
                "LayerZero対応dApps利用",
                "ポイントプログラム参加",
            ],
            "end_date": future(50),
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
            "description": "EVM互換ZK-Rollup。Scroll Marks (ポイント) の第2ラウンドが進行中。",
            "tasks": [
                "ScrollネットワークへETHブリッジ",
                "Scroll上でのDeFi利用 (Ambient, Aave等)",
                "複数週にわたるアクティビティ継続",
            ],
            "end_date": future(60),
            "logo": "https://assets.coingecko.com/coins/images/25734/small/scroll.png",
            "url": "https://scroll.io/",
            "is_hot": False,
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
            "description": "Ethereumのリステーキングプロトコル。AVSエコシステムが拡大中、継続的なステーキング報酬あり。",
            "tasks": [
                "ETHをリステーキング",
                "LST (stETH/rETH等) をデポジット",
                "AVSへの参加",
                "EigenDA利用プロジェクトを使う",
            ],
            "end_date": future(120),
            "logo": "https://assets.coingecko.com/coins/images/33751/small/eigen.png",
            "url": "https://eigenlayer.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "sonic-s",
            "name": "Sonic (S)",
            "symbol": "S",
            "category": "Layer1",
            "type": "エコシステム報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "旧Fantom後継の高速EVM L1。Sonic Gemsプログラムによるアクティビティ報酬。",
            "tasks": [
                "Sonicネットワーク上でのDeFi利用",
                "Gems獲得のための継続的アクティビティ",
                "Soniclabs生態系プロジェクトの利用",
            ],
            "end_date": future(40),
            "logo": "",
            "url": "https://soniclabs.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "movement-move",
            "name": "Movement (MOVE)",
            "symbol": "MOVE",
            "category": "Layer2",
            "type": "新規上場",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 350,
            "description": "Move VMを使用するEthereum L2。MoveVM独自の安全性とEVM互換性を持つ。",
            "tasks": [
                "Movementネットワーク利用",
                "Discordコミュニティ参加",
                "エコシステムDApp利用",
            ],
            "end_date": future(20),
            "logo": "https://assets.coingecko.com/coins/images/39619/small/MOVE_color.png",
            "url": "https://movementlabs.xyz/",
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
    seen_names = {a["name"].lower(): a for a in curated}
    new_items = []
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    # airdrops.io スクレイピング
    for s in _scrape_airdrops_io():
        name_lower = s["name"].lower()
        if name_lower not in seen_names and len(s["name"]) > 2:
            entry = {
                "id": s["name"].lower().replace(" ", "-"),
                "name": s["name"],
                "symbol": "",
                "category": "その他",
                "type": "エアドロップ",
                "status": "active",
                "difficulty": "easy",
                "estimated_value_usd": _parse_value(s.get("estimated_value", "")),
                "description": f"airdrops.ioより取得。推定価値: {s.get('estimated_value', '不明')}",
                "tasks": ["公式サイトを確認して参加手順に従う"],
                "end_date": s.get("end_date", "未定"),
                "logo": s.get("logo", ""),
                "url": s.get("url", ""),
                "is_hot": False,
                "added_date": today_str,
                "source": "airdrops.io",
            }
            curated.append(entry)
            new_items.append(s["name"])
            seen_names[name_lower] = entry

    # airdrop-alert.com スクレイピング
    for s in _scrape_airdrop_alert():
        name_lower = s["name"].lower()
        if name_lower not in seen_names and len(s["name"]) > 2:
            entry = {
                "id": s["name"].lower().replace(" ", "-") + "-alert",
                "name": s["name"],
                "symbol": "",
                "category": "その他",
                "type": "エアドロップ",
                "status": "active",
                "difficulty": "easy",
                "estimated_value_usd": 0,
                "description": "airdrop-alert.comより取得。詳細は公式サイトを確認してください。",
                "tasks": ["公式サイトを確認して参加手順に従う"],
                "end_date": "未定",
                "logo": s.get("logo", ""),
                "url": s.get("url", ""),
                "is_hot": False,
                "added_date": today_str,
                "source": "airdrop-alert.com",
            }
            curated.append(entry)
            new_items.append(s["name"])
            seen_names[name_lower] = entry

    # CoinGecko新着コインを追加（エアドロップ候補）
    for coin in _new_coins_as_airdrops():
        name_lower = coin["name"].lower()
        if name_lower not in seen_names:
            curated.append(coin)
            seen_names[name_lower] = coin
            # 新着コインは new_items に追加しない (ノイズが多い)

    # ソート: is_hot → estimated_value_usd
    curated.sort(key=lambda x: (not x.get("is_hot"), -x.get("estimated_value_usd", 0)))

    logger.info(f"合計 {len(curated)} 件のエアドロップ情報を収集 (新着: {len(new_items)} 件)")
    return curated, new_items


def _parse_value(value_str: str) -> int:
    """'$500' や '500 USD' などの文字列から数値を取得"""
    import re
    if not value_str:
        return 0
    nums = re.findall(r"[\d,]+", value_str.replace(",", ""))
    if nums:
        try:
            return int(nums[0])
        except ValueError:
            pass
    return 0
