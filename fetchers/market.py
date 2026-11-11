"""
週足ローソク足 (OHLC) の取得。
APIキー不要の公開エンドポイントを順に試し、最初に成功したものを使う。
返り値は古い順の list[dict]: {"ts": 秒, "open", "high", "low", "close"}
(最後の1本は進行中の週足 = close が現在値)
"""

import logging

import requests

logger = logging.getLogger(__name__)

TIMEOUT = 15
HEADERS = {"accept": "application/json", "User-Agent": "signal-bot/1.0"}


def _candle(ts, o, h, l, c) -> dict:
    return {"ts": int(ts), "open": float(o), "high": float(h), "low": float(l), "close": float(c)}


def _binance(base: str, limit: int) -> list[dict]:
    r = requests.get(
        "https://data-api.binance.vision/api/v3/klines",
        params={"symbol": f"{base}USDT", "interval": "1w", "limit": limit},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return [_candle(k[0] // 1000, k[1], k[2], k[3], k[4]) for k in r.json()]


def _okx(base: str, limit: int) -> list[dict]:
    r = requests.get(
        "https://www.okx.com/api/v5/market/candles",
        params={"instId": f"{base}-USDT", "bar": "1Wutc", "limit": min(limit, 300)},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    body = r.json()
    if body.get("code") != "0":
        raise RuntimeError(f"OKX error: {body.get('msg')}")
    rows = sorted(body["data"], key=lambda k: int(k[0]))  # OKXは新しい順で返す
    return [_candle(int(k[0]) // 1000, k[1], k[2], k[3], k[4]) for k in rows]


def _kraken(base: str, limit: int) -> list[dict]:
    pair = f"{'XBT' if base == 'BTC' else base}USD"
    r = requests.get(
        "https://api.kraken.com/0/public/OHLC",
        params={"pair": pair, "interval": 10080},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    body = r.json()
    if body.get("error"):
        raise RuntimeError(f"Kraken error: {body['error']}")
    rows = next(v for k, v in body["result"].items() if k != "last")
    return [_candle(k[0], k[1], k[2], k[3], k[4]) for k in rows][-limit:]


SOURCES = [("binance", _binance), ("okx", _okx), ("kraken", _kraken)]


def fetch_weekly_candles(base: str = "BTC", limit: int = 260) -> tuple[list[dict], str]:
    """週足を取得。Returns: (candles, 取得元の名前)。全滅なら RuntimeError。"""
    base = base.upper()
    errors = []
    for name, fn in SOURCES:
        try:
            candles = fn(base, limit)
            if len(candles) >= 30:
                return candles, name
            errors.append(f"{name}: データ不足 ({len(candles)}本)")
        except Exception as e:  # 次の取得元へフォールバック
            errors.append(f"{name}: {e}")
            logger.warning(f"{name} からの週足取得に失敗: {e}")
    raise RuntimeError("週足データを取得できませんでした — " + " / ".join(errors))
