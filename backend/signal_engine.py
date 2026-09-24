# BTC AI SCANNER V3
# SIGNAL ENGINE

import logging
import math
from typing import Optional


# ============================================================
# INDICATORS
# ============================================================

def ema(values, period):
    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)

    result = sum(values[:period]) / period

    for price in values[period:]:
        result = (
            (price - result) * multiplier
        ) + result

    return result


def rsi(values, period=14):
    if len(values) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(values)):
        change = values[i] - values[i - 1]

        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (
            (avg_gain * (period - 1))
            + gains[i]
        ) / period

        avg_loss = (
            (avg_loss * (period - 1))
            + losses[i]
        ) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss

    return 100 - (
        100 / (1 + rs)
    )


def atr(candles, period=14):
    if len(candles) < period + 1:
        return None

    trs = []

    for i in range(1, len(candles)):

        high = float(candles[i]["high"])
        low = float(candles[i]["low"])

        previous_close = float(
            candles[i - 1]["close"]
        )

        tr = max(
            high - low,
            abs(high - previous_close),
            abs(low - previous_close)
        )

        trs.append(tr)

    if len(trs) < period:
        return None

    return sum(
        trs[-period:]
    ) / period


def macd(values):
    if len(values) < 35:
        return None, None, None

    ema12 = []
    ema26 = []

    multiplier12 = 2 / 13
    multiplier26 = 2 / 27

    current12 = sum(values[:12]) / 12
    current26 = sum(values[:26]) / 26

    ema12.append(current12)
    ema26.append(current26)

    for price in values[12:]:
        current12 = (
            (price - current12) * multiplier12
        ) + current12

        ema12.append(current12)

    for price in values[26:]:
        current26 = (
            (price - current26) * multiplier26
        ) + current26

    length = min(
        len(ema12),
        len(ema26)
    )

    macd_values = []

    for i in range(length):
        macd_values.append(
            ema12[-length + i]
            - ema26[-length + i]
        )

    if len(macd_values) < 9:
        return None, None, None

    signal_line = sum(
        macd_values[:9]
    ) / 9

    multiplier9 = 2 / 10

    for value in macd_values[9:]:
        signal_line = (
            (value - signal_line) * multiplier9
        ) + signal_line

    macd_line = macd_values[-1]

    histogram = (
        macd_line - signal_line
    )

    return (
        macd_line,
        signal_line,
        histogram
    )


# ============================================================
# SAFE FLOAT
# ============================================================

def safe_float(value, default=0.0):

    try:

        if value is None:
            return default

        result = float(value)

        if not math.isfinite(result):
            return default

        return result

    except (
        TypeError,
        ValueError
    ):

        return default


# ============================================================
# SLOPE
# ============================================================

def calculate_slope(values, period=10):

    if len(values) < period:
        return 0.0

    start = safe_float(
        values[-period]
    )

    end = safe_float(
        values[-1]
    )

    if start == 0:
        return 0.0

    return (
        (end - start)
        / start
        * 100
    )


# ============================================================
# TRADE PARAMETERS
# ============================================================

def calculate_trade_parameters(
    price,
    direction,
    atr_value,
    max_risk_usd=2.0,
    risk_reward=3.0
):

    price = safe_float(price)
    atr_value = safe_float(atr_value)

    max_risk_usd = safe_float(
        max_risk_usd,
        2.0
    )

    risk_reward = safe_float(
        risk_reward,
        3.0
    )

    if price <= 0:
        return {
            "valid": False,
            "reason": "Prix invalide"
        }

    if atr_value <= 0:
        return {
            "valid": False,
            "reason": "ATR invalide"
        }

    if max_risk_usd <= 0:
        return {
            "valid": False,
            "reason": "Risque invalide"
        }

    if risk_reward <= 0:
        return {
            "valid": False,
            "reason": "Risk/Reward invalide"
        }

    # --------------------------------------------------------
    # STOP DISTANCE
    # --------------------------------------------------------

    stop_distance = atr_value * 1.20

    minimum_stop = price * 0.0005

    stop_distance = max(
        stop_distance,
        minimum_stop
    )

    # --------------------------------------------------------
    # TARGET
    # --------------------------------------------------------

    target_distance = (
        stop_distance
        * risk_reward
    )

    # --------------------------------------------------------
    # STOP / TP
    # --------------------------------------------------------

    if direction == "LONG":

        stop_loss = (
            price - stop_distance
        )

        take_profit = (
            price + target_distance
        )

    elif direction == "SHORT":

        stop_loss = (
            price + stop_distance
        )

        take_profit = (
            price - target_distance
        )

    else:

        return {
            "valid": False,
            "reason": "Direction invalide"
        }

    # --------------------------------------------------------
    # POSITION
    # --------------------------------------------------------

    quantity = (
        max_risk_usd
        / stop_distance
    )

    position_notional = (
        quantity * price
    )

    actual_risk = (
        stop_distance * quantity
    )

    potential_profit = (
        target_distance * quantity
    )

    return {

        "valid": True,

        "entry_price": float(price),

        "stop_loss": float(
            stop_loss
        ),

        "take_profit": float(
            take_profit
        ),

        # Compatibilité V3
        "stop_price": float(
            stop_loss
        ),

        "target_price": float(
            take_profit
        ),

        "stop_distance": float(
            stop_distance
        ),

        "target_distance": float(
            target_distance
        ),

        "position_quantity": float(
            quantity
        ),

        "position_notional_usd": float(
            position_notional
        ),

        "actual_risk_usd": float(
            actual_risk
        ),

        "potential_profit_usd": float(
            potential_profit
        ),

        "risk_reward": float(
            risk_reward
        )
    }


# ============================================================
# SIGNAL ENGINE
# ============================================================

def signal(
    candles,
    bid_depth=None,
    ask_depth=None,
    max_risk_usd=2.0,
    risk_reward=3.0
):

    if not candles:

        return {
            "signal": "NO SIGNAL",
            "direction": "NO TRADE",
            "confidence": 0,
            "score": 0,
            "edge": 0,
            "reason": "Aucune donnée marché"
        }

    if len(candles) < 200:

        return {
            "signal": "NO SIGNAL",
            "direction": "NO TRADE",
            "confidence": 0,
            "score": 0,
            "edge": 0,
            "reason": (
                f"Données insuffisantes "
                f"({len(candles)}/200)"
            )
        }

    # --------------------------------------------------------
    # PRICES
    # --------------------------------------------------------

    closes = [
        safe_float(c["close"])
        for c in candles
    ]

    highs = [
        safe_float(c["high"])
        for c in candles
    ]

    lows = [
        safe_float(c["low"])
        for c in candles
    ]

    current_price = closes[-1]

    # --------------------------------------------------------
    # EMA
    # --------------------------------------------------------

    ema9 = ema(
        closes,
        9
    )

    ema21 = ema(
        closes,
        21
    )

    ema50 = ema(
        closes,
        50
    )

    ema200 = ema(
        closes,
        200
    )

    # --------------------------------------------------------
    # RSI
    # --------------------------------------------------------

    rsi_value = rsi(
        closes,
        14
    )

    # --------------------------------------------------------
    # ATR
    # --------------------------------------------------------

    atr_value = atr(
        candles,
        14
    )

    # --------------------------------------------------------
    # MACD
    # --------------------------------------------------------

    macd_line, macd_signal, macd_hist = macd(
        closes
    )

    # --------------------------------------------------------
    # EMA SLOPE
    # --------------------------------------------------------

    ema21_values = []

    for i in range(
        max(0, len(closes) - 30),
        len(closes)
    ):

        subset = closes[:i + 1]

        value = ema(
            subset,
            21
        )

        if value is not None:
            ema21_values.append(value)

    ema21_slope = calculate_slope(
        ema21_values,
        min(
            10,
            len(ema21_values)
        )
        if ema21_values
        else 1
    )

    # --------------------------------------------------------
    # ORDER BOOK
    # --------------------------------------------------------

    bid = safe_float(
        bid_depth
    )

    ask = safe_float(
        ask_depth
    )

    total_depth = bid + ask

    if total_depth > 0:

        orderbook_ratio = (
            bid / total_depth
        )

    else:

        orderbook_ratio = 0.5

    # --------------------------------------------------------
    # RECENT RANGE
    # --------------------------------------------------------

    recent_high = max(
        highs[-20:]
    )

    recent_low = min(
        lows[-20:]
    )

    # --------------------------------------------------------
    # SCORING
    # --------------------------------------------------------

    long_score = 0.0
    short_score = 0.0

    long_confirmations = []
    short_confirmations = []

    # EMA trend
    if (
        ema9 is not None
        and ema21 is not None
        and ema50 is not None
        and ema200 is not None
    ):

        if (
            ema9 > ema21
            and ema21 > ema50
            and ema50 > ema200
        ):

            long_score += 25

            long_confirmations.append(
                "EMA trend"
            )

        elif (
            ema9 < ema21
            and ema21 < ema50
            and ema50 < ema200
        ):

            short_score += 25

            short_confirmations.append(
                "EMA trend"
            )

    # RSI
    if rsi_value is not None:

        if 50 < rsi_value < 70:

            long_score += 15

            long_confirmations.append(
                "RSI"
            )

        elif 30 < rsi_value < 50:

            short_score += 15

            short_confirmations.append(
                "RSI"
            )

    # MACD
    if (
        macd_line is not None
        and macd_signal is not None
    ):

        if macd_line > macd_signal:

            long_score += 20

            long_confirmations.append(
                "MACD"
            )

        elif macd_line < macd_signal:

            short_score += 20

            short_confirmations.append(
                "MACD"
            )

    # EMA slope
    if ema21_slope > 0.02:

        long_score += 15

        long_confirmations.append(
            "EMA slope"
        )

    elif ema21_slope < -0.02:

        short_score += 15

        short_confirmations.append(
            "EMA slope"
        )

    # Order book
    if orderbook_ratio > 0.55:

        long_score += 10

        long_confirmations.append(
            "Order book"
        )

    elif orderbook_ratio < 0.45:

        short_score += 10

        short_confirmations.append(
            "Order book"
        )

    # Price position
    if current_price > recent_high:

        long_score += 15

        long_confirmations.append(
            "Breakout"
        )

    elif current_price < recent_low:

        short_score += 15

        short_confirmations.append(
            "Breakdown"
        )

    # --------------------------------------------------------
    # DIRECTION
    # --------------------------------------------------------

    if long_score > short_score:

        direction = "LONG"

        score = long_score

        confirmations = len(
            long_confirmations
        )

    elif short_score > long_score:

        direction = "SHORT"

        score = short_score

        confirmations = len(
            short_confirmations
        )

    else:

        return {
            "signal": "NO SIGNAL",
            "direction": "NO TRADE",
            "confidence": 0,
            "score": 0,
            "edge": 0,
            "reason": "Marché neutre"
        }

    edge = abs(
        long_score - short_score
    )

    # --------------------------------------------------------
    # FILTER
    # --------------------------------------------------------

    if (
        score < 70
        or edge < 15
        or confirmations < 3
    ):

        return {
            "signal": "NO SIGNAL",
            "direction": "NO TRADE",
            "confidence": round(
                min(score, 100)
            ),
            "score": round(score),
            "edge": round(edge),
            "reason": (
                "Signal insuffisant"
            ),
            "long_score": round(
                long_score
            ),
            "short_score": round(
                short_score
            ),
            "indicators": {
                "price": current_price,
                "ema9": ema9,
                "ema21": ema21,
                "ema50": ema50,
                "ema200": ema200,
                "rsi": rsi_value,
                "atr": atr_value,
                "macd": macd_line,
                "macd_signal": macd_signal,
                "macd_hist": macd_hist,
                "ema21_slope": ema21_slope,
                "orderbook_ratio": orderbook_ratio
            }
        }

    # --------------------------------------------------------
    # TRADE PARAMETERS
    # --------------------------------------------------------

    trade = calculate_trade_parameters(

        current_price,

        direction,

        atr_value,

        max_risk_usd,

        risk_reward

    )

    if not trade.get(
        "valid"
    ):

        return {
            "signal": "NO SIGNAL",
            "direction": "NO TRADE",
            "confidence": 0,
            "score": round(score),
            "edge": round(edge),
            "reason": trade.get(
                "reason",
                "Trade invalide"
            )
        }

    # --------------------------------------------------------
    # FINAL SIGNAL
    # --------------------------------------------------------

    return {

        "signal": "ENTRY WINDOW",

        "direction": direction,

        "confidence": round(
            min(score, 100)
        ),

        "score": round(score),

        "edge": round(edge),

        "confirmations": confirmations,

        "reason": (
            f"{direction} confirmé avec "
            f"{confirmations} confirmations"
        ),

        "entry_price": trade[
            "entry_price"
        ],

        "stop_loss": trade[
            "stop_loss"
        ],

        "take_profit": trade[
            "take_profit"
        ],

        # Compatibilité avec main.py
        "stop_price": trade[
            "stop_price"
        ],

        "target_price": trade[
            "target_price"
        ],

        "max_risk_usd": float(
            max_risk_usd
        ),

        "actual_risk_usd": trade[
            "actual_risk_usd"
        ],

        "potential_profit_usd": trade[
            "potential_profit_usd"
        ],

        "risk_reward": trade[
            "risk_reward"
        ],

        "position_quantity": trade[
            "position_quantity"
        ],

        "position_notional_usd": trade[
            "position_notional_usd"
        ],

        "stop_distance": trade[
            "stop_distance"
        ],

        "target_distance": trade[
            "target_distance"
        ],

        "indicators": {

            "price": current_price,

            "ema9": ema9,

            "ema21": ema21,

            "ema50": ema50,

            "ema200": ema200,

            "rsi": rsi_value,

            "atr": atr_value,

            "macd": macd_line,

            "macd_signal": macd_signal,

            "macd_hist": macd_hist,

            "ema21_slope": ema21_slope,

            "orderbook_ratio": orderbook_ratio

        },

        "long_score": round(
            long_score
        ),

        "short_score": round(
            short_score
        )

    }