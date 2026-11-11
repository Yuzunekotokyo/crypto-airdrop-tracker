from datetime import datetime, timedelta, timezone

import pytest

import config
import signal_checker
from notifier.gmail import build_signal_email
from signals.engine import SignalConfig, evaluate, fib, kijun, sma


def make_candles(closes, wick=0.01):
    return [
        {"ts": i * 604800, "open": c, "high": c * (1 + wick), "low": c * (1 - wick), "close": c}
        for i, c in enumerate(closes)
    ]


def pullback(last_price):
    """57,800 → 約100,000 まで上昇後に押している相場 (最後の1本が現在値)"""
    up = [57800 + (100000 - 57800) * i / 19 for i in range(20)]
    down = [97000, 93000, 90000, 88000, 86000, 84000, 82000]
    return make_candles([60000] * 10 + up + down + [last_price])


def test_indicators():
    c = make_candles(list(range(1, 41)), wick=0)
    assert sma(c, 25) == sum(range(16, 41)) / 25
    assert kijun(c) == (40 + 15) / 2
    assert fib(57800, 100000, 0.5) == 78900


def test_statuses_follow_price_into_and_through_zone():
    cfg = SignalConfig(confluence_pct=0.08)
    zone = evaluate(pullback(81000), cfg)["zone"]
    assert zone["strength"] == 3
    assert evaluate(pullback(zone["high"] * 1.10), cfg)["status"] == "NONE"
    assert evaluate(pullback(zone["high"] * 1.02), cfg)["status"] == "WATCH"
    long = evaluate(pullback((zone["high"] + zone["low"]) / 2), cfg)
    assert long["status"] == "LONG"
    assert long["plan"]["stop"] < long["plan"]["entry"] < long["plan"]["targets"][-1]["price"]
    assert evaluate(pullback(zone["low"] * 0.95), cfg)["status"] == "BROKEN"


def test_wick_touch_counts_as_long_while_price_is_still_near():
    cfg = SignalConfig(confluence_pct=0.08)
    zone = evaluate(pullback(81000), cfg)["zone"]
    candles = pullback(zone["high"] * 1.02)
    assert evaluate(candles, cfg)["status"] == "WATCH"
    candles[-1]["low"] = zone["high"]
    r = evaluate(candles, cfg)
    assert r["status"] == "LONG" and r["touched"]


def test_swing_uses_latest_up_leg_not_the_older_bigger_top():
    # 126k → 57.8k → 87.4k → 押し。フィボの起点は 57.8k、終点は 87.4k になるべき
    closes = [126000, 110000, 90000, 70000, 60000, 58000, 65000, 75000, 87000, 82000, 78000, 74000]
    r = evaluate(make_candles([100000] * 20 + closes, wick=0.0), SignalConfig())
    assert (r["swing_low"], r["swing_high"]) == (58000, 87000)


def test_no_zone_when_levels_are_far_apart():
    r = evaluate(pullback(81000), SignalConfig(confluence_pct=0.001))
    assert r["zone"] is None and r["status"] == "NONE"


def test_below_when_previous_week_already_closed_under_zone():
    candles = pullback(81000)
    candles[-2]["close"] = 50000
    assert evaluate(candles, SignalConfig(confluence_pct=0.2))["status"] == "BELOW"


def test_manual_swing_override():
    r = evaluate(pullback(81000), SignalConfig(swing_low=50000, swing_high=90000))
    assert r["levels"]["fib50"] == 70000


def test_should_notify_dedup():
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(hours=1)).isoformat()
    old = (now - timedelta(hours=48)).isoformat()
    sn = signal_checker.should_notify
    assert sn("LONG", {}, now, 24)
    assert not sn("NONE", {}, now, 24)
    assert not sn("LONG", {"status": "LONG"}, now, 24)
    assert not sn("LONG", {"status": "WATCH", "notified": {"LONG": recent}}, now, 24)
    assert sn("LONG", {"status": "WATCH", "notified": {"LONG": old}}, now, 24)
    assert not sn("WATCH", {"status": "LONG", "notified": {"LONG": recent}}, now, 24)
    assert not sn("BROKEN", {"status": "NONE"}, now, 24)
    assert sn("BROKEN", {"status": "LONG", "notified": {"LONG": recent}}, now, 24)


@pytest.fixture
def runner(tmp_path, monkeypatch):
    sent = []
    box = {"price": 81000, "ok": True}
    monkeypatch.setattr(config, "SIGNAL_STATE_FILE", str(tmp_path / "state.json"))
    monkeypatch.setattr(config, "SIGNAL_SYMBOLS", ["BTC"])
    monkeypatch.setattr(config, "SIGNAL_CONFLUENCE_PCT", 0.08)
    monkeypatch.setattr(signal_checker, "fetch_weekly_candles", lambda s: (pullback(box["price"]), "test"))
    monkeypatch.setattr(signal_checker, "send_signal_alert", lambda r: (sent.append(r["status"]), box["ok"])[1])
    return box, sent


def test_runner_sends_once_per_state_change(runner):
    box, sent = runner
    zone = evaluate(pullback(81000), SignalConfig(confluence_pct=0.08))["zone"]
    for price in (zone["high"] * 1.02, zone["high"] * 1.02, zone["low"], zone["low"], zone["low"] * 0.9):
        box["price"] = price
        signal_checker.run_signal_check()
    assert sent == ["WATCH", "LONG", "BROKEN"]


def test_runner_retries_after_failed_send(runner):
    box, sent = runner
    box["ok"] = False
    assert signal_checker.run_signal_check()["BTC"]["email_failed"]
    box["ok"] = True
    signal_checker.run_signal_check()
    signal_checker.run_signal_check()
    assert sent == ["LONG", "LONG"]


def test_runner_reports_fetch_failure(runner, monkeypatch):
    def boom(symbol):
        raise RuntimeError("down")

    monkeypatch.setattr(signal_checker, "fetch_weekly_candles", boom)
    assert signal_checker.run_signal_check() == {"BTC": {"error": "down"}}


def test_email_contains_levels_and_plan():
    r = evaluate(pullback(81000), SignalConfig(confluence_pct=0.08))
    r.update(symbol="BTC", source="test")
    subject, html, plain = build_signal_email(r)
    assert "BTC LONGシグナル" in subject and "$81,000" in subject
    assert "週足 25MA" in html and "損切り目安" in html and "損切り目安" in plain
