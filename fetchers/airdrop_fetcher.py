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
    """手動管理の注目エアドロップシードデータ (2026年7月時点の最新情報で更新)"""
    today = datetime.utcnow()
    return [
        {
            "id": "backpack-back",
            "name": "Backpack Exchange (BACK)",
            "symbol": "BACK",
            "category": "取引所/Solana",
            "type": "取引所トークン",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1500,
            "description": "セルフカストディウォレット+規制取引所を展開するBackpack。2026年2月にTGE計画を正式発表し、供給量の25%をコミュニティに配分予定。現在Epilogueフェーズでポイント最終獲得受付中。",
            "tasks": ["Backpack Exchangeでのトレーディング", "Backpack WalletでのSolana DeFi利用", "Backpack Pay利用", "紹介プログラム", "TGE前にKYC完了が必須"],
            "end_date": (today + timedelta(days=25)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/39457/small/backpack.png",
            "url": "https://backpack.exchange/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "opensea-sea",
            "name": "OpenSea (SEA)",
            "symbol": "SEA",
            "category": "NFT",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 1000,
            "description": "最大手NFTマーケットプレイスOpenSeaのネイティブトークン。供給量の50%をコミュニティに配分。Voyages(XPクエスト)への参加度合いで配分比率が決まる。",
            "tasks": ["OS2プラットフォームでのNFT売買", "週次Voyagesクエスト達成", "EVM/Solanaウォレット連携", "X・Discordアカウント連携"],
            "end_date": (today + timedelta(days=40)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/1/small/opensea.png",
            "url": "https://opensea.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "base-token",
            "name": "Base Network Token",
            "symbol": "BASE",
            "category": "Layer2",
            "type": "推測段階(未確定)",
            "status": "upcoming",
            "difficulty": "medium",
            "estimated_value_usd": 2000,
            "description": "Coinbase開発のLayer2「Base」。ネットワークトークン発行を検討中と公式発言あり(2025年9月)。JPMorganは時価総額120〜340億ドルと試算。正式発表はまだだが2026年内の可能性が最も注目される大型案件。",
            "tasks": ["EthereumからBaseへETHブリッジ", "Base上のDEXでスワップ", "DeFiへの流動性提供", "Coinbaseアカウント連携(Sybil対策として有利との観測)"],
            "end_date": "未定 (2026年内に発表の可能性)",
            "logo": "https://assets.coingecko.com/asset_platforms/images/131/small/base-network.png",
            "url": "https://base.org/",
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
            "description": "急成長中の予測市場プラットフォーム。トークン発行が有力視されており、早期からの取引実績がエアドロップ対象になる可能性。",
            "tasks": ["市場での予測ポジション取引", "継続的な取引アクティビティ", "USDC入出金の実績"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/44802/small/polymarket.png",
            "url": "https://polymarket.com/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "metamask-mask",
            "name": "MetaMask (MASK)",
            "symbol": "MASK",
            "category": "ウォレット",
            "type": "レトロアクティブ",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 150,
            "description": "最大手Web3ウォレットMetaMaskのトークン化が期待されている。ユーザー数が非常に多いため一人あたりの配分は少なめの見込み。",
            "tasks": ["MetaMask Swaps利用", "MetaMask Card利用", "Portfolio機能でのアクティビティ"],
            "end_date": "未定",
            "logo": "https://assets.coingecko.com/coins/images/1/small/metamask.png",
            "url": "https://metamask.io/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "grass-season2",
            "name": "Grass Season 2",
            "symbol": "GRASS",
            "category": "DePIN",
            "type": "追加配布",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 200,
            "description": "未使用の帯域幅を提供してAI学習データ収集に貢献するDePINプロジェクト。Season2ウォレットが2026年7月中旬にローンチ予定、7月7日にトークンホルダー向け公開コールを実施。",
            "tasks": ["Grass拡張機能をインストールし帯域幅を共有", "Season2ウォレットの新規登録", "7月7日の公開コールに参加"],
            "end_date": (today + timedelta(days=15)).strftime("%Y-%m-%d"),
            "logo": "https://assets.coingecko.com/coins/images/38270/small/Grass_200x200.png",
            "url": "https://www.grass.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "hyperliquid-hype-s2",
            "name": "Hyperliquid Season 2",
            "symbol": "HYPE",
            "category": "DeFi/DEX",
            "type": "追加ポイント配布",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 600,
            "description": "高速オンチェーン永久先物DEX。Season1配布後も取引量・流動性提供に応じた継続的なポイント/報酬プログラムが稼働中。",
            "tasks": ["Hyperliquid上での先物取引", "流動性提供(HLPボールト)", "紹介プログラム参加"],
            "end_date": (today + timedelta(days=50)).strftime("%Y-%m-%d"),
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
