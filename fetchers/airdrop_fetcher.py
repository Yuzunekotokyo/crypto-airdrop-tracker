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


# その日の更新で特筆すべき点 (更新バナー最上部に表示)
DAILY_NOTES = [
    "🆕 Saturn (STRN): Season1/2 のエアドロップ登録が11/9開始、11/16 9:00 EST (23:00 JST) 締切。TGEは2026年Q4予定、Season2に供給の最大5%。登録URLが二次情報で不一致のため、必ず公式Xのリンクから。",
    "🆕 Predict.fun (PREDICT): Binance上場延期に伴いTGE・Season1クレームが延期。即時35% / 12か月ベスティング100% の2択。",
    "✏️ Aster Stage 6: クレーム終了日を 12/4 12:00 UTC に修正 (複数ソースで一致。11/28は外れ値)。",
    "✏️ StandX: トークンローンチ自体は中止、DUSDクレームは12/31 08:00 UTC まで。",
    "⏰ 期限が近い順: Saturn登録 11/16 → Fables 11/20 → Doppler 11/28 → Aster 12/4。",
    "終了: infiniFi (INFI) の登録は11/10、KOR Protocol のクレームは11/9に締切済み。",
]


def _build_seed_airdrops() -> list[dict]:
    """手動管理の注目エアドロップ (2026-11-11 時点の検索結果に基づく)。
    ポイント制は必ずしもトークン配布を保証しない。公式サイトで必ず確認すること。"""
    d = "2026-11-11"

    def mk(id_, name, symbol, cat, typ, status, diff, val, desc, tasks, end, url, hot):
        return {
            "id": id_, "name": name, "symbol": symbol, "category": cat, "type": typ,
            "status": status, "difficulty": diff, "estimated_value_usd": val,
            "description": desc, "tasks": tasks, "end_date": end, "logo": "",
            "url": url, "is_hot": hot, "added_date": d, "source": "curated",
        }

    return [
        mk("saturn-strn", "Saturn (STRN)", "STRN", "DeFi", "エアドロップ登録受付中", "active", "easy", 0,
           "Season1/Season2のエアドロップ登録が11/9に開始、11/16 9:00 EST(23:00 JST)締切。TGEは2026年Q4予定で、Season2参加者に総供給の最大5%。"
           "登録=配布保証ではない(財団明言)。Discordアカウントは作成5日以上が条件との情報あり。登録URLが二次情報で食い違うため公式Xのリンクのみ使用。",
           ["公式Xで案内される登録ページでウォレット/Discordを登録(11/16まで)", "Season2ポイントの積み増しは登録締切後も継続"],
           "2026-11-16", "", True),
        mk("aster-stage6", "Aster (ASTER) Stage 6", "ASTER", "DeFi/DEX", "クレーム受付中", "active", "easy", 0,
           "Stage6「Convergence」で6,400万ASTER(総供給の0.8%)を配布。100%ベスト済みクレームは11/4 12:00 UTC〜12/4 12:00 UTC。"
           "Stage6で10,000ポイント以上、かつ4/20〜5/2に6か月ベスティングを選択した参加者が対象。",
           ["対象か公式ページで確認", "12/4 12:00 UTCまでにクレーム"], "2026-12-04", "https://www.asterdex.com/", True),
        mk("fables", "Fables (FABLES)", "FABLES", "DeFi/DEX", "ポイントクレーム", "active", "easy", 0,
           "Robinhood Chain上のDEX(Uniswap v4 Hook)。ポイントクレーム期限は11/20 23:59 UTC。"
           "10/19 02:00 UTCまでにクレームオプションを保存済みのウォレットのみ対象(新規参加不可)。",
           ["fables.fi でポイントをクレーム(11/20まで)"], "2026-11-20", "https://fables.fi/", True),
        mk("predict-fun", "Predict.fun (PREDICT)", "PREDICT", "予測市場", "TGE延期・クレーム待ち", "upcoming", "medium", 0,
           "Binance Alpha/現物上場の延期に合わせ、TGEとSeason1クレームが延期(新日程未定)。即時クレームは割当の35%、12か月ベスティングなら100%。"
           "選択フォーム締切は11/26 09:00 UTCとの報道あり(単一ソース・要公式確認)。",
           ["公式Xで新しいクレーム日時を確認", "35%即時 / 100%ベスティングの選択を期限内に提出"],
           "未定", "https://predict.fun/", True),
        mk("opensea-sea", "OpenSea (SEA)", "SEA", "NFT", "ポイント/将来配布", "upcoming", "medium", 0,
           "SEAトークンは公式に確認済みで供給の50%をコミュニティへ。ただしローンチは複数回延期され日程未定。",
           ["OpenSeaでの取引・利用"], "未定", "https://opensea.io/", True),
        mk("polymarket", "Polymarket", "POLY", "予測市場", "未発表", "upcoming", "medium", 0,
           "CMOがPOLYトークンとエアドロップを確認済みだが、時期・条件は未公開(新情報なし)。",
           ["Polymarketでの取引を継続"], "未定", "https://polymarket.com/", True),
        mk("doppler-xdp", "Doppler Finance (XDP)", "XDP", "DeFi", "ジェネシスエアドロップ", "active", "easy", 0,
           "Genesis Airdrop(総供給の1%、ロックなし)は11/28 12:00 UTC終了、未請求分は失効。2026/7/30以前にBaseアドレスを登録済みのユーザーのみ対象(新規参加不可)。",
           ["対象アドレスでクレーム"], "2026-11-28", "", False),
        mk("standx-dusd", "StandX (DUSD)", "DUSD", "DeFi", "クレーム受付中", "active", "easy", 0,
           "11/2からDUSDクレーム開放、12/31 08:00 UTCまで。トークンローンチ自体は中止と報道。チェッカー/クレームは公式サイトのみ(偽サイト注意)。",
           ["公式サイトでクレーム"], "2026-12-31", "", False),
        mk("dango-dng", "Dango (DNG)", "DNG", "DeFi", "ポイントプログラム", "upcoming", "medium", 0,
           "ポイントプログラム実施中、TGEは2026年Q4予定(宣伝系ソースのため要注意)。",
           ["ポイントプログラムに参加"], "未定", "", False),
        mk("metamask-mask", "MetaMask (MASK)", "MASK", "ウォレット", "未確定", "upcoming", "medium", 0,
           "情報が錯綜。Rewards Season1は終了済みで「独自トークンの予定なし」とする報道と、11/26クレーム期限とする記載が混在。期待値は低めに見るべき。",
           ["MetaMaskの利用(Swaps/Perps等)"], "未定", "https://metamask.io/", False),
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
    # 同順位は手動キュレーションの並び (期限が近い/注目度順) を維持
    curated.sort(key=lambda x: (not x.get("is_hot"), -x.get("estimated_value_usd", 0)))

    return curated, new_items
