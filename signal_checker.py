"""
週足コンフルエンス・シグナルの監視ランナー。

  python signal_checker.py            # 判定し、状態が変わったときだけメール
  python signal_checker.py --dry-run  # 判定結果を表示するだけ (メール・状態保存なし)
  python signal_checker.py --force    # 現在の判定をシグナル無しでも必ずメール (疎通確認用)
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone

import config
from fetchers.market import fetch_weekly_candles
from notifier.gmail import send_signal_alert
from signals.engine import SignalConfig, evaluate

logger = logging.getLogger(__name__)

NOTIFY_STATUSES = ("WATCH", "LONG", "BROKEN")


def _load_state() -> dict:
    try:
        with open(config.SIGNAL_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save_state(state: dict):
    os.makedirs(os.path.dirname(config.SIGNAL_STATE_FILE), exist_ok=True)
    with open(config.SIGNAL_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _hours_since(iso: str | None, now: datetime) -> float:
    if not iso:
        return float("inf")
    return (now - datetime.fromisoformat(iso)).total_seconds() / 3600


def should_notify(status: str, prev: dict, now: datetime, cooldown_h: float) -> bool:
    """同じ内容のメールを連打しないための判定。prev は前回保存した銘柄ごとの状態。"""
    if status not in NOTIFY_STATUSES or status == prev.get("status"):
        return False
    notified = prev.get("notified", {})
    if _hours_since(notified.get(status), now) < cooldown_h:
        return False  # 境界付近を行き来しても同種の通知は cooldown 中は送らない
    if status == "WATCH" and _hours_since(notified.get("LONG"), now) < cooldown_h:
        return False  # LONG 通知直後にゾーン上へ戻っただけなら予告は不要
    if status == "BROKEN" and not (notified.get("LONG") or notified.get("WATCH")):
        return False  # 追っていなかったゾーンの「割れ」は知らせない
    return True


def _config_for(index: int) -> SignalConfig:
    return SignalConfig(
        confluence_pct=config.SIGNAL_CONFLUENCE_PCT,
        min_levels=config.SIGNAL_MIN_LEVELS,
        watch_pct=config.SIGNAL_WATCH_PCT,
        break_pct=config.SIGNAL_BREAK_PCT,
        swing_low=config.SIGNAL_SWING_LOW if index == 0 else None,
        swing_high=config.SIGNAL_SWING_HIGH if index == 0 else None,
    )


def run_signal_check(dry_run: bool = False, force: bool = False) -> dict:
    """全銘柄を判定。Returns: {symbol: 判定結果}。取得失敗した銘柄は {"error": ...}。"""
    now = datetime.now(timezone.utc)
    state = _load_state()
    results = {}

    for i, symbol in enumerate(config.SIGNAL_SYMBOLS):
        try:
            candles, source = fetch_weekly_candles(symbol)
            result = evaluate(candles, _config_for(i))
        except Exception as e:
            logger.error(f"{symbol}: 判定失敗 — {e}")
            results[symbol] = {"error": str(e)}
            continue

        result.update(symbol=symbol, source=source, checked_at=now.isoformat())
        results[symbol] = result
        status = result["status"]
        zone = result["zone"]
        logger.info(
            f"{symbol}: {status} 現在値 ${result['price']:,.0f}"
            + (f" / ゾーン ${zone['low']:,.0f}–${zone['high']:,.0f} ({zone['strength']}本)" if zone else " / ゾーンなし")
        )
        if dry_run:
            continue

        prev = state.get(symbol, {})
        notified = dict(prev.get("notified", {}))
        new_status = status
        if force or should_notify(status, prev, now, config.SIGNAL_COOLDOWN_HOURS):
            if send_signal_alert(result):
                notified[status] = now.isoformat()
            else:
                new_status = prev.get("status")  # 送れなかったら次回また試す
                results[symbol]["email_failed"] = True
        if status in ("NONE", "BELOW") and prev.get("status") in ("BROKEN", "BELOW"):
            notified = {}  # ゾーンから離れたら履歴をリセットし、次のゾーンに備える
        state[symbol] = {**result, "status": new_status, "notified": notified}

    if not dry_run:
        _save_state(state)
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    out = run_signal_check(dry_run="--dry-run" in sys.argv, force="--force" in sys.argv)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    # データ取得やメール送信に失敗したら終了コード1 (GitHub Actions で気づけるように)
    sys.exit(1 if any("error" in r or r.get("email_failed") for r in out.values()) else 0)
