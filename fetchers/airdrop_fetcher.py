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
    """手動管理の注目エアドロップシードデータ (毎日の自動更新タスクが最新情報に基づき書き換える)"""
    today = datetime.utcnow()
    return [
        {
            "id": "mint-io-mntd",
            "name": "mint.io (MNTD)",
            "symbol": "MNTD",
            "category": "DeFi/カジノ",
            "type": "ポイント制エアドロップ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 150,
            "description": "Base上のオンラインカジノ&スポーツブック。2026年9月のTGE前に総額$125,000相当のMNTDをプレイヤーに分配予定。累計$50ベットのみという低い参加ハードルが特徴。",
            "tasks": ["mint.ioで無料アカウント登録", "USDT/USDC/ETHを入金", "カジノ or スポーツブックで累計$50以上ベット", "スナップショットまでシーズンXPを積み上げ"],
            "end_date": "2026-09-30",
            "logo": "",
            "url": "https://mint.io/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "push-chain-pc",
            "name": "Push Chain (PC)",
            "symbol": "PC",
            "category": "インフラ",
            "type": "レトロアクティブ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 400,
            "description": "あらゆるチェーンのアプリを繋ぐユニバーサルブロックチェーン。Devnet Drop Points Program S2でPushポイントを貯めるとメインネット後のPCトークンエアドロップの資格になる。",
            "tasks": ["Push Chainポータルでウォレット接続・資格確認", "Devnetエコシステムアプリを利用してポイント獲得", "デイリーチェックイン", "レガシーPUSHトークンを30日ロックで1.2倍ブースト"],
            "end_date": "2026-11-30",
            "logo": "",
            "url": "https://push.org/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "aiw3",
            "name": "AIW3",
            "symbol": "AIW3",
            "category": "AI/Solana",
            "type": "ジェネシス+月次エアドロップ",
            "status": "active",
            "difficulty": "medium",
            "estimated_value_usd": 300,
            "description": "Solana上のAIエージェント×ソーシャルトレーディング&予測市場プラットフォーム。2026年8月3日にジェネシススナップショットに基づくTGEを実施済み。今後もポイントに応じた月次エアドロップが継続予定。",
            "tasks": ["AIW3でウォレット接続", "AIトレーディング戦略・予測市場に参加", "継続的にポイント(スコア)を蓄積"],
            "end_date": "月次継続",
            "logo": "",
            "url": "https://aiw3.ai/",
            "is_hot": True,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "propr-propr",
            "name": "Propr (PROPR)",
            "symbol": "PROPR",
            "category": "DeFi/トレーディング",
            "type": "ジェネシスエアドロップ",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 200,
            "description": "Hyperliquid上のオンチェーンプロップトレーディングファーム。総供給10億枚のうち20%を2026年8月24日のTGEでジェネシスエアドロップとして配布済み。クレーム期間中。",
            "tasks": ["Proprで評価チャレンジ(ファンデッドアカウント審査)に参加", "対象期間中の取引実績を積む", "公式サイトでクレーム状況を確認"],
            "end_date": "2026-09-15",
            "logo": "",
            "url": "https://www.propr.xyz/",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "orbinum-orb",
            "name": "Orbinum (ORB)",
            "symbol": "ORB",
            "category": "プライバシー/インフラ",
            "type": "テストネットポイント",
            "status": "active",
            "difficulty": "easy",
            "estimated_value_usd": 100,
            "description": "プライバシー重視のL1テストネット。Shield/Private Transfer/UnshieldのオンチェーンクエストでORBクレジットを貯めると、獲得比率に応じて2,000万ORBが配分される。メインネット/TGEは2026年Q4予定。",
            "tasks": ["Orbinum Hub (app.orbinum.network) でウォレット接続", "X・Discord・Telegramを連携 (サインアップで+20クレジット)", "testnetでShield/Private Transfer/Unshieldを毎日実行", "週次ストリークを維持してマルチプライヤーを上げる"],
            "end_date": "メインネット14日前にスナップショット",
            "logo": "",
            "url": "https://app.orbinum.network/community",
            "is_hot": False,
            "added_date": today.strftime("%Y-%m-%d"),
            "source": "curated",
        },
        {
            "id": "yakkamon",
            "name": "Yakkamon",
            "symbol": "",
            "category": "GameFi",
            "type": "事前登録ポイント",
            "status": "upcoming",
            "difficulty": "easy",
            "estimated_value_usd": 150,
            "description": "Sunflower Land開発元Thought FarmによるRonin上のクリーチャー収集・アイドルファーミングゲーム。Season 0事前登録のポイント順位が早期アクセスとNFTエアドロップの優先度を左右。早期アクセスは2026年第4四半期予定。",
            "tasks": ["yakkamon.comでSeason 0事前登録 (メールのみ、ウォレット不要)", "$FLOWERを早期デポジットしてポイント獲得", "Discord/Xコミュニティに参加"],
            "end_date": "2026年Q4 (早期アクセス開始)",
            "logo": "",
            "url": "https://yakkamon.com/",
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
