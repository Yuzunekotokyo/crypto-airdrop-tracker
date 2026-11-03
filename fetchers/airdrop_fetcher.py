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
    """手動管理の注目エアドロップ (毎日のWeb調査で更新)。推定価値は目安で未確認情報を含む。"""
    return [{'id': 'polymarket-poly', 'name': 'Polymarket (POLY)', 'symbol': 'POLY', 'category': '予測市場', 'type': 'トークン/エアドロ確認済', 'status': 'upcoming', 'difficulty': 'medium', 'estimated_value_usd': 1000, 'description': 'CMOがトークンとエアドロップを公式に確認済み。スナップショット日・条件は未発表。※非公式サイトの『受取』リンクは詐欺に注意。公式はpolymarket.comのみ。', 'tasks': ['予測市場で継続的に取引', '取引量・活動の分散', '公式発表を確認'], 'end_date': '未定', 'logo': '', 'url': 'https://polymarket.com/', 'is_hot': True, 'added_date': '2026-11-03', 'source': 'curated'},
        {'id': 'metamask-mask', 'name': 'MetaMask (MASK)', 'symbol': 'MASK', 'category': 'ウォレット', 'type': 'ポイント制', 'status': 'active', 'difficulty': 'medium', 'estimated_value_usd': 800, 'description': '2025年10月にポイントプログラム開始(スワップ/パープ/ブリッジ/紹介)。LINEA利用でポイント2倍と報じられる。公式の配布条件は未発表で推測を含む。', 'tasks': ['MetaMask内でスワップ・パープ取引', 'ブリッジ利用', 'LINEAを利用'], 'end_date': '未定', 'logo': '', 'url': 'https://metamask.io/', 'is_hot': True, 'added_date': '2026-11-03', 'source': 'curated'},
        {'id': 'opensea-sea', 'name': 'OpenSea (SEA)', 'symbol': 'SEA', 'category': 'NFT/マーケット', 'type': 'トークン', 'status': 'upcoming', 'difficulty': 'easy', 'estimated_value_usd': 500, 'description': '2026年Q1目標と報じられたが、ローンチ/請求状況は今回確認できず。供給の50%がコミュニティ向け。公式で最新状況を要確認。', 'tasks': ['過去のOpenSea利用実績', 'OS2でのXP活動', '公式請求ページのみ利用'], 'end_date': '未定', 'logo': '', 'url': 'https://opensea.io/', 'is_hot': False, 'added_date': '2026-11-03', 'source': 'curated'},
        {'id': 'concrete-ct', 'name': 'Concrete (CT)', 'symbol': 'CT', 'category': 'DeFi/利回り', 'type': 'ポイント制', 'status': 'active', 'difficulty': 'easy', 'estimated_value_usd': 300, 'description': '2026年9月に独自トークンCTとTGE計画を発表。ポイントキャンペーンが参加入口。', 'tasks': ['ポイントキャンペーンに参加', 'Vaultへ入金'], 'end_date': '未定', 'logo': '', 'url': 'https://concrete.xyz/', 'is_hot': False, 'added_date': '2026-11-03', 'source': 'curated'},
        {'id': 'ekiden', 'name': 'Ekiden', 'symbol': '', 'category': 'DEX', 'type': 'ポイント制', 'status': 'upcoming', 'difficulty': 'medium', 'estimated_value_usd': 300, 'description': 'メインネット開始に合わせたリワードプログラムを予告。取引活動でポイント獲得。', 'tasks': ['メインネット後に取引', 'ポイント獲得'], 'end_date': '未定', 'logo': '', 'url': 'https://ekiden.fi/', 'is_hot': False, 'added_date': '2026-11-03', 'source': 'curated'},
        {'id': 'megaeth-mega', 'name': 'MegaETH (MEGA)', 'symbol': 'MEGA', 'category': 'Layer2', 'type': 'NFT保有者', 'status': 'upcoming', 'difficulty': 'hard', 'estimated_value_usd': 500, 'description': '公式の一般向けエアドロは未確認。The Fluffle NFT保有者に供給の5%以上が配布予定。', 'tasks': ['エコシステムdApp利用', '公式発表を監視'], 'end_date': '未定', 'logo': '', 'url': 'https://megaeth.com/', 'is_hot': False, 'added_date': '2026-11-03', 'source': 'curated'},
        {'id': 'backpack-points', 'name': 'Backpack (Points)', 'symbol': '', 'category': '取引所', 'type': 'ポイント制', 'status': 'active', 'difficulty': 'easy', 'estimated_value_usd': 300, 'description': '週次の取引活動が複数シーズンにわたりTGE配分を決定(第三者ガイドの情報)。', 'tasks': ['Backpackで毎週取引'], 'end_date': '未定', 'logo': '', 'url': 'https://backpack.exchange/', 'is_hot': False, 'added_date': '2026-11-03', 'source': 'curated'}]


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
