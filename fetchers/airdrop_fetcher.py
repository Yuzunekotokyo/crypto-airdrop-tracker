"""
Airdrop情報をWeb/APIから収集するモジュール。
airdrops.ioのパブリックページとCoinGeckoトレンドを組み合わせて使用。
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


def _scrape_coingecko_new_airdrops() -> list[dict]:
    """CoinGeckoの新着コインからエアドロップ候補を取得"""
    try:
        new_coins = get_new_coins()
        items = []
        for coin in new_coins[:10]:
            name = coin.get("name", "")
            symbol = coin.get("symbol", "").upper()
            coin_id = coin.get("id", "")
            if name:
                items.append({
                    "name": f"{name} ({symbol})" if symbol else name,
                    "url": f"https://www.coingecko.com/en/coins/{coin_id}",
                    "estimated_value": "未定",
                    "end_date": "未定",
                    "logo": coin.get("thumb", ""),
                    "source": "coingecko-new",
                })
        return items
    except Exception as e:
        logger.warning(f"CoinGecko new coins fetch failed: {e}")
        return []


def _build_seed_airdrops() -> list[dict]:
    """注目エアドロップのキュレーションデータ"""
    today = datetime.utcnow()

    return [
        # ===== Layer 2 / インフラ =====
        {
            "id": "berachain-bera",
            "name": "Berachain (BERA)",
            "symbol": "BERA",
            "category": "Layer1",
            "type": "流動性マイニング",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "EVM互換Layer1。独自のProof-of-Liquidity合意メカニズム。DeFiエコシステムが急成長中。BGTトークンを積み重ねてエアドロップを獲得。",
            "tasks": [
                "Berachain上でBEX (DEX) を使いスワップ",
                "Honey (ステーブルコイン) をミント",
                "流動性プールに参加してBGTを獲得",
                "BeadleでNFT活動",
            ],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/34049/small/bera.png",
            "url": "https://berachain.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "monad-mon",
            "name": "Monad",
            "symbol": "MON",
            "category": "Layer1",
            "type": "テストネット報酬",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 1200,
            "description": "EVM互換の高性能Layer1。毎秒10,000TPS達成。テストネット参加者へのエアドロップ予定。コミュニティ活動が重要。",
            "tasks": [
                "Monadテストネットでトランザクション実行",
                "公式Discord/Telegramに参加",
                "テストネットNFTをミント",
                "MonadエコシステムdApps利用",
            ],
            "end_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/35272/small/monad.jpg",
            "url": "https://monad.xyz/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "megaeth-meth",
            "name": "MegaETH",
            "symbol": "METH",
            "category": "Layer2",
            "type": "テストネット報酬",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 600,
            "description": "リアルタイムEthereum L2。1ミリ秒のブロック時間と100,000+ TPSを実現。テストネット参加者向けエアドロップ予定。",
            "tasks": [
                "MegaETHテストネットに参加",
                "テストネット上でDeFi操作",
                "コミュニティタスク完了",
            ],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/38744/small/megaeth.jpg",
            "url": "https://megaeth.systems/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "story-ip",
            "name": "Story Protocol (IP)",
            "symbol": "IP",
            "category": "インフラ",
            "type": "エコシステム報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 500,
            "description": "IPをオンチェーンで管理・ライセンスするための専用L1。クリエイター・コンテンツ保有者向け報酬あり。",
            "tasks": [
                "IPアセットを登録してNFTをミント",
                "ライセンストークンの発行・取引",
                "コミュニティ貢献タスク",
                "Story上のdAppsを利用",
            ],
            "end_date": (today + timedelta(days=75)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39159/small/story.jpg",
            "url": "https://www.story.foundation/",
            "is_hot": True,
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
            "estimated_value_usd": 1500,
            "description": "高速オンチェーン永久先物DEX。独自L1チェーン上で動作。取引量によるポイント報酬が継続中。",
            "tasks": [
                "Hyperliquid上での先物取引",
                "流動性提供 (HLP Vault)",
                "紹介プログラム参加",
                "新規上場トークンの早期取引",
            ],
            "end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
            "is_hot": True,
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
            "estimated_value_usd": 300,
            "description": "旧Fantom。10,000 TPS超の高速EVM L1。Sonicポイントプログラムでアクティブユーザーに報酬。",
            "tasks": [
                "Sonic上のDeFiプロトコル利用",
                "流動性提供",
                "Sonicエコシステム参加",
            ],
            "end_date": (today + timedelta(days=50)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39428/small/sonic.jpg",
            "url": "https://www.soniclabs.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "plume-plume",
            "name": "Plume Network (PLUME)",
            "symbol": "PLUME",
            "category": "RWA",
            "type": "テストネット報酬",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 400,
            "description": "RWA (現実資産) 特化のL2。不動産・商品・プライベートクレジット等をトークン化。テストネット参加者向けエアドロップ予定。",
            "tasks": [
                "Plumeテストネットに参加",
                "RWAトークンをテストネット上で取引",
                "コミュニティタスク完了",
            ],
            "end_date": (today + timedelta(days=40)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/40591/small/plume.jpg",
            "url": "https://plumenetwork.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "symbiotic-sym",
            "name": "Symbiotic",
            "symbol": "SYM",
            "category": "インフラ",
            "type": "リステーキング",
            "status": "active",
            "difficulty": "hard",
            "estimated_value_usd": 600,
            "description": "マルチアセット・マルチネットワーク対応リステーキングプロトコル。EigenLayerの競合。多様なアセットのリステーキングが可能。",
            "tasks": [
                "wstETH/wBTC等をSymbioticにデポジット",
                "Vaultへの参加",
                "ネットワーク統合プロジェクト利用",
            ],
            "end_date": (today + timedelta(days=80)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/40027/small/symbiotic.jpg",
            "url": "https://symbiotic.fi/",
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
            "estimated_value_usd": 700,
            "description": "Ethereumのリステーキングプロトコル。ETHをステーキングし追加報酬を獲得。EIGEN第2フェーズのステーキング報酬が継続中。",
            "tasks": [
                "ETHをリステーキング",
                "LST (stETH/rETH等) をデポジット",
                "AVSへの参加・委任",
            ],
            "end_date": (today + timedelta(days=100)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/33751/small/eigen.png",
            "url": "https://eigenlayer.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "humanity-rh",
            "name": "Humanity Protocol (RH)",
            "symbol": "RH",
            "category": "SocialFi",
            "type": "Proof-of-Humanity",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 350,
            "description": "掌紋認証によるProof-of-Humanityプロトコル。1人1アカウントを保証。人間認証者へのエアドロップ予定。",
            "tasks": [
                "掌紋認証でHumanity IDを取得",
                "テストネットに参加",
                "コミュニティタスク完了",
            ],
            "end_date": (today + timedelta(days=55)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/38618/small/humanity.jpg",
            "url": "https://humanity.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "scroll-scr",
            "name": "Scroll (SCR)",
            "symbol": "SCR",
            "category": "Layer2",
            "type": "レトロアクティブ継続",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 250,
            "description": "EVM互換ZK-Rollup。第2弾エアドロップ継続中。Scroll上でのDeFi活動でScroll Marksを獲得。",
            "tasks": [
                "ScrollネットワークへETHブリッジ",
                "Scroll上でのDeFi利用 (Aave, Uniswap等)",
                "継続的なアクティビティ維持",
            ],
            "end_date": (today + timedelta(days=70)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/25734/small/scroll.png",
            "url": "https://scroll.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "nillion-nil",
            "name": "Nillion (NIL)",
            "symbol": "NIL",
            "category": "インフラ",
            "type": "プライバシー計算",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 450,
            "description": "分散型プライバシー計算ネットワーク。機密データの処理を可能にするMPC技術。テストネット参加者への報酬あり。",
            "tasks": [
                "Nillion testnetに参加",
                "SecretVaultにデータを保存",
                "開発者タスクに挑戦",
            ],
            "end_date": (today + timedelta(days=65)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39635/small/nillion.jpg",
            "url": "https://nillion.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "movement-move",
            "name": "Movement (MOVE)",
            "symbol": "MOVE",
            "category": "Layer2",
            "type": "エコシステム報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 300,
            "description": "Move VMを使用するEthereum L2。高速・低コストトランザクション。エコシステム拡大中。",
            "tasks": [
                "Movement上でのDeFi利用",
                "ブリッジ経由でアセット移動",
                "コミュニティ参加",
            ],
            "end_date": (today + timedelta(days=20)).strftime("%Y-%m-%d"),
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
    scraped_web = _scrape_airdrops_io()
    scraped_cg = _scrape_coingecko_new_airdrops()
    scraped = scraped_web + scraped_cg

    seen_names = {a["name"].lower() for a in curated}
    # シンボルなし版も登録 (e.g. "Berachain" matches "Berachain (BERA)")
    for a in curated:
        base = a["name"].split(" (")[0].lower()
        seen_names.add(base)

    new_items = []

    for s in scraped:
        raw_name = s["name"]
        base_name = raw_name.split(" (")[0].lower()
        if raw_name.lower() not in seen_names and base_name not in seen_names:
            curated.append({
                "id": raw_name.lower().replace(" ", "-")[:40],
                "name": raw_name,
                "symbol": "",
                "category": "その他",
                "type": "エアドロップ",
                "status": "active",
                "difficulty": "easy",
                "estimated_value_usd": 0,
                "description": f"{s.get('source','web')}より取得: {s.get('estimated_value', '')}",
                "tasks": [],
                "end_date": s.get("end_date", "未定"),
                "logo": s.get("logo", ""),
                "url": s.get("url", ""),
                "is_hot": False,
                "added_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "source": s.get("source", "web"),
            })
            new_items.append(raw_name)
            seen_names.add(raw_name.lower())
            seen_names.add(base_name)

    # 注目度でソート: is_hot → estimated_value_usd
    curated.sort(key=lambda x: (not x.get("is_hot"), -x.get("estimated_value_usd", 0)))

    return curated, new_items
