# ============================================================
# BTC AI SCANNER V2.2
# SIGNAL ENGINE
# ============================================================

import math
from typing import Optional

import numpy as np


# ============================================================
# BASIC INDICATORS
# ============================================================

def ema(values, period):
    values = np.asarray(values, dtype=float)

    if len(values) == 0:
        return np.array([])

    if len(values) < period:
        return np.full(len(values), np.nan)

    alpha = 2.0 / (period + 1.0)

    result = np.full(len(values), np.nan)

    result[period - 1] = np.mean(values[:period])

    for i in range(period, len(values)):
        result[i] = (
            alpha * values[i]
            + (1.0 - alpha) * result[i - 1]
        )

    return result


def rsi(values, period=14):
    """
    RSI de Wilder.
    Retourne une valeur entre 0 et 100.
    """

    values = np.asarray(values, dtype=float)

    if len(values) < period + 1:
        return None

    delta = np.diff(values)

    gains = np.where(delta > 0, delta, 0.0)
    losses = np.where(delta < 0, -delta, 0.0)

    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss

    rsi_value = 100.0 - (100.0 / (1.0 + rs))

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
            rsi_value = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi_value = 100.0 - (
                100.0 / (1.0 + rs)
            )

    return float(rsi_value)


def atr(candles, period=14):
    if len(candles) < period + 1:
        return None

    highs = np.array(
        [float(x["high"]) for x in candles],
        dtype=float
    )

    lows = np.array(
        [float(x["low"]) for x in candles],
        dtype=float
    )

    closes = np.array(
        [float(x["close"]) for x in candles],
        dtype=float
    )

    previous_close = closes[:-1]

    current_high = highs[1:]
    current_low = lows[1:]

    tr1 = current_high - current_low

    tr2 = np.abs(
        current_high - previous_close
    )

    tr3 = np.abs(
        current_low - previous_close
    )

    true_range = np.maximum(
        tr1,
        np.maximum(tr2, tr3)
    )

    if len(true_range) < period:
        return None

    atr_value = np.mean(
        true_range[-period:]
    )

    return float(atr_value)


def macd(values):
    values = np.asarray(values, dtype=float)

    if len(values) < 35:
        return None, None, None

    ema12 = ema(values, 12)
    ema26 = ema(values, 26)

    macd_line = ema12 - ema26

    valid = macd_line[
        ~np.isnan(macd_line)
    ]

    if len(valid) < 9:
        return None, None, None

    signal_line = ema(
        valid,
        9
    )

    macd_value = float(valid[-1])

    signal_value = float(
        signal_line[-1]
    )

    histogram = (
        macd_value - signal_value
    )

    return (
        macd_value,
        signal_value,
        histogram
    )


# ============================================================
# HELPERS
# ============================================================

def safe_float(value, default=0.0):

    try:
        value = float(value)

        if math.isnan(value):
            return default

        if math.isinf(value):
            return default

        return value

    except Exception:
        return default


def calculate_slope(values, lookback=5):

    if len(values) < lookback + 1:
        return 0.0

    current = float(values[-1])
    previous = float(values[-lookback - 1])

    if previous == 0:
        return 0.0

    return (
        (current - previous)
        / previous
    ) * 100.0


# ============================================================
# RISK MANAGEMENT
# ============================================================

def calculate_trade_parameters(
    price,
    atr_value,
    direction,
    max_risk_usd,
    risk_reward
):

    price = float(price)
    atr_value = float(atr_value)
    max_risk_usd = float(max_risk_usd)
    risk_reward = float(risk_reward)

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
    # STOP BASED ON MARKET VOLATILITY
    # --------------------------------------------------------

    stop_distance = atr_value * 1.20

    # Protection contre un SL trop petit
    minimum_stop = price * 0.0005

    stop_distance = max(
        stop_distance,
        minimum_stop
    )

    # --------------------------------------------------------
    # POSITION SIZE
    # --------------------------------------------------------

    quantity = (
        max_risk_usd
        / stop_distance
    )

    position_notional = (
        quantity * price
    )

    actual_risk = (
        quantity * stop_distance
    )

    # --------------------------------------------------------
    # TAKE PROFIT
    # --------------------------------------------------------

    target_distance = (
        stop_distance * risk_reward
    )

    if direction == "LONG":

        stop_loss = (
            price - stop_distance
        )

        take_profit = (
            price + target_distance
        )

    else:

        stop_loss = (
            price + stop_distance
        )

        take_profit = (
            price - target_distance
        )

    potential_profit = (
        actual_risk * risk_reward
    )

    return {
        "valid": True,

        "entry_price": price,

        "stop_loss": float(stop_loss),

        "take_profit": float(take_profit),

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
        ),
    }


# ============================================================
# MAIN SIGNAL ENGINE
# ============================================================

def signal(
    candles,
    bid_depth=0,
    ask_depth=0,
    trade_amount_usd=None,
    max_risk_usd=2.0,
    risk_reward=3.0
):

    # --------------------------------------------------------
    # BASIC VALIDATION
    # --------------------------------------------------------

    if not candles:

        return {
            "signal": "NO TRADE",
            "confidence": 0,
            "reason": "Aucune donnée marché"
        }

    if len(candles) < 200:

        return {
            "signal": "NO TRADE",
            "confidence": 0,
            "reason": (
                f"Historique insuffisant "
                f"({len(candles)}/200 bougies)"
            )
        }

    # --------------------------------------------------------
    # DATA
    # --------------------------------------------------------

    closes = np.array(
        [
            float(x["close"])
            for x in candles
        ],
        dtype=float
    )

    highs = np.array(
        [
            float(x["high"])
            for x in candles
        ],
        dtype=float
    )

    lows = np.array(
        [
            float(x["low"])
            for x in candles
        ],
        dtype=float
    )

    price = float(closes[-1])

    # --------------------------------------------------------
    # INDICATORS
    # --------------------------------------------------------

    ema9_series = ema(
        closes,
        9
    )

    ema21_series = ema(
        closes,
        21
    )

    ema50_series = ema(
        closes,
        50
    )

    ema200_series = ema(
        closes,
        200
    )

    ema9_value = float(
        ema9_series[-1]
    )

    ema21_value = float(
        ema21_series[-1]
    )

    ema50_value = float(
        ema50_series[-1]
    )

    ema200_value = float(
        ema200_series[-1]
    )

    # --------------------------------------------------------
    # RSI
    # --------------------------------------------------------
    # IMPORTANT :
    # correction du bug V2.2 :
    # rsi(closes)
    # et non rsi()

    rsi_value = rsi(
        closes
    )

    if rsi_value is None:
        rsi_value = 50.0

    # --------------------------------------------------------
    # ATR
    # --------------------------------------------------------

    atr_value = atr(
        candles,
        14
    )

    if atr_value is None:

        return {
            "signal": "NO TRADE",
            "confidence": 0,
            "reason": "ATR indisponible"
        }

    # --------------------------------------------------------
    # MACD
    # --------------------------------------------------------

    (
        macd_value,
        macd_signal,
        macd_histogram
    ) = macd(closes)

    if macd_value is None:

        macd_value = 0.0
        macd_signal = 0.0
        macd_histogram = 0.0

    # --------------------------------------------------------
    # EMA SLOPE
    # --------------------------------------------------------

    ema21_slope = calculate_slope(
        ema21_series[
            ~np.isnan(ema21_series)
        ],
        5
    )

    # --------------------------------------------------------
    # RECENT RANGE
    # --------------------------------------------------------

    recent_high = float(
        np.max(highs[-10:])
    )

    recent_low = float(
        np.min(lows[-10:])
    )

    recent_range = (
        recent_high - recent_low
    )

    if recent_range > 0:

        range_position = (
            (price - recent_low)
            / recent_range
        )

    else:

        range_position = 0.5

    # --------------------------------------------------------
    # ORDER BOOK
    # --------------------------------------------------------

    bid_depth = safe_float(
        bid_depth
    )

    ask_depth = safe_float(
        ask_depth
    )

    total_depth = (
        bid_depth + ask_depth
    )

    if total_depth > 0:

        orderbook_ratio = (
            bid_depth / total_depth
        )

    else:

        orderbook_ratio = 0.5

    # ========================================================
    # SCORING
    # ========================================================

    long_score = 0.0
    short_score = 0.0

    long_confirmations = 0
    short_confirmations = 0

    # --------------------------------------------------------
    # EMA STRUCTURE — 25 points
    # --------------------------------------------------------

    if (
        ema9_value > ema21_value
        and ema21_value > ema50_value
    ):

        long_score += 25
        long_confirmations += 1

    elif (
        ema9_value < ema21_value
        and ema21_value < ema50_value
    ):

        short_score += 25
        short_confirmations += 1

    else:

        if ema9_value > ema21_value:
            long_score += 12

        if ema9_value < ema21_value:
            short_score += 12

    # --------------------------------------------------------
    # PRICE VS EMA200 — 10 points
    # --------------------------------------------------------

    if price > ema200_value:

        long_score += 10

    elif price < ema200_value:

        short_score += 10

    # --------------------------------------------------------
    # EMA21 SLOPE — 10 points
    # --------------------------------------------------------

    if ema21_slope > 0.015:

        long_score += 10
        long_confirmations += 1

    elif ema21_slope < -0.015:

        short_score += 10
        short_confirmations += 1

    # --------------------------------------------------------
    # RSI — 10 points
    # --------------------------------------------------------

    if 52 <= rsi_value <= 68:

        long_score += 10
        long_confirmations += 1

    elif 32 <= rsi_value <= 48:

        short_score += 10
        short_confirmations += 1

    elif rsi_value > 50:

        long_score += 5

    elif rsi_value < 50:

        short_score += 5

    # --------------------------------------------------------
    # MACD — 15 points
    # --------------------------------------------------------

    if macd_histogram > 0:

        long_score += 15
        long_confirmations += 1

    elif macd_histogram < 0:

        short_score += 15
        short_confirmations += 1

    # --------------------------------------------------------
    # RANGE POSITION — 10 points
    # --------------------------------------------------------

    if range_position >= 0.65:

        long_score += 10

    elif range_position <= 0.35:

        short_score += 10

    # --------------------------------------------------------
    # ORDER BOOK — 10 points
    # --------------------------------------------------------

    if orderbook_ratio > 0.55:

        long_score += 10

    elif orderbook_ratio < 0.45:

        short_score += 10

    # ========================================================
    # DETERMINE DIRECTION
    # ========================================================

    edge = abs(
        long_score - short_score
    )

    if long_score > short_score:

        direction = "LONG"
        score = long_score
        opposite_score = short_score
        confirmations = long_confirmations

    elif short_score > long_score:

        direction = "SHORT"
        score = short_score
        opposite_score = long_score
        confirmations = short_confirmations

    else:

        return {
            "signal": "NO TRADE",
            "confidence": 0,
            "reason": "Marché neutre",

            "indicators": {
                "ema9": ema9_value,
                "ema21": ema21_value,
                "ema50": ema50_value,
                "ema200": ema200_value,
                "rsi": rsi_value,
                "macd": macd_value,
                "macd_signal": macd_signal,
                "macd_histogram": macd_histogram,
                "atr": atr_value,
                "ema21_slope": ema21_slope,
            },

            "long_score": long_score,
            "short_score": short_score,
        }

    # ========================================================
    # SIGNAL FILTERS
    # ========================================================

    if score < 70:

        return {
            "signal": "NO TRADE",
            "confidence": round(score),
            "reason": (
                f"Score insuffisant : "
                f"{score:.0f}/100"
            ),

            "indicators": {
                "ema9": ema9_value,
                "ema21": ema21_value,
                "ema50": ema50_value,
                "ema200": ema200_value,
                "rsi": rsi_value,
                "macd": macd_value,
                "macd_signal": macd_signal,
                "macd_histogram": macd_histogram,
                "atr": atr_value,
                "ema21_slope": ema21_slope,
            },

            "long_score": round(
                long_score
            ),

            "short_score": round(
                short_score
            ),
        }

    if edge < 15:

        return {
            "signal": "NO TRADE",
            "confidence": round(score),
            "reason": (
                f"Edge insuffisant : "
                f"{edge:.0f}"
            ),

            "indicators": {
                "ema9": ema9_value,
                "ema21": ema21_value,
                "ema50": ema50_value,
                "ema200": ema200_value,
                "rsi": rsi_value,
                "macd": macd_value,
                "macd_signal": macd_signal,
                "macd_histogram": macd_histogram,
                "atr": atr_value,
                "ema21_slope": ema21_slope,
            },

            "long_score": round(
                long_score
            ),

            "short_score": round(
                short_score
            ),
        }

    if confirmations < 3:

        return {
            "signal": "NO TRADE",
            "confidence": round(score),
            "reason": (
                f"Confirmations insuffisantes : "
                f"{confirmations}/3"
            ),

            "indicators": {
                "ema9": ema9_value,
                "ema21": ema21_value,
                "ema50": ema50_value,
                "ema200": ema200_value,
                "rsi": rsi_value,
                "macd": macd_value,
                "macd_signal": macd_signal,
                "macd_histogram": macd_histogram,
                "atr": atr_value,
                "ema21_slope": ema21_slope,
            },

            "long_score": round(
                long_score
            ),

            "short_score": round(
                short_score
            ),
        }

    # ========================================================
    # RISK / REWARD
    # ========================================================

    trade = calculate_trade_parameters(
        price=price,
        atr_value=atr_value,
        direction=direction,
        max_risk_usd=max_risk_usd,
        risk_reward=risk_reward
    )

    if not trade["valid"]:

        return {
            "signal": "NO TRADE",
            "confidence": round(score),
            "reason": trade["reason"],

            "indicators": {
                "ema9": ema9_value,
                "ema21": ema21_value,
                "ema50": ema50_value,
                "ema200": ema200_value,
                "rsi": rsi_value,
                "macd": macd_value,
                "macd_signal": macd_signal,
                "macd_histogram": macd_histogram,
                "atr": atr_value,
                "ema21_slope": ema21_slope,
            }
        }

    # ========================================================
    # FINAL ENTRY WINDOW
    # ========================================================

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
            f"{direction} confirmé "
            f"avec {confirmations} confirmations"
        ),

        # ----------------------------------------------------
        # PRICE
        # ----------------------------------------------------

        "entry_price": trade[
            "entry_price"
        ],

        "stop_loss": trade[
            "stop_loss"
        ],

        "take_profit": trade[
            "take_profit"
        ],

        # ----------------------------------------------------
        # RISK
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # POSITION
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # INDICATORS
        # ----------------------------------------------------

        "indicators": {

            "ema9": ema9_value,

            "ema21": ema21_value,

            "ema50": ema50_value,

            "ema200": ema200_value,

            "rsi": rsi_value,

            "macd": macd_value,

            "macd_signal": macd_signal,

            "macd_histogram": macd_histogram,

            "atr": atr_value,

            "ema21_slope": ema21_slope,

            "range_position": range_position,

            "orderbook_ratio": orderbook_ratio,
        },

        # ----------------------------------------------------
        # SCORES
        # ----------------------------------------------------

        "long_score": round(
            long_score
        ),

        "short_score": round(
            short_score
        ),
    }