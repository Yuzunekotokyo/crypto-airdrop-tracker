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
    "📌 本日の結論: 新規の大型・高期待値エアドロップの発表は確認できず。最優先は引き続き Saturn (STRN) 登録 (締切 11/16 23:00 JST、残り4日)。",
    "🆕 Perpl (Monad): Purple Summer の mPoints を3週間延長 (週5万mPoints、計15万追加+最終トーナメント)。報酬はMON建てで終了後1週間以内に配布との情報。今から参加できる数少ない案件。",
    "🆕 infiniFi (INFI): Season1/2 登録は11/10 15:30 UTCで締切済み。TGEはQ4予定のまま日付未発表 (残工程: トークン文書→対象者公開→最終スナップショット→TGE)。Season3ポイントは継続中。",
    "🆕 Midnight (NIGHT): Glacier Drop の解凍(thaw)期間が12/4終了、その後90日間の猶予期間でポータル閉鎖。既存の請求者は未償還分を確認。",
    "✏️ Saturn: 11/16締切を2つ目のソースでも確認。Season2ポイントはTGEまたは12/8の早い方でスナップショット。",
    "✏️ Predict.fun: 35%即時/100%ステーキングの選択フォーム締切 11/26 09:00 UTC (18:00 JST) を複数ソースで確認。TGE・クレーム新日程は未発表。",
    "✏️ MetaMask: 「オプトイン締切 11/12・当選者は11/26 17:00 CETまでにクレーム開始 (KYC/税務確認あり)」との記載は1ソースのみ。公式サポートでは未確認のため、アプリ内 Rewards タブで要確認。",
    "ℹ️ Binance Alpha: システムアップグレード補償として、11/6 23:59 UTC時点でAlphaポイント200以上のユーザーに計35万ドルを自動配布 (申請不要・配布日未定)。",
    "⏰ 期限が近い順: Saturn登録 11/16 → Perpl最終スナップショット 11/18頃 → Fables 11/20 → Predict.fun選択 11/26 → Doppler 11/28 → Aster / Midnight解凍 12/4 → StandX 12/31。",
    "⚠️ 本日は airdrops.io / cryptoticker.io に直接アクセスできず、検索結果の二次情報に基づく更新。日付は必ず公式チャネルで確認を。",
]


def _build_seed_airdrops() -> list[dict]:
    """手動管理の注目エアドロップ (2026-11-12 時点の検索結果に基づく)。
    ポイント制は必ずしもトークン配布を保証しない。公式サイトで必ず確認すること。"""
    d = "2026-11-12"

    def mk(id_, name, symbol, cat, typ, status, diff, val, desc, tasks, end, url, hot):
        return {
            "id": id_, "name": name, "symbol": symbol, "category": cat, "type": typ,
            "status": status, "difficulty": diff, "estimated_value_usd": val,
            "description": desc, "tasks": tasks, "end_date": end, "logo": "",
            "url": url, "is_hot": hot, "added_date": d, "source": "curated",
        }

    return [
        mk("saturn-strn", "Saturn (STRN)", "STRN", "DeFi", "エアドロップ登録受付中", "active", "easy", 0,
           "Season1/Season2のエアドロップ登録は11/16 9:00 EST(23:00 JST)締切(複数ソースで確認)。TGEは2026年Q4予定で、Season2参加者に総供給の最大5%。"
           "Season2ポイントはTGEまたは12/8の早い方でスナップショット。登録=配布保証ではない(財団明言)。クレームはTGE時に別途開始。登録リンクは公式X(@Saturn_credit)のみ使用。",
           ["公式Xで案内される登録ページでウォレット/Discordを登録(11/16まで)", "Season2ポイントの積み増しはスナップショット(TGEまたは12/8)まで継続"],
           "2026-11-16", "", True),
        mk("aster-stage6", "Aster (ASTER) Stage 6", "ASTER", "DeFi/DEX", "クレーム受付中", "active", "easy", 0,
           "Stage6「Convergence」で6,400万ASTER(総供給の0.8%)を配布。100%ベスト済みクレームは11/4 12:00 UTC〜12/4 12:00 UTC。"
           "Stage6で10,000ポイント以上、かつ4/20〜5/2に6か月ベスティングを選択した参加者が対象。",
           ["対象か公式ページで確認", "12/4 12:00 UTCまでにクレーム"], "2026-12-04", "https://www.asterdex.com/", True),
        mk("fables", "Fables (FABLES)", "FABLES", "DeFi/DEX", "ポイントクレーム", "active", "easy", 0,
           "Robinhood Chain上のDEX(Uniswap v4 Hook)。ポイントクレーム期限は11/20 23:59 UTC。"
           "PROLOGUEの償還も同日まで。10/19 02:00 UTCまでにクレームオプションを保存済みのウォレットのみ対象(新規参加不可)。",
           ["fables.fi でポイントをクレーム(11/20まで)"], "2026-11-20", "https://fables.fi/", True),
        mk("predict-fun", "Predict.fun (PREDICT)", "PREDICT", "予測市場", "TGE延期・配布方法の選択受付", "upcoming", "medium", 0,
           "Binance Alpha/現物上場の延期に合わせ、TGEとSeason1クレームが延期(新日程は未発表、公式Xで告知予定)。即時受取は割当の35%、1年ステーキングなら100%。"
           "選択フォームの締切は11/26 09:00 UTC(18:00 JST)と複数ソースが報道。期限欄はこのフォーム締切で、TGE日ではない。",
           ["35%即時 / 100%(1年)の選択フォームを11/26 09:00 UTCまでに提出", "公式Xで新しいTGE・クレーム日時を確認"],
           "2026-11-26", "https://predict.fun/", True),
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
           "情報が錯綜。Rewards Season1は終了済み。一部カレンダーに「オプトイン締切11/12、当選者は11/26 17:00 CETまでにクレーム開始(KYC・税務確認あり)」との記載があるが、"
           "公式サポートページでは確認できず(単一ソース)。MASKトークン自体は未発表。期待値は低めに見るべき。",
           ["MetaMaskアプリの Rewards タブで参加中キャンペーンの期限を確認", "MetaMaskの利用(Swaps/Perps等)"], "未定", "https://metamask.io/", False),
        mk("perpl-monad", "Perpl (Purple Summer)", "MON", "DeFi/DEX", "取引ポイント(MON報酬)", "active", "medium", 0,
           "Monad上のPerp DEX。7/8開始の16週キャンペーン「Purple Summer」のmPointsを3週間延長(週5万mPoints、計15万追加+最終トーナメント)。"
           "スナップショットは毎週水曜16:00 UTC、最終は11/18前後との情報。報酬はMON建てでキャンペーン終了後1週間以内に配布。延長分の原資は約15万ドル規模と小さめ。取引損失リスクあり。",
           ["Perplでオーガニックな取引を行いmPointsを獲得", "公式ブログ/Discordで最終スナップショット日を確認"],
           "2026-11-18", "https://perpl.xyz/", False),
        mk("infinifi-infi", "infiniFi (INFI)", "INFI", "DeFi", "TGE待ち(登録締切済)", "upcoming", "medium", 0,
           "Season1/2のエアドロップ登録は11/10 15:30 UTCで締切済み(延長なし)、配布は登録済みウォレットのみとの情報。TGEは2026年Q4目標で日付未発表。"
           "創業者が挙げた残工程はトークン文書→対象者公開→最終スナップショット→TGE。Season3ポイントは継続中。",
           ["登録済みの場合: 公式Xで対象者公開・TGE日を待つ", "未登録の場合: Season3ポイント(預入)が次回配布の対象になるか公式発表を確認"],
           "未定", "", False),
        mk("midnight-night", "Midnight (NIGHT) Glacier Drop", "NIGHT", "L1/プライバシー", "償還(解凍)期間", "active", "easy", 0,
           "Glacier Dropの請求自体は2025年10月に終了済み(新規参加不可)。割当は360日かけて4回に分けて解凍され、解凍期間は12/4に終了。"
           "その後90日間の猶予期間(〜2027年3月初旬)でポータルが閉鎖されるため、請求済みの人は未償還トランシェを要確認。",
           ["公式ポータルで解凍済みNIGHTを償還", "猶予期間終了(2027年3月初旬)までに全トランシェを回収"],
           "2026-12-04", "https://midnight.network/", False),
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
