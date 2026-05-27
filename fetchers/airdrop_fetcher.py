"""
Airdrop情報をWeb/APIから収集するモジュール。
- airdrops.io スクレイピング
- CoinGeckoトレンド
- 2026年最新キュレーションデータ
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
        logger.info(f"airdrops.ioから{len(items)}件取得")
        return items
    except Exception as e:
        logger.warning(f"airdrops.io scrape failed: {e}")
        return []


def _scrape_airdropalert() -> list[dict]:
    """airdropalert.comからエアドロップ情報を取得 (補助ソース)"""
    try:
        r = requests.get("https://airdropalert.com/", headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        for card in soup.select(".airdrop-card, .airdrop-item, article")[:20]:
            name_el = card.select_one("h2, h3, .title, .airdrop-name")
            link_el = card.select_one("a[href]")
            if not name_el:
                continue
            href = link_el["href"] if link_el else "https://airdropalert.com/"
            if not href.startswith("http"):
                href = "https://airdropalert.com" + href
            items.append({
                "name": name_el.get_text(strip=True),
                "url": href,
                "estimated_value": "不明",
                "end_date": "未定",
                "logo": "",
                "source": "airdropalert",
            })
        logger.info(f"airdropalert.comから{len(items)}件取得")
        return items
    except Exception as e:
        logger.warning(f"airdropalert.com scrape failed: {e}")
        return []


def _build_seed_airdrops() -> list[dict]:
    """
    2026年最新注目エアドロップのキュレーションデータ。
    定期的に更新される手動管理リスト。
    """
    today = datetime.utcnow()

    return [
        # ===== Layer 2 / ZK Rollups =====
        {
            "id": "monad-mon",
            "name": "Monad (MON)",
            "symbol": "MON",
            "category": "Layer1/EVM",
            "type": "テストネット/メインネット",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 2000,
            "description": "超高速EVM互換Layer1。10,000 TPS達成、Ethereumとの完全互換。テストネット参加者へのエアドロップ期待大。",
            "tasks": [
                "Monadテストネットでトランザクション実行",
                "公式Discordコミュニティ参加",
                "テストネットDAppsの利用 (DEX/レンディング)",
                "週次アクティビティの維持",
            ],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/32188/small/monad.png",
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
            "type": "テストネット",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 1500,
            "description": "リアルタイムEVM。最大100,000 TPSを実現するEthereum L2。テストネット公開中で参加者が増加中。",
            "tasks": [
                "MegaETHテストネットへの参加",
                "テストトークンを使ったDeFi操作",
                "コミュニティクエスト完了",
                "NFTミント参加",
            ],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39870/small/megaeth.png",
            "url": "https://megaeth.systems/",
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
            "estimated_value_usd": 300,
            "description": "Matter Labsが開発するZK-Rollup。エコシステムが急拡大中。継続的なトランザクションで追加報酬の可能性。",
            "tasks": [
                "zkSync Era上でのスワップ",
                "Syncswap/Mute/Velocore利用",
                "zkSync公式ブリッジ利用",
                "Era上でのNFT取引",
            ],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/38043/small/ZKTokenBlack.png",
            "url": "https://zksync.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },

        # ===== AI + Blockchain =====
        {
            "id": "bittensor-tao",
            "name": "Bittensor エコシステム",
            "symbol": "TAO",
            "category": "AI/ML",
            "type": "サブネット報酬",
            "status": "active",
            "difficulty": "hard",
            "estimated_value_usd": 3000,
            "description": "分散型AIネットワーク。サブネットへの参加・マイニングで報酬獲得。2026年AI需要急増で注目度MAX。",
            "tasks": [
                "Bittensorバリデーター/マイナー参加",
                "サブネットへの貢献",
                "TAOステーキング",
                "AIモデルの提供",
            ],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/28452/small/ARUsPeNQ_400x400.jpeg",
            "url": "https://bittensor.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "aethir-ath",
            "name": "Aethir (ATH)",
            "symbol": "ATH",
            "category": "DePIN/AI",
            "type": "ノード運営",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1200,
            "description": "分散型GPU/クラウドコンピューティング。AIトレーニング用分散インフラ。チェッカーノード参加でトークン獲得。",
            "tasks": [
                "チェッカーノードの運営",
                "Aethirエコシステム利用",
                "コミュニティ貢献",
                "Discord検証完了",
            ],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/35529/small/Aethir-logomark-Full-colour-1.png",
            "url": "https://aethir.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },

        # ===== DePIN =====
        {
            "id": "io-net-io",
            "name": "io.net (IO)",
            "symbol": "IO",
            "category": "DePIN",
            "type": "GPU分散ネットワーク",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "Solana上の分散型GPUネットワーク。ML/AIワークロードを分散処理。IOGENポイントを貯めてIOトークン獲得。",
            "tasks": [
                "GPUワーカーとして参加",
                "io.netアプリダウンロード",
                "ポイントプログラム参加",
                "紹介プログラム活用",
            ],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/36073/small/io.png",
            "url": "https://io.net/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },

        # ===== DeFi =====
        {
            "id": "hyperliquid-hype",
            "name": "Hyperliquid (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "取引所トークン",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 2500,
            "description": "高速オンチェーン永久先物DEX。HyperEVM上での新規プロジェクトが続々登場。取引量でポイント獲得。",
            "tasks": [
                "Hyperliquid上での先物取引",
                "HyperEVMプロジェクトへの参加",
                "流動性提供 (HLP)",
                "新規上場トークンの取引",
            ],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
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
            "estimated_value_usd": 1000,
            "description": "Ethereumのリステーキングプロトコル。AVSエコシステムが拡大中。ステーキング量でシーズン2報酬獲得。",
            "tasks": [
                "ETHまたはLSTをリステーキング",
                "AVSへのオペレーター参加",
                "シーズン2ポイント蓄積",
                "EigenDAへの貢献",
            ],
            "end_date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/33751/small/eigen.png",
            "url": "https://eigenlayer.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },

        # ===== Modular Blockchain =====
        {
            "id": "celestia-tia",
            "name": "Celestia (TIA)",
            "symbol": "TIA",
            "category": "モジュラー",
            "type": "ステーキング報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 500,
            "description": "モジュラーブロックチェーンのパイオニア。TIAステーキングでエコシステムプロジェクトからのエアドロップ獲得。",
            "tasks": [
                "TIAをステーキング (最低1TIA)",
                "バリデーターへの委任",
                "Celestiaエコシステムプロジェクト利用",
                "Mocha/Arabicaテストネット参加",
            ],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/31967/small/tia.jpg",
            "url": "https://celestia.org/",
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
            "estimated_value_usd": 600,
            "description": "Move VMを使用するEthereum L2。メインネット稼働中。エコシステムDApps利用でシーズン2報酬期待。",
            "tasks": [
                "Movement上でのDeFi活動",
                "公式ブリッジでのブリッジ",
                "コミュニティクエスト",
                "Movement NFTミント",
            ],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39619/small/MOVE_color.png",
            "url": "https://movementlabs.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "story-protocol-ip",
            "name": "Story Protocol (IP)",
            "symbol": "IP",
            "category": "IP/NFT",
            "type": "クリエイター報酬",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 800,
            "description": "IP (知的財産) のブロックチェーン化。クリエイターがIPをオンチェーン登録しライセンス収益を得られる。",
            "tasks": [
                "Story上でIPアセット登録",
                "ライセンスの設定・取引",
                "バリデーターへのステーキング",
                "Odysseyテストネット参加",
            ],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39622/small/story.png",
            "url": "https://www.story.foundation/",
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
            "description": "EVM互換ZK-Rollup。Scroll Sessions ポイントプログラムで継続的な報酬。DeFi利用で乗数ボーナス。",
            "tasks": [
                "ScrollネットワークへETHブリッジ",
                "Scroll上でのDeFi利用",
                "Sessions Marks収集",
                "複数週にわたるアクティビティ維持",
            ],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/25734/small/scroll.png",
            "url": "https://scroll.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "layerzero-zro",
            "name": "LayerZero シーズン2",
            "symbol": "ZRO",
            "category": "インフラ",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 400,
            "description": "クロスチェーンメッセージングプロトコル。シーズン2のポイントプログラムが稼働中。継続的なブリッジ利用が重要。",
            "tasks": [
                "Stargate経由でブリッジを実行",
                "複数チェーンでのトランザクション",
                "LayerZero対応dApps利用",
                "流動性提供でブースト獲得",
            ],
            "end_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/28206/small/ftxG9_TJ_400x400.jpeg",
            "url": "https://layerzero.network/",
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
    scraped_io = _scrape_airdrops_io()
    scraped_alert = _scrape_airdropalert()
    scraped = scraped_io + scraped_alert

    seen_names = {a["name"].lower() for a in curated}
    new_items = []

    for s in scraped:
        name_lower = s["name"].lower()
        # 短すぎる名前や重複をスキップ
        if len(s["name"]) < 3 or name_lower in seen_names:
            continue

        curated.append({
            "id": s["name"].lower().replace(" ", "-").replace("/", "-")[:50],
            "name": s["name"],
            "symbol": "",
            "category": "その他",
            "type": "エアドロップ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 0,
            "description": f"外部ソース ({s.get('source', '不明')}) より取得: {s.get('estimated_value', '')}",
            "tasks": [],
            "end_date": s.get("end_date", "未定"),
            "logo": s.get("logo", ""),
            "url": s.get("url", ""),
            "is_hot": False,
            "added_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "source": s.get("source", "scraped"),
        })
        new_items.append(s["name"])
        seen_names.add(name_lower)

    # 注目度でソート: is_hot → estimated_value_usd
    curated.sort(key=lambda x: (not x.get("is_hot"), -x.get("estimated_value_usd", 0)))

    logger.info(f"合計 {len(curated)} 件のエアドロップを取得 (新規スクレイプ: {len(new_items)} 件)")
    return curated, new_items
