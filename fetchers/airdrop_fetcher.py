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


def _item(id, name, symbol, category, type_, status, difficulty, value, desc, tasks, end_date, url, hot=False, added="2026-10-15", note=""):
    return {
        "id": id, "name": name, "symbol": symbol, "category": category, "type": type_,
        "status": status, "difficulty": difficulty, "estimated_value_usd": value,
        "description": desc, "tasks": tasks, "end_date": end_date, "logo": "",
        "url": url, "is_hot": hot, "added_date": added, "source": "curated", "note": note,
    }


def _build_seed_airdrops() -> list[dict]:
    """手動キュレーションの注目エアドロップ (日次ルーティンで最新情報に更新)。
    最終キュレーション: 2026-10-15。出典は集計サイト(CryptoTicker/AirdropBuzz/CryptoRank等)。
    公式発表での再確認を推奨。"""
    return [
        _item("polymarket-poly", "Polymarket (POLY)", "POLY", "予測市場", "トレードエアドロップ", "upcoming", "medium", 0,
              "2025年10月にCMOがトークン&エアドロップを明言。2026-10-14時点でTGE/スナップショットは未発表。CEOがTOKEN2049(10/7)で再言及し思惑が再燃。",
              ["Polymarketで継続的に取引", "複数カテゴリの市場に参加", "公式発表を要監視"], "未定", "https://polymarket.com/", hot=True,
              note="未確定・TGE日未発表"),
        _item("mint-mntd", "MINT (MNTD)", "MNTD", "ギャンブル/ゲーム", "ポイント", "upcoming", "easy", 50,
              "Season1エアドロ総額$125,000相当のMNTD。累計$50以上のウェイジャリングでXP獲得。TGE日は情報源で9月/Q4/10月20日と食い違い。",
              ["MINTアカウント作成", "対象ゲームで累計$50以上ベット", "XP獲得(クエスト/紹介)"], "2026-10-20", "https://airdrops.io/mint-io/", hot=True,
              note="TGE日が情報源で不一致。資金リスクあり(実資金ベット必須)"),
        _item("tastyco-tasty", "TastyCo (TASTY)", "TASTY", "コンシューマー", "ポイント", "active", "easy", 0,
              "TGE前にポイントを貯めた初期ユーザー向けに$100,000相当の$TASTYエアドロップを確認(AirdropBuzz)。TGE日は未発表。",
              ["TastyCoでポイント獲得タスクを実行"], "未定", "https://airdropbuzz.com/latest-airdrops", hot=True, note="TGE日未発表"),
        _item("jupiter-jup", "Jupiter (JUP) 追加配布", "JUP", "DeFi/DEX", "ロイヤリティ", "active", "easy", 0,
              "CryptoRankで10/13時点に『confirmed』表示。詳細は公式で確認。", ["Jupiter利用/ステーク"], "未定", "https://cryptorank.io/drophunting"),
        _item("ekiden", "Ekiden", "", "DeFi/DEX", "ポイント", "active", "medium", 0,
              "CryptoRankで10/14時点に『confirmed』表示。", ["公式サイトでタスク確認"], "未定", "https://cryptorank.io/drophunting"),
        _item("ecash-com", "eCash.com", "", "決済", "エアドロップ", "active", "easy", 0,
              "CryptoRankで10/14時点に『confirmed』表示。", ["公式サイトでタスク確認"], "未定", "https://cryptorank.io/drophunting"),
        _item("meteora-s2", "Meteora LP Stimulus Season 2 (MET)", "MET", "DeFi/DEX", "クレーム", "active", "easy", 0,
              "Season2のクレーム期限は10/21(CryptoTicker週間まとめ)。期限切れ前に請求。", ["対象ウォレットでクレームページから請求"], "2026-10-21", "https://docs.meteora.ag/protocol/met/s2-airdrop-terms", hot=True,
              note="Meteora旧情報と食い違いあり。公式確認必須"),
        _item("pharos-pros", "Pharos (PROS)", "PROS", "Layer1", "クレーム", "active", "easy", 0,
              "クレームポータルは10/25に閉鎖。未請求分はPharos財団に戻る。", ["対象ウォレットで請求"], "2026-10-25", "https://pharos.xyz/"),
        _item("questflow-s3", "Questflow Trader Arena Season 3", "", "AI/エージェント", "キャンペーン", "active", "medium", 0,
              "Season3は8/24〜10/24開催(掲載サイト情報)。", ["Trader Arenaに参加"], "2026-10-24", "https://airdropalert.com/farm/"),
        _item("near-allocation", "NEAR 配布", "NEAR", "Layer1", "クレーム", "active", "easy", 0,
              "AirdropBuzzで配布ライブ表示(10/9更新)。詳細は公式確認。", ["公式サイトで対象確認"], "未定", "https://airdropbuzz.com/latest-airdrops"),
        _item("midnight-night", "Midnight (NIGHT)", "NIGHT", "プライバシー", "解凍", "active", "easy", 0,
              "解凍(thawing)は2026-12-04まで、その後90日の猶予。", ["解凍スケジュールに沿って請求"], "2026-12-04", "https://midnight.network/"),
        _item("grass-stage2", "Grass Stage 2", "GRASS", "DePIN", "クレーム", "active", "easy", 0,
              "Stage2のクレームは2027-01-22まで。", ["Grassウォレットで請求"], "2027-01-22", "https://www.getgrass.io/"),
        _item("sonic-s-burn", "Sonic (S) 未請求分バーン", "S", "Layer1", "クレーム", "ended", "easy", 0,
              "10/15に未請求S約3,269万枚がバーンされ請求受付終了。", [], "2026-10-15", "https://www.soniclabs.com/"),
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
    curated.sort(key=lambda x: (x.get("status") == "ended", not x.get("is_hot"), -x.get("estimated_value_usd", 0)))

    return curated, new_items
