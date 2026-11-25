"""
Airdrop情報をWeb/APIから収集するモジュール。
現在はairdrops.ioのパブリックページとCoinGeckoトレンドを組み合わせて使用。
"""

import requests
import logging
from datetime import datetime
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


# 手動キュレーションの最終確認日と、その日の更新メモ (サイト最上部のUPDATEに表示)
CURATED_UPDATED = "2026-11-25"
CURATED_NOTES = [
    {"kind": "deadline", "text": "Doppler Finance (XDP) のGenesisエアドロップ請求は 11/28 12:00 UTC 締切。未請求分は失効。"},
    {"kind": "deadline", "text": "Aster (ASTER) Stage 6 の請求期限は情報源により 11/28 または 12/4。早い方の 11/28 までに請求を。"},
    {"kind": "deadline", "text": "Midnight (NIGHT) Glacier Drop の解凍期間は 12/4 終了 (その後90日の猶予期間)。"},
    {"kind": "hot", "text": "Extended (XTEN): 3億XTEN (供給量の30%) の割当チェッカー公開中。12/31 23:59 UTC までにアプリで規約へ署名しないと割当は失効。TGE日は未発表。"},
    {"kind": "hot", "text": "Predict.fun (PREDICT): 11/17 にTGEとSeason 1請求を延期 (2〜4週間後めど)。新日程は未確定、偽の請求サイトに注意。"},
    {"kind": "new", "text": "新着: Bitbase「ORIGIN」ポイントシーズン (11/4〜2027/5/4、毎週100万ポイント配布)。将来のトークン・エアドロップ計画が報じられているが公式詳細は未確認。"},
    {"kind": "new", "text": "新着: Zest Protocol (ZEST) Season 1 の請求受付中。締切は 12/10 (12/19 との記載もあり要確認)。"},
    {"kind": "ended", "text": "終了: Treehouse (TREE) Season 2 請求 (11/25 07:00 UTC)、Fables ポイント交換 (11/20)。"},
    {"kind": "removed", "text": "一覧を全面刷新: 配布済みの旧案件 (LayerZero, Scroll, zkSync, Hyperliquid, EigenLayer, Movement) を削除。Hyperliquid「Season 2」は公式発表なしのため掲載見送り。"},
]


def _a(id, name, symbol, category, type_, status, difficulty, description, tasks,
       end_date, url, is_hot=False, added_date=CURATED_UPDATED, value=0):
    return {
        "id": id, "name": name, "symbol": symbol, "category": category, "type": type_,
        "status": status, "difficulty": difficulty, "estimated_value_usd": value,
        "description": description, "tasks": tasks, "end_date": end_date, "logo": "",
        "url": url, "is_hot": is_hot, "added_date": added_date, "source": "curated",
    }


def _build_seed_airdrops() -> list[dict]:
    """手動管理の注目エアドロップ一覧 (最終確認日: CURATED_UPDATED)。

    推定価値は根拠のある数字が無い限り 0 (=未定) とする。
    日付はアグリゲーター経由の情報を含むため、参加前に必ず公式発表で確認すること。
    """
    return [
        _a("extended-xten", "Extended (XTEN)", "XTEN", "DeFi/DEX", "確定エアドロップ", "active", "easy",
           "Perp DEX。ポイント保有者に3億XTEN (総供給10億の30%) を配布、TGE時に全量アンロック。"
           "11/11に割当チェッカー公開。期限までに規約へ署名しない分はエコシステム基金へ移る。TGE日は未発表。",
           ["Extendedアプリで割当を確認", "12/31 23:59 UTC までに規約へ署名 (受諾)", "TGE日程は公式発表を待つ"],
           "2026-12-31", "https://extended.exchange/", is_hot=True),
        _a("predict-fun", "Predict.fun (PREDICT)", "PREDICT", "予測市場", "確定エアドロップ", "upcoming", "easy",
           "予測市場。Season 1エアドロップ確定済みだが、11/17にTGEと請求開始を延期 (2〜4週間後めど、新日程未確定)。"
           "TGEまで「即時35%受取」か「12か月ベスティング」を選択・変更可能。請求開始後の受付は30日間との報道。",
           ["公式サイトで割当を確認", "即時35% or 12か月ベスティングを選択", "公式Xで新しい請求日を確認 (偽サイト注意)"],
           "未定 (12月見込み)", "https://predict.fun/", is_hot=True),
        _a("polymarket-poly", "Polymarket (POLY)", "POLY", "予測市場", "ポイント/利用実績", "active", "medium",
           "最大手の予測市場。CMOが「トークンもエアドロップもある」と発言しPOLYは確定視されているが、"
           "日程・配分・条件は未公表 (10月時点)。取引実績が基準になるとの見方が多い。",
           ["Polymarketで継続的に取引", "複数カテゴリの市場に参加", "流動性提供 (指値注文)"],
           "未定", "https://polymarket.com/", is_hot=True),
        _a("doppler-xdp", "Doppler Finance (XDP)", "XDP", "DeFi", "請求受付中", "active", "easy",
           "Genesisエアドロップの請求受付中。2026/7/30までにBaseアドレスを登録済みのユーザーのみ対象。"
           "11/28 12:00 UTC までに請求しないと失効。",
           ["対象か確認 (7/30までに登録済みか)", "公式ポータルで請求"],
           "2026-11-28", "https://doppler.finance/"),
        _a("aster-stage6", "Aster (ASTER) Stage 6", "ASTER", "DeFi/DEX", "請求受付中", "active", "easy",
           "Stage 6で6,400万ASTER (供給量の0.8%) を1万ポイント以上の参加者へ配布。"
           "請求期限は情報源により11/28 12:00 UTCまたは12/4と食い違いあり — 早い方を期限と考えるのが安全。",
           ["公式サイトで請求", "期限は公式で再確認"],
           "2026-11-28", "https://www.asterdex.com/"),
        _a("midnight-night", "Midnight (NIGHT)", "NIGHT", "インフラ", "請求受付中", "active", "easy",
           "Glacier Drop / Scavenger Mineで獲得したNIGHTの償還。解凍期間は12/4に終了し、その後90日の猶予期間。"
           "新規の獲得受付は終了済み (既存の対象者向け)。",
           ["対応ウォレットで償還ポータルに接続", "解凍済みトランシェを償還"],
           "2026-12-04", "https://midnight.network/"),
        _a("zest-zest", "Zest Protocol (ZEST)", "ZEST", "DeFi", "請求受付中", "active", "easy",
           "Season 1エアドロップの請求受付中。締切は12/10との情報 (12/19との記載もあり、公式で要確認)。",
           ["公式サイトで対象・割当を確認", "締切までに請求"],
           "2026-12-10", "https://www.zestprotocol.com/"),
        _a("standx-dusd", "StandX (DUSD)", "DUSD", "DeFi/DEX", "請求受付中", "active", "easy",
           "TGEを中止し、ロックアップなしのエアドロップに変更。請求は11/1開始、12/31 08:00 UTCまで。",
           ["公式サイトで請求"],
           "2026-12-31", "https://standx.com/"),
        _a("bitbase-origin", "Bitbase ORIGIN", "", "取引所", "ポイントプログラム", "active", "medium",
           "取引所Bitbaseの初回ポイントシーズン (11/4〜2027/5/4の26週間)。毎週100万ポイントを貢献度に応じて配布、自動参加。"
           "ポイントを基にした取引所トークンのエアドロップ計画が報じられている (11/18報道)。トークン詳細は未公表。",
           ["Bitbaseで取引 (自動エンロール)", "継続的な利用でポイント蓄積", "bitbase.com/points で順位確認"],
           "2027-05-04", "https://bitbase.com/points"),
        _a("infinifi-infi", "infiniFi (INFI)", "INFI", "DeFi", "確定エアドロップ", "upcoming", "medium",
           "Season 1/2のウォレット登録は11/10に締切済み。TGEはQ4 2026見込みだが日付未発表、初回トークンは凍結状態で届く予定。"
           "未請求分はSeason 3報酬に上乗せ — Season 3は引き続き参加可能。",
           ["登録済みならTGE発表を待つ", "Season 3でポイント獲得を継続"],
           "未定 (Q4見込み)", "https://infinifi.xyz/"),
        _a("saturn-strn", "Saturn (STRN)", "STRN", "DeFi", "確定エアドロップ", "upcoming", "easy",
           "エアドロップ登録は11/16に締切済み。請求はTGE時に開始予定だが、TGE日・上場先は未発表。",
           ["登録済みならTGE発表を待つ"],
           "未定", "https://www.coingabbar.com/en/saturn-airdrop-registration-closed-strn-claim-token-launch-soon"),
        _a("base-token", "Base", "", "Layer2", "未確定 (観測)", "active", "easy",
           "CoinbaseのL2。トークン発行を「検討」と示唆したのみで、発行もエアドロップも未確定。期待先行の案件。",
           ["Base上でdApps利用", "ブリッジ・スワップ等のオンチェーン実績"],
           "未定", "https://www.base.org/"),
        _a("metamask-rewards", "MetaMask Rewards (MASK)", "MASK", "ウォレット", "未確定 (観測)", "active", "easy",
           "MetaMaskのリワードポイント制度。将来のMASKトークンとの関連が示唆されているが、発行・配布は未確定。",
           ["MetaMask内でスワップ/ブリッジ/Perps利用", "リワードポイントを蓄積"],
           "未定", "https://metamask.io/"),
        _a("treehouse-tree", "Treehouse (TREE) Season 2", "TREE", "DeFi", "請求終了", "ended", "easy",
           "Season 2 (2,310万TREE) の請求は11/25 07:00 UTCで終了。未請求分はトレジャリーへ。",
           [], "2026-11-25", "https://www.treehouse.finance/"),
        _a("fables", "Fables (FABLES)", "FABLES", "その他", "請求終了", "ended", "easy",
           "ポイント→トークン交換とPROLOGUE償還は11/20 23:59 UTCで終了。",
           [], "2026-11-20", "https://cryptoticker.io/en/most-profitable-crypto-airdrops-week-47-2026/"),
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

    # ソート: 終了案件は末尾 → is_hot → estimated_value_usd
    curated.sort(key=lambda x: (x.get("status") == "ended", not x.get("is_hot"), -x.get("estimated_value_usd", 0)))

    return curated, new_items
