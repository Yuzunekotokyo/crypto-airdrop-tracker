"""
Airdrop情報をWeb/APIから収集するモジュール。
airdrops.ioのパブリックページとCoinGeckoトレンドを組み合わせて使用。
シードデータは2026年6月時点の最新情報に更新済み。
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
        # 複数セレクタで幅広くカードを取得
        selectors = [".airdrop-item", ".airdrop-card", "article.airdrop", ".col-airdrop"]
        cards = []
        for sel in selectors:
            found = soup.select(sel)
            if found:
                cards = found[:30]
                break

        for card in cards:
            name_el = (
                card.select_one(".airdrop-title")
                or card.select_one("h3")
                or card.select_one("h2")
            )
            link_el = card.select_one("a[href]")
            value_el = (
                card.select_one(".airdrop-value")
                or card.select_one(".value")
                or card.select_one("[class*='worth']")
            )
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


def _scrape_cryptorank() -> list[dict]:
    """cryptorank.ioのエアドロップページからデータを補完取得"""
    try:
        r = requests.get(
            "https://cryptorank.io/drophunting",
            headers=HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        items = []
        for card in soup.select("[class*='airdrop']")[:20]:
            name_el = card.select_one("h3") or card.select_one("[class*='name']")
            link_el = card.select_one("a[href]")
            if not name_el:
                continue
            items.append({
                "name": name_el.get_text(strip=True),
                "url": link_el["href"] if link_el else "https://cryptorank.io/drophunting",
                "estimated_value": "不明",
                "end_date": "未定",
                "logo": "",
                "source": "cryptorank.io",
            })
        return items
    except Exception as e:
        logger.warning(f"cryptorank.io scrape failed: {e}")
        return []


def _build_seed_airdrops() -> list[dict]:
    """
    2026年6月時点のキュレート済み注目エアドロップシードデータ。
    情報源: airdrops.io, CoinGecko, CryptoNews, KuCoin Blog (2026年6月調査)
    """
    today = datetime.utcnow()
    return [
        # ===== 超注目 (HOT) =====
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "ウォレット",
            "type": "MetaMask Rewards",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 2000,
            "description": (
                "3000万人以上が使うNo.1 EVMウォレット。MetaMask Rewardsでスワップ・"
                "ブリッジ・エコシステム利用によりMASKトークンが貯まる仕組みが進行中。"
                "正式TGEは未定だが業界最大の潜在的エアドロップとして注目度No.1。"
            ),
            "tasks": [
                "MetaMask Swapsでトークンスワップを実行",
                "MetaMask Bridgeでクロスチェーンブリッジ",
                "MetaMask Benefitsタブでポイント確認・特典を請求",
                "Ethereum/Base/Linea/Arbitrumでのアクティビティ継続",
                "MetaMask公式SNSをフォロー・エンゲージ",
            ],
            "end_date": "未定 (TGE待ち)",
            "logo": "https://assets.coingecko.com/coins/images/9892/small/Image_Icon_FOX.png",
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
            "type": "プラットフォームトークン",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 1500,
            "description": (
                "評価額90億ドルの分散型予測市場。2026年下半期にPOLYトークン発行予定"
                "($750M規模のエアドロッププログラム計画)。Polygonネットワーク上で動作。"
                "スポーツ・政治・クリプトイベントの予測取引でポイント獲得中。"
            ),
            "tasks": [
                "Polymarketアカウントを作成 (KYC不要)",
                "Polygonネットワークに資金追加",
                "複数の予測市場でポジションを取る",
                "X(Twitter)アカウントをプロフィールにリンク",
                "継続的な取引活動 (月次スナップショット可能性)",
            ],
            "end_date": "2026-12-31",
            "logo": "https://assets.coingecko.com/coins/images/31600/small/polymarket.png",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "megaeth-mega",
            "name": "MegaETH (MEGA)",
            "symbol": "MEGA",
            "category": "Layer2",
            "type": "メインネット移行",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1200,
            "description": (
                "2026年2月9日にメインネット稼働開始の超高スループットL2。"
                "公開セールで4億5000万ドル調達。Fluffle NFTホルダーに最低5%のMEGA配布が確定。"
                "メインネット上でのアクティビティが配分を左右する可能性大。"
            ),
            "tasks": [
                "MegaETHメインネットにETHブリッジ",
                "MegaETH上のDEXでスワップ実行",
                "MegaETHエコシステムのdApps利用",
                "The Fluffle NFT保有 (確定報酬あり)",
                "Discordコミュニティへの参加・貢献",
            ],
            "end_date": "2026-09-30",
            "logo": "https://assets.coingecko.com/coins/images/53178/small/megaeth.png",
            "url": "https://megaeth.systems/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "opensea-sea",
            "name": "OpenSea (SEA)",
            "symbol": "SEA",
            "category": "NFT",
            "type": "プラットフォームトークン",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 800,
            "description": (
                "世界最大のNFTマーケットプレイス。コミュニティへ50%配分を確定発表。"
                "2025年2月にSEAトークンを確認、2026年Q1予定が3月に延期。新TGE日程は未定。"
                "過去の取引履歴・OpenSea Pro利用実績が対象になる可能性。"
            ),
            "tasks": [
                "OpenSeaでNFTを購入または出品",
                "OpenSea Pro (Gem) でアグリゲーター利用",
                "複数コレクションの取引実績を作る",
                "OpenSeaのSNSアカウントをフォロー",
                "ウォレットをOpenSeaに接続・プロフィール設定",
            ],
            "end_date": "未定 (再スケジュール中)",
            "logo": "https://assets.coingecko.com/coins/images/12465/small/os.png",
            "url": "https://opensea.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-coinbase",
            "name": "Base (Coinbase L2)",
            "symbol": "BASE",
            "category": "Layer2",
            "type": "エコシステムトークン",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 600,
            "description": (
                "Coinbaseが運営するOP Stack L2。Baseトークン発行の可能性について"
                "市場で強く期待されている。Baseエコシステムでの継続的なアクティビティが"
                "将来の配分に影響する可能性。現在3億人以上のCoinbaseユーザー基盤が強み。"
            ),
            "tasks": [
                "Baseメインネットにブリッジ",
                "Aerodrome / BaseSwapなどBaseのDeFiを利用",
                "Base上のNFTを購入・ミント",
                "Base上でのゲーム・SocialFiアプリ利用",
                "Coinbase Walletをアクティブに使用",
            ],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/asset_platforms/images/131/small/base.jpeg",
            "url": "https://base.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        # ===== 継続参加型 =====
        {
            "id": "espresso-esp",
            "name": "Espresso (ESP)",
            "symbol": "ESP",
            "category": "インフラ",
            "type": "モジュラーブロックチェーン",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 500,
            "description": (
                "L2トランザクションを高速・安全・シームレスにするモジュラーインフラ。"
                "ESPトークンのエアドロップを計画中。a16zなどVCからの大型調達あり。"
                "テストネット参加者・インテグレーター向けに配分予定。"
            ),
            "tasks": [
                "Espressoテストネットへの参加",
                "Espressoを利用したL2でのトランザクション",
                "Discordでのコミュニティ参加",
                "テストネットのバリデーター運用",
            ],
            "end_date": "2026-12-31",
            "logo": "https://assets.coingecko.com/coins/images/espresso.png",
            "url": "https://www.espressosys.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "lighter-lit",
            "name": "Lighter (LIT)",
            "symbol": "LIT",
            "category": "DeFi/DEX",
            "type": "オーダーブックDEX",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 400,
            "description": (
                "分散型オーダーブック取引所。総供給量の25%をエアドロップとして配布予定。"
                "Hyperliquidに対抗する次世代onchain DEXとして注目。"
                "取引量・流動性提供でポイントを獲得。"
            ),
            "tasks": [
                "Lighterでスポット/先物取引",
                "流動性プールに資金提供",
                "テストネット参加で先行ポイント獲得",
                "紹介プログラムへの参加",
            ],
            "end_date": "2026-09-30",
            "logo": "https://assets.coingecko.com/coins/images/lighter.png",
            "url": "https://lighter.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "eigenlayer-eigen",
            "name": "EigenLayer (EIGEN)",
            "symbol": "EIGEN",
            "category": "インフラ",
            "type": "リステーキング/エコシステム",
            "status": "active",
            "difficulty": "hard",
            "estimated_value_usd": 700,
            "description": (
                "Ethereumリステーキングプロトコル。EIGENトークンは発行済みだが、"
                "AVSエコシステムへの参加・新しいインセンティブプログラムが継続中。"
                "EigenLayer上に構築されたAVS（Actively Validated Services）の"
                "独自トークンを獲得できる可能性がある。"
            ),
            "tasks": [
                "ETHまたはLSTをEigenLayerにリステーキング",
                "EigenDA・AVSオペレーターへの委任",
                "EigenLayer上のアプリケーション利用",
                "エコシステム内の新規プロジェクトのポイント獲得",
            ],
            "end_date": (today + timedelta(days=180)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/33751/small/eigen.png",
            "url": "https://eigenlayer.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "layerzero-farming",
            "name": "LayerZero エコシステム",
            "symbol": "ZRO",
            "category": "インフラ",
            "type": "クロスチェーン継続ファーミング",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 300,
            "description": (
                "ZROトークンは発行済みだが、LayerZeroエコシステム上に構築された"
                "プロトコル独自のトークンを狙う戦略が継続中。Stargate Finance等の"
                "LayerZero対応dAppsでの高品質なクロスチェーン履歴が有効とされる。"
            ),
            "tasks": [
                "Stargate経由でクロスチェーンブリッジを継続実行",
                "LayerZero対応DEX・レンディングの定期利用",
                "複数チェーンにわたるウォレット活動",
                "LayerZero上の新規プロジェクトのテストネット参加",
            ],
            "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/28206/small/ftxG9_TJ_400x400.jpeg",
            "url": "https://layerzero.network/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "backpack-exchange",
            "name": "Backpack Exchange",
            "symbol": "BP",
            "category": "CeFi/DeFi",
            "type": "取引所トークン",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 350,
            "description": (
                "Mad Lads NFT発行元が運営する次世代CEX/DEXハイブリッド取引所。"
                "2026年Q1注目エアドロップ候補として複数メディアが取り上げ。"
                "取引量・保有資産によるポイントシステムで報酬配布見込み。"
            ),
            "tasks": [
                "Backpackアカウント作成・KYC完了",
                "スポット/先物取引を継続実行",
                "Mad Lads NFT保有 (優先配分の可能性)",
                "紹介プログラム参加",
                "ステーキング機能の利用",
            ],
            "end_date": "2026-12-31",
            "logo": "https://assets.coingecko.com/coins/images/backpack.png",
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

    # airdrops.io取得失敗時はcryptorankからも補完
    if not scraped:
        scraped = _scrape_cryptorank()

    seen_names = {a["name"].lower() for a in curated}
    # シンボルでも重複チェック
    seen_ids = {a["id"] for a in curated}
    new_items = []

    for s in scraped:
        name_lower = s["name"].lower()
        item_id = name_lower.replace(" ", "-")
        if name_lower not in seen_names and item_id not in seen_ids:
            curated.append({
                "id": item_id,
                "name": s["name"],
                "symbol": "",
                "category": "その他",
                "type": "エアドロップ",
                "status": "active",
                "difficulty": "easy",
                "estimated_value_usd": 0,
                "description": f"airdrops.ioより取得 — 推定価値: {s.get('estimated_value', '不明')}",
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
            seen_ids.add(item_id)

    # 注目度でソート: is_hot → estimated_value_usd
    curated.sort(key=lambda x: (not x.get("is_hot"), -x.get("estimated_value_usd", 0)))

    return curated, new_items
