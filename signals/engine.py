"""
週足コンフルエンス・シグナル判定 (純粋関数のみ、通信なし)。

考え方: 押し目買いの「支持線」が複数重なった価格帯 (ゾーン) を探す。
  1. フィボナッチ 0.5 (直近スイング安値 → 高値の半値押し)
  2. 週足 一目均衡表の基準線 (過去26週の高値と安値の中間)
  3. 週足 25MA (過去25週の終値平均)
この3本が近い位置に集まり、価格がそこまで落ちてきたら LONG シグナル。
"""

from dataclasses import dataclass
from itertools import combinations

LEVEL_LABELS = {"fib50": "フィボ0.5 (半値押し)", "kijun": "週足 雲基準線", "sma25": "週足 25MA"}


@dataclass
class SignalConfig:
    confluence_pct: float = 0.04  # ゾーンとみなす支持線同士の最大の開き
    min_levels: int = 3           # 何本重なればシグナルにするか (2 or 3)
    watch_pct: float = 0.03       # ゾーン上限までこの距離に入ったら「接近中」
    break_pct: float = 0.02       # ゾーン下限をこれだけ割ったら「割れ」
    touch_pct: float = 0.005      # ゾーン上限のこの手前まで来たら「到達」とみなす誤差
    swing_lookback: int = 52      # スイング安値を探す週数
    swing_low: float | None = None   # 手動指定 (例: 57800)
    swing_high: float | None = None


def sma(candles: list[dict], n: int) -> float:
    return sum(c["close"] for c in candles[-n:]) / n


def kijun(candles: list[dict], n: int = 26) -> float:
    window = candles[-n:]
    return (max(c["high"] for c in window) + min(c["low"] for c in window)) / 2


def find_swing(candles: list[dict], cfg: SignalConfig) -> tuple[float, float]:
    """
    直近の上昇スイングの (安値, 高値)。
    安値 = 直近lookback週の最安値、高値 = その安値を付けた後の最高値。
    いま最安値を更新中 (= 安値の後に上昇がまだ無い) の場合は、
    期間内の最高値とそれ以前の最安値にフォールバックする。
    """
    start = max(0, len(candles) - cfg.swing_lookback)
    idx = range(start, len(candles))
    lo_idx = min(idx, key=lambda i: candles[i]["low"])
    hi_idx = max(range(lo_idx, len(candles)), key=lambda i: candles[i]["high"])
    if hi_idx == lo_idx:
        hi_idx = max(idx, key=lambda i: candles[i]["high"])
        lo_idx = min(range(max(0, hi_idx - cfg.swing_lookback), hi_idx + 1), key=lambda i: candles[i]["low"])
    return cfg.swing_low or candles[lo_idx]["low"], cfg.swing_high or candles[hi_idx]["high"]


def fib(low: float, high: float, ratio: float) -> float:
    return high - (high - low) * ratio


def _best_cluster(levels: dict[str, float], cfg: SignalConfig) -> list[str] | None:
    """開きが confluence_pct 以内で、最も本数が多く・最も密な支持線の組を返す。"""
    for size in range(len(levels), cfg.min_levels - 1, -1):
        best = None
        for names in combinations(levels, size):
            vals = [levels[n] for n in names]
            spread = (max(vals) - min(vals)) / (sum(vals) / len(vals))
            if spread <= cfg.confluence_pct and (best is None or spread < best[0]):
                best = (spread, list(names))
        if best:
            return best[1]
    return None


def evaluate(candles: list[dict], cfg: SignalConfig | None = None) -> dict:
    """
    status:
      NONE   … 支持線が重なっていない / 価格がまだ遠い
      WATCH  … ゾーンに接近中 (予告)
      LONG   … ゾーンに到達 = 買いシグナル
               (今週の安値がタッチ済みで、まだゾーン近くにいる場合も含む → touched=True)
      BROKEN … ゾーンを下に割った (シナリオ無効)
      BELOW  … 先週終値の時点で既にゾーンの下 (支持線として機能していない)
    """
    cfg = cfg or SignalConfig()
    if len(candles) < 30:
        raise ValueError("週足が30本以上必要です")

    price = candles[-1]["close"]
    prev_close = candles[-2]["close"]
    swing_low, swing_high = find_swing(candles, cfg)
    levels = {
        "fib50": fib(swing_low, swing_high, 0.5),
        "kijun": kijun(candles),
        "sma25": sma(candles, 25),
    }
    result = {
        "price": price,
        "levels": levels,
        "swing_low": swing_low,
        "swing_high": swing_high,
        "status": "NONE",
        "zone": None,
    }

    cluster = _best_cluster(levels, cfg)
    if not cluster:
        return result

    vals = [levels[n] for n in cluster]
    zone_lo, zone_hi = min(vals), max(vals)
    stop = zone_lo * (1 - cfg.break_pct)
    result["zone"] = {
        "low": zone_lo,
        "high": zone_hi,
        "levels": cluster,
        "strength": len(cluster),
        "distance_pct": (price - zone_hi) / price,
    }

    touch_line = zone_hi * (1 + cfg.touch_pct)
    near = (price - zone_hi) / price <= cfg.watch_pct
    if prev_close < zone_lo:
        result["status"] = "BELOW"
    elif price < stop:
        result["status"] = "BROKEN"
    elif price <= touch_line:
        result["status"] = "LONG"
    elif near and candles[-1]["low"] <= touch_line:
        # 15分間隔の監視ではヒゲを取り逃がすので、週足の安値でタッチを拾う
        result["status"] = "LONG"
        result["touched"] = True
    elif near:
        result["status"] = "WATCH"

    if result["status"] in ("WATCH", "LONG"):
        entry = price if result["status"] == "LONG" else zone_hi
        risk = entry - stop
        targets = []
        for label, tp in (("フィボ0.382", fib(swing_low, swing_high, 0.382)), ("直近高値", swing_high)):
            if tp > entry and risk > 0:
                targets.append({"label": label, "price": tp, "rr": (tp - entry) / risk})
        result["plan"] = {"entry": entry, "stop": stop, "targets": targets}
    return result
