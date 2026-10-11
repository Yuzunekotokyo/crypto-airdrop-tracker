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
    """手動管理の注目エアドロップシードデータ (毎日の更新で見直す)。最終見直し: 2026-10-11"""
    added = "2026-10-11"

    def item(id, name, symbol, category, type_, status, difficulty, value, desc, tasks, end, url, hot, note=""):
        return {
            "id": id, "name": name, "symbol": symbol, "category": category, "type": type_,
            "status": status, "difficulty": difficulty, "estimated_value_usd": value,
            "description": desc, "tasks": tasks, "end_date": end, "logo": "",
            "url": url, "is_hot": hot, "added_date": added, "source": "curated", "note": note,
        }

    return [
        item("sonic-s", "Sonic (S) 最終請求", "S", "Layer1", "請求期限", "active", "easy", 0,
             "Season1/2エアドロップの未請求分 約3,269万S が 2026-10-15 に焼却予定。延長なし・猶予なし。ペナルティなしで請求可能。",
             ["my.soniclabs.com/airdrop で対象か確認", "未請求ならSeason1/2を請求"],
             "2026-10-15", "https://my.soniclabs.com/airdrop", True, "期限まで残り4日。偽ポータルに注意"),
        item("pharos-pros", "Pharos (PROS) 請求期限", "PROS", "Layer1", "請求期限", "active", "easy", 0,
             "請求ポータルは 2026-10-25 に閉鎖。未請求分はPharos財団へ返還。テストネット参加者・Stake Before the Stake・Discordロール・OKX Wallet施策が対象。",
             ["claim.pharos.xyz で対象を確認 (類似ドメインのドレイナーに注意)", "期限前に請求"],
             "2026-10-25", "https://claim.pharos.xyz/", True, "期限まで残り約2週間"),
        item("grass-stage2", "Grass (Stage 2) USDC報酬", "GRASS", "DePIN", "請求期限", "active", "easy", 0,
             "Stage 2の報酬はUSDCで支払い。請求は 2027-01-22 まで可能。",
             ["Grassアカウントで対象を確認", "USDC報酬を請求"],
             "2027-01-22", "https://www.getgrass.io/", False),
        item("ekiden", "Ekiden", "", "DeFi/DEX", "ポイント", "active", "medium", 0,
             "Cryptorankで10/2時点Confirmed。メインネット取引でポイント獲得→エアドロップ。TGE日程は未発表(集約サイト情報・要公式確認)。",
             ["メインネットで取引", "ポイントを蓄積"],
             "未定", "https://cryptorank.io/drophunting", True, "新規注目案件(未検証情報を含む)"),
        item("aster-dex", "Aster DEX 取引エアドロップ", "ASTER", "DeFi/DEX", "取引報酬", "active", "medium", 0,
             "取引量に応じたASTER配布。AirdropAlert上でStage 6(約6,400万ASTER)。(集約サイト情報)",
             ["Aster DEXで取引", "ステージごとの配布を確認"],
             "未定", "https://airdropalert.com/browse-airdrops/", False),
        item("ecash-ecx", "eCash.com (ECX)", "ECX", "その他", "エアドロップ", "upcoming", "easy", 0,
             "Cryptorankで10/2時点Confirmed。詳細は未検証。", [], "未定", "https://cryptorank.io/drophunting", False),
        item("titan-canton", "Titan (Canton)", "", "インフラ", "エアドロップ", "upcoming", "medium", 0,
             "Cryptorankで10/2時点Confirmed。詳細は未検証。", [], "未定", "https://cryptorank.io/drophunting", False),
        item("brownian-bro", "Brownian ($BRO)", "BRO", "その他", "ポイント", "upcoming", "medium", 0,
             "ポイントはTGEで$BROに変換、TGEは遅くとも2026年Q4目標。変換方式は未公表。",
             ["ポイント獲得タスクを継続"], "2026-12-31", "https://cryptorank.io/drophunting", False),
        item("ink-kraken", "Ink (Kraken L2)", "", "Layer2", "ポイント", "upcoming", "medium", 0,
             "2026年内のTGE見込み。ポイントのトークン変換は確認済み、日程は未発表。",
             ["Ink上でDeFi/ブリッジ利用"], "未定", "https://inkonchain.com/", False),
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
