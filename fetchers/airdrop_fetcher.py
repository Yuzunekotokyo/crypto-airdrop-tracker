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


def _item(id, name, symbol, category, type_, status, difficulty, value, desc, tasks,
          end_date, url, hot=False, added="2026-11-08", note=""):
    return {
        "id": id, "name": name, "symbol": symbol, "category": category, "type": type_,
        "status": status, "difficulty": difficulty, "estimated_value_usd": value,
        "description": desc, "tasks": tasks, "end_date": end_date, "logo": "",
        "url": url, "is_hot": hot, "added_date": added, "source": "curated",
        "note": note,
    }


def _build_seed_airdrops() -> list[dict]:
    """手動管理の注目エアドロップ (毎日の調査で更新)。
    情報源: 2026-11-08時点のWeb検索結果 (Bittime / MEXC / Cryptorank / CoinGabbar)。
    金額は目安であり、各公式チャンネルで必ず確認すること。"""
    return [
        _item("aster-stage6", "Aster (Stage 6)", "ASTER", "DeFi/DEX", "ポイント報酬", "active", "medium", 0,
              "Aster Stage 6 のクレーム受付中。11/4開始、期限は12月上旬。",
              ["公式サイトでウォレット接続しクレーム", "Stage 6 対象ポイントの確認"],
              "2026-12-05", "https://www.asterdex.com/", hot=True, added="2026-11-04",
              note="期限は『12月上旬』のため目安日"),
        _item("variational-genesis", "Variational", "", "DeFi/DEX", "ジェネシス・エアドロップ", "upcoming", "medium", 0,
              "ポイント保有者向けジェネシスエアドロップ。TGEは2026年Q4目標、全量アンロック予定(MEXC掲載)。",
              ["Variationalで取引してポイントを貯める"],
              "2026-12-31", "https://variational.io/", hot=True,
              note="TGE日未確定。Q4目標"),
        _item("ink-kraken", "Ink (Kraken)", "INK", "Layer2", "レトロアクティブ", "upcoming", "easy", 0,
              "Kraken系L2のINKエアドロップが発表済み。対象条件は未確定。",
              ["Ink上でのDeFi/ブリッジ利用", "公式の続報を確認"],
              "未定", "https://inkonchain.com/", hot=True,
              note="エリジビリティ未確定"),
        _item("standx-claim", "StandX", "", "DeFi/DEX", "クレーム", "active", "easy", 0,
              "クレーム受付中(11/2開始)。",
              ["公式でクレーム資格を確認"], "未定", "https://standx.com/", added="2026-11-02"),
        _item("fables-claim", "Fables", "", "ゲーム", "クレーム", "active", "easy", 0,
              "クレーム期限 11/20。", ["公式でクレーム資格を確認"], "2026-11-20", "https://airdrops.io/"),
        _item("predictfun-claim", "Predict.fun", "", "予測市場", "クレーム", "active", "easy", 0,
              "クレーム期限 11/26。", ["公式でクレーム資格を確認"], "2026-11-26", "https://predict.fun/"),
        _item("doppler-claim", "Doppler", "", "インフラ", "クレーム", "active", "easy", 0,
              "クレーム期限 11/28。", ["公式でクレーム資格を確認"], "2026-11-28", "https://airdrops.io/"),
        _item("apyx", "Apyx", "", "DeFi", "配分確定", "upcoming", "easy", 0,
              "トークン配分は確定済みだがTGEは延期中。", ["公式の続報を確認"], "未定", "https://airdrops.io/"),
        _item("metric-qfex", "Metric / QFEX", "", "その他", "噂・未確認", "upcoming", "medium", 0,
              "Cryptorankが11/7前後の潜在エアドロップとして掲載。未確認情報。",
              ["公式情報の確認を優先"], "未定", "https://cryptorank.io/drophunting",
              note="未確認。詐欺・フィッシングに注意"),
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
