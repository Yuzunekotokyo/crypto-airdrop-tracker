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
    """手動管理の注目エアドロップシードデータ (2026年6月更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "metamask-mask",
            "name": "MetaMask ($MASK)",
            "symbol": "MASK",
            "category": "ウォレット",
            "type": "リワードポイント",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 2000,
            "description": "1.4億人以上が使うWeb3ウォレット。MetaMask Rewardsポイントが$MASKトークンに転換予定。Q3-Q4 2026にTGE見込み。スワップ・ブリッジ・マルチチェーン活動でポイント獲得。",
            "tasks": [
                "MetaMask モバイルアプリでRewardsを有効化",
                "MetaMask内でトークンスワップを実施",
                "MetaMask Bridgeで複数チェーン間ブリッジ",
                "5チェーン以上(ETH・Base・Linea・Arbitrum・Polygonなど)で利用",
                "MetaMask Card利用またはPerps取引で追加ポイント",
                "MetaMask Portfolio Stakingへ参加",
            ],
            "end_date": "2026-12-31",
            "logo": "https://assets.coingecko.com/coins/images/11849/small/metamask.png",
            "url": "https://portfolio.metamask.io/rewards",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "polymarket-poly",
            "name": "Polymarket ($POLY)",
            "symbol": "POLY",
            "category": "予測市場",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 3000,
            "description": "世界最大の暗号通貨予測市場。CMOが「トークンとエアドロップは必ずある」と公言。$9B評価額で総額$1.4B規模の配布も噂。2026年後半にTGE見込み。",
            "tasks": [
                "Polymarket.comでアカウント作成 (MetaMask等で接続)",
                "USDC入金してPolygonで予測市場をトレード",
                "政治・スポーツ・クリプトなど複数カテゴリに分散参加",
                "X(Twitter)アカウントをPolymarketに連携",
                "polymarket.com/rewardsで指値注文を出し流動性提供",
                "複数ウォレットは不可・ウォッシュトレード禁止",
            ],
            "end_date": "2026-12-31",
            "logo": "https://assets.coingecko.com/coins/images/34977/small/polymarket.jpg",
            "url": "https://polymarket.com/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "grvt-token",
            "name": "GRVT ($GRVT)",
            "symbol": "GRVT",
            "category": "DeFi/DEX",
            "type": "Season 2",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1500,
            "description": "ZK AppChain上のプライバシー特化ハイブリッドDEX。コミュニティへ総供給量28%を配布予定。Season 2は2026年6月30日終了、Q3 2026にTGE予定。今すぐ参加が必要。",
            "tasks": [
                "grvt.ioでアカウント作成・KYC完了",
                "取引量を増やしてポイント獲得",
                "建玉(Open Interest)維持でポイント加算",
                "流動性提供でポイント獲得",
                "紹介プログラムへ参加",
                "Season 2期限: 2026年6月30日",
            ],
            "end_date": "2026-06-30",
            "logo": "https://assets.coingecko.com/coins/images/40072/small/grvt.png",
            "url": "https://grvt.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-coinbase",
            "name": "Base (Coinbase L2)",
            "symbol": "BASE",
            "category": "Layer2",
            "type": "レトロアクティブ (未確認)",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 1000,
            "description": "Coinbaseが開発するEthereum L2。JPモルガン試算で$12〜34Bの時価総額見込み。トークン未発行で最大ポテンシャルの未確認エアドロップ。今のうちにオンチェーン活動を積むべし。",
            "tasks": [
                "Base L2へETHをブリッジ",
                "Uniswap/Aerodrome等でスワップ",
                "BaseのNFTを購入・Mintに参加",
                "BaseのDeFiプロトコル (Aave等) を利用",
                "Coinbaseウォレットまたはbase.orgで活動",
                "継続的なマルチウィーク活動を積む",
            ],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/32394/small/base-network-logo.png",
            "url": "https://base.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "layerzero-zero-l1",
            "name": "LayerZero Zero L1",
            "symbol": "ZRO",
            "category": "インフラ",
            "type": "ZROホルダー特典",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 600,
            "description": "LayerZeroが2026年秋に独自L1ブロックチェーン「Zero」を立ち上げ予定。Tether・DTCC・ICE・Google Cloudが支援。ZROトークンがZeroのガストークンになる見込みでZRO保有者にとって追加の恩恵。",
            "tasks": [
                "ZROトークンを購入・保有",
                "LayerZero公式サイトで最新情報チェック",
                "ZeroチェーンのTGE情報に備える (2026年秋予定)",
                "Stargate経由でブリッジを実施し既存エコシステムに参加",
            ],
            "end_date": "2026-12-31",
            "logo": "https://assets.coingecko.com/coins/images/28206/small/ftxG9_TJ_400x400.jpeg",
            "url": "https://layerzero.network/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "kaito-ai",
            "name": "Kaito AI ($KAITO)",
            "symbol": "KAITO",
            "category": "AI/InfoFi",
            "type": "Studio / Yap",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 400,
            "description": "AI×情報ファイナンスプロジェクト。TGE済み(2025年)で総供給の56.6%をコミュニティに配布。2026年2月にKaito Studioを立ち上げ、継続的なドロップキャンペーン実施中。",
            "tasks": [
                "Kaito.aiでアカウント作成",
                "Kaito Studioのブランドキャンペーンに参加",
                "クリプト関連コンテンツをXで発信しYapポイント獲得",
                "Binance HODLerエアドロップ枠にも注目",
            ],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/38424/small/kaito.jpg",
            "url": "https://kaito.ai/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "uniswap-v4",
            "name": "Uniswap V4",
            "symbol": "UNI",
            "category": "DeFi/DEX",
            "type": "流動性提供報酬",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 800,
            "description": "Uniswap V4はカスタムフック機能を持つ次世代AMM。V4への移行初期にLP提供者・アクティブユーザーへの追加UNI配布が期待される。",
            "tasks": [
                "Uniswap V4でLP (流動性提供) を実施",
                "Uniswap V4のスワップを定期的に行う",
                "UNIトークンをガバナンス投票に使用",
                "複数チェーン(ETH・Base・Arbitrum)で活動",
            ],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/12504/small/uniswap-uni.png",
            "url": "https://uniswap.org/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-hype",
            "name": "Hyperliquid (HYPE)",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "継続エコシステム",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 500,
            "description": "高速オンチェーン永久先物DEX。2024年12月にTGE済み。HYPEトークンが独自L1のネイティブガストークン。継続的な取引でポイント(Points)獲得&将来の追加配布に備える。",
            "tasks": [
                "Hyperliquid上での先物・スポット取引",
                "HyperEVM上のDeFiプロトコル利用",
                "流動性提供 (HLP Vault)",
                "HYPEトークンのステーキング",
            ],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/42277/small/hyperliquid.jpg",
            "url": "https://hyperliquid.xyz/",
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
