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
CURATED_UPDATED = "2026-11-27"
CURATED_NOTES = [
    {"kind": "hot", "text": "Extended (XTEN): 配布日程が確定。初回バッチは 11/29 に送付、対象になるには 11/29 08:30 UTC (17:30 JST) までにアプリで規約署名と各種確認を完了すること。XTEN/USDCスポット取引は 11/30 15:00 UTC (12/1 0:00 JST) 開始。以降の署名分は順次送付、最終期限は 12/31 23:59 UTC。"},
    {"kind": "deadline", "text": "明日締切: Doppler Finance (XDP) の請求は 11/28 12:00 UTC (21:00 JST) まで。未請求分は失効し、再請求の機会はなし。"},
    {"kind": "hot", "text": "Flop Labs (FLOP): テストネット分のエアドロップ上限は36億FLOPと報道 (マイナー・バリデーター・AIエージェントに均等3分割)。約90日後に1回のスナップショット、メインネットは2027年Q1予定。前日の「配布量は未公表」を更新。"},
    {"kind": "new", "text": "Antseed (ANTS) を追加 — AI利用マーケットプレイス。有料のAI利用でポイントが貯まり、毎週木曜にANTSを請求できる (10/26開始)。実費がかかる点、請求したANTSは現時点で譲渡・売却不可との情報、報酬は運営裁量で変更・停止されうる点に注意。"},
    {"kind": "deadline", "text": "Predict.fun (PREDICT): Binance Wallet経由の受取方式フォームは 11/26 に締切済み。TGE・請求の新日程は引き続き未発表 (11/17の延期時点で「2〜4週間後」)。アプリ側の受取方式はTGEまで変更可能。"},
    {"kind": "deadline", "text": "来週の締切: 12/4 12:00 UTC に Aster (ASTER) Stage 6 の請求期限、同日 Midnight (NIGHT) の解凍期間終了。12/10 に Zest (ZEST) の請求期限。"},
    {"kind": "removed", "text": "Treehouse (TREE) Season 2 は 11/25 に請求終了のため一覧から削除。Variational (VAR) はTGE日が引き続き未発表 (Q4 2026予定)。"},
]

_PREV = "2026-11-25"  # 前回から掲載している案件の追加日


def _a(id, name, symbol, category, type_, status, difficulty, description, tasks,
       end_date, url, is_hot=False, added_date=_PREV, value=0):
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
    new = CURATED_UPDATED
    return [
        _a("extended-xten", "Extended (XTEN)", "XTEN", "DeFi/DEX", "確定エアドロップ", "active", "easy",
           "Perp DEX。【初回送付は11/29、取引開始は11/30】Xpoints保有者に3億XTEN (総供給10億の30%、1 Xpoint≒4.29 XTEN) を配布、TGE時に全量アンロック。"
           "11/29 08:30 UTC (17:30 JST) までに規約署名と各種確認を済ませると初回バッチに入り、取引開始前に着金。XTEN/USDCスポットは11/30 15:00 UTC (12/1 0:00 JST) 開始と報道。"
           "以降の署名分は順次送付。署名期限は12/31 23:59 UTCで、未署名分は失効。ステーキング中・解除中のトークンは7日間移転不可、EU居住者は当初スポット取引不可との報道。"
           "請求はExtendedアプリ内のみ (偽チェッカーの報告あり)。",
           ["Extendedアプリで割当を確認", "11/29 08:30 UTC (17:30 JST) までに規約へ署名 (初回バッチ入り)", "11/30 15:00 UTC の取引開始を公式Xで確認", "最終期限は12/31 23:59 UTC"],
           "2026-12-31", "https://extended.exchange/", is_hot=True),
        _a("flop-labs", "Flop Labs (FLOP)", "FLOP", "AI/インフラ", "テストネット", "active", "medium",
           "アーサー・ヘイズ氏が率いるAI計算 (推論) ブロックチェーン。テストネットが11/24 07:00 UTCに開始 (約90日間との情報)。承認・ウェイトリストなし、実資金不要。"
           "エージェントが毎日フォーセットからテストネットFLOPを受け取り、推論に使った量でエアドロップを計測 (保有のみ・Devnet分は対象外)。開始直後で機能は順次有効化中。"
           "テストネット分のエアドロップ上限は36億FLOP (マイナー・バリデーター・AIエージェントに均等3分割) と報道。終了時に1回のスナップショット、メインネットは2027年Q1予定。個別の配分式は未公表、ホワイトペーパーも未整備との指摘あり。",
           ["公式ドキュメント (docs.flop.network) で手順と稼働状況を確認", "フォーセットでテストネットFLOPを毎日取得", "エージェントで推論にFLOPを消費", "非公式ツール・偽サイトに注意"],
           "未定 (2027年2月ごろまで)", "https://x.com/flop_labs", is_hot=True, added_date="2026-11-26"),
        _a("variational-var", "Variational (VAR)", "VAR", "DeFi/DEX", "確定エアドロップ", "active", "medium",
           "Arbitrum上のPerp DEX。VAR供給量の32%をジェネシス・エアドロップとしてポイント保有者に比例配布、TGE時に全量アンロック。"
           "TGEはQ4 2026予定 (Q3から延期、日付未発表)。ポイントはTGEまで毎週15万ポイント配布。1ポイント以上で請求対象、未請求分はバーン。",
           ["ArbitrumウォレットでUSDCを入金して取引", "TGE前に利用規約へ署名", "公式XでTGE日を確認"],
           "未定 (Q4見込み)", "https://x.com/variational_io/status/2102929439063765192", is_hot=True, added_date="2026-11-26"),
        _a("predict-fun", "Predict.fun (PREDICT)", "PREDICT", "予測市場", "確定エアドロップ", "upcoming", "easy",
           "予測市場。Season 1エアドロップ確定済みだが、11/17にTGEと請求開始を延期 (2〜4週間後めど)。11/27時点でも新日程は未発表。"
           "アプリ側はTGEまで「即時35%」か「12か月分割で100%」を選択・変更可能。Binance Wallet経由のポイント保有者向け選択フォームは11/26に締切済み。"
           "TGE前に請求を促すページは偽物。",
           ["公式サイトで割当を確認", "即時35% or 12か月ベスティングを選択", "公式Xで新しい請求日を確認 (偽サイト注意)"],
           "未定 (12月見込み)", "https://predict.fun/", is_hot=True),
        _a("doppler-xdp", "Doppler Finance (XDP)", "XDP", "DeFi", "請求受付中", "active", "easy",
           "【明日締切】Genesisエアドロップの請求受付中。登録済みのBaseウォレットのみ対象 (登録は締切済み)。"
           "11/28 12:00 UTC (21:00 JST) までに請求しないと失効。",
           ["対象か確認 (登録済みか)", "公式ポータルで請求"],
           "2026-11-28", "https://app.doppler.finance/"),
        _a("aster-stage6", "Aster (ASTER) Stage 6", "ASTER", "DeFi/DEX", "請求受付中", "active", "easy",
           "Stage 6「Convergence」で6,400万ASTER (供給量の0.8%) を1万ポイント以上の参加者へ配布。"
           "ベスティング選択者向けの請求は11/4開始、12/4 12:00 UTCまで (複数媒体で一致)。11/28とする古い報道もあるため早めの請求が安全。",
           ["公式サイト (asterdex.com) で請求", "期限は公式ページで再確認"],
           "2026-12-04", "https://www.asterdex.com/"),
        _a("midnight-night", "Midnight (NIGHT)", "NIGHT", "インフラ", "請求受付中", "active", "easy",
           "Glacier Drop / Scavenger Mineで獲得したNIGHTの償還。解凍期間は12/4に終了し、その後90日の猶予期間。"
           "新規の獲得受付は終了済み (既存の対象者向け)。",
           ["対応ウォレットで償還ポータルに接続", "解凍済みトランシェを償還"],
           "2026-12-04", "https://midnight.network/"),
        _a("zest-zest", "Zest Protocol (ZEST)", "ZEST", "DeFi", "請求受付中", "active", "easy",
           "Season 1エアドロップの請求受付中 (11/19 12:00 UTC開始)。締切は公式リマインダーによれば12/10、未請求分はトレジャリーへ。"
           "対象は5/13スナップショット時点のポイント保有者のみ。",
           ["公式サイトで対象・割当を確認", "12/10までに請求"],
           "2026-12-10", "https://www.zestprotocol.com/"),
        _a("standx-dusd", "StandX (DUSD)", "DUSD", "DeFi/DEX", "請求受付中", "active", "easy",
           "TGEを中止し、ロックアップなしのエアドロップに変更。請求は11月初旬から受付中、12/31 08:00 UTCまで。チェッカーと請求は公式サイトのみ。",
           ["公式サイトで請求"],
           "2026-12-31", "https://standx.com/"),
        _a("grass-s2", "Grass Season 2 (USDC)", "GRASS", "DePIN", "請求受付中", "active", "easy",
           "帯域共有DePIN。Season 2報酬はネットワーク収益からUSDCで支払われ、2027/1/22まで請求可能。"
           "既にNetwork Pointsを獲得済みのアカウント向け (新規に条件を満たすことは不可)。少額だったとの報告が多い。",
           ["Grassダッシュボードで対象を確認", "2027/1/22までに請求"],
           "2027-01-22", "https://app.grass.io/", added_date="2026-11-26"),
        _a("usdai-s2", "USD.AI Season 2", "", "DeFi", "請求受付中", "active", "easy",
           "AIインフラ向け融資のステーブルコイン。Season 2エアドロップの請求がArbitrum上で10/20から受付中、2027/1/31まで。既存の割当保有者向け。",
           ["公式サイトで割当を確認", "2027/1/31までに請求"],
           "2027-01-31", "https://www.tradingview.com/news/coinmarketcal:92fbcfa61094b:0-usd-ai-season-2-airdrop-claims-open-on-arbitrum-20-oct-2026-to-31-jan-2027/", added_date="2026-11-26"),
        _a("bitbase-origin", "Bitbase ORIGIN", "", "取引所", "ポイントプログラム", "active", "medium",
           "取引所Bitbaseの初回ポイントシーズン (11/4〜2027/5/4の26週間)。毎週100万ポイントを貢献度に応じて配布、自動参加。"
           "ポイントを基にした取引所トークンのエアドロップ計画が報じられている (開始2週間で1.7万人超がポイント獲得)。トークンの時期・詳細は未公表。",
           ["Bitbaseで取引 (自動エンロール)", "継続的な利用でポイント蓄積", "bitbase.com/points で順位確認"],
           "2027-05-04", "https://bitbase.com/points"),
        _a("antseed-ants", "Antseed (ANTS)", "ANTS", "AI/インフラ", "ポイントプログラム", "active", "medium",
           "AIサービスのマーケットプレイス。10/26開始のAntseed Pointsで、有料のAI利用額×プロバイダー倍率に応じてポイントが貯まり、毎週木曜の締め後にANTSをウォレットへ請求できる。"
           "無料モデル・倍率0のプロバイダーは対象外、1人あたり週次プールの5%が上限。実費がかかる点に注意。"
           "請求したANTSは現時点で譲渡・売却不可との情報があり、報酬は運営の裁量で変更・停止されうる (規約)。",
           ["公式ブログで条件を確認", "対象プロバイダーの有料AIを利用 (実費)", "毎週木曜にANTSを請求"],
           "未定 (毎週配布)", "https://antseed.com/blog/antseed-points/", added_date=new),
        _a("polymarket-poly", "Polymarket (POLY)", "POLY", "予測市場", "ポイント/利用実績", "active", "medium",
           "最大手の予測市場。2025年10月にCMOが「トークンもエアドロップもある」と発言したが、スナップショット日・配分・条件は今も未公表 "
           "(公式ヘルプは「トークンなし・エアドロップ未発表」と記載)。偽のPOLY請求サイトが多いので注意。",
           ["Polymarketで継続的に取引", "複数カテゴリの市場に参加", "流動性提供 (指値注文)"],
           "未定", "https://polymarket.com/"),
        _a("tzero-t0", "Tzero (T0)", "T0", "ローンチパッド", "テストネット", "active", "easy",
           "Base Sepoliaテストネット上のローンチパッド。「Pre-flight Points Season 0」でT0供給量の11%をユーザー向けに確保 (Season 0分5%)。実資金不要。"
           "メインネット移行はLayerZeroの「Zero」メインネット (11/30予定との情報) 以降の見込み。情報源が限られるため公式ドキュメントで要確認。",
           ["テストネットでポイントを獲得 (500ポイント以上が対象との情報)", "公式ドキュメントで条件を確認"],
           "未定", "https://testnet.tzer0.fun/docs/points", added_date="2026-11-26"),
        _a("saturn-strn", "Saturn (STRN)", "STRN", "DeFi", "確定エアドロップ", "upcoming", "easy",
           "Season 1/2のエアドロップ登録は11/16に締切済み。請求はTGE時に開始予定だが、TGE日 (Q4予定)・上場先は未発表。"
           "Season 2のスナップショットはTGE時または12/8のいずれか早い方。請求リンクは公式X (@saturn_credit) のみで告知。",
           ["登録済みならTGE発表を待つ"],
           "未定", "https://www.coingabbar.com/en/saturn-airdrop-registration-closed-strn-claim-token-launch-soon"),
        _a("genlayer-gen", "GenLayer (GEN)", "GEN", "インフラ", "確定エアドロップ", "upcoming", "easy",
           "登録は10/31に締切済み。請求はTGE時に開始 (日付未発表)。請求時に20%、以後毎月20%ずつアンロックされる方式と報じられている。",
           ["登録済みならTGE発表を待つ"],
           "未定", "https://www.coingabbar.com/en/genlayer-airdrop-registration-reopens-gen-tokenomics-out", added_date="2026-11-26"),
        _a("base-token", "Base", "", "Layer2", "未確定 (観測)", "active", "easy",
           "CoinbaseのL2。トークン発行を「検討」と示唆したのみで、発行もエアドロップも未確定。期待先行の案件。",
           ["Base上でdApps利用", "ブリッジ・スワップ等のオンチェーン実績"],
           "未定", "https://www.base.org/"),
        _a("metamask-rewards", "MetaMask Rewards (MASK)", "MASK", "ウォレット", "未確定 (観測)", "active", "easy",
           "MetaMaskのリワードポイント制度。将来のMASKトークンとの関連が示唆されているが、発行・配布は未確定。",
           ["MetaMask内でスワップ/ブリッジ/Perps利用", "リワードポイントを蓄積"],
           "未定", "https://metamask.io/"),
        _a("infinifi-infi", "infiniFi (INFI)", "INFI", "DeFi", "配布済み", "ended", "medium",
           "11/17 15:30 UTCにTGE実施。Season 1/2分は11/10までに登録したウォレットへ直接送付済みで、請求手続きは不要 (「INFIを請求」と誘導するページは偽物)。"
           "Season 3は別枠で継続中との情報。",
           [], "2026-11-17", "https://infinifi.xyz/"),
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
