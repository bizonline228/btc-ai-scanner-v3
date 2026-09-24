from math import sqrt


def ema(v, p):
    if len(v) < p:
        return None

    k = 2 / (p + 1)
    x = sum(v[:p]) / p

    for y in v[p:]:
        x = y * k + x * (1 - k)

    return x


def rsi(v, p=14):
    if len(v) < p + 1:
        return None

    gains = []
    losses = []

    for a, b in zip(v[-p - 1:-1], v[-p:]):
        d = b - a
        gains.append(max(d, 0))
        losses.append(max(-d, 0))

    avg_gain = sum(gains) / p
    avg_loss = sum(losses) / p

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def atr(h, l, c, p=14):
    if len(c) < p + 1:
        return None

    tr = []

    for i in range(len(c)):
        if i == 0:
            value = h[i] - l[i]
        else:
            value = max(
                h[i] - l[i],
                abs(h[i] - c[i - 1]),
                abs(l[i] - c[i - 1])
            )

        tr.append(value)

    return sum(tr[-p:]) / p


def macd(v):
    if len(v) < 35:
        return None, None, None, None

    fast = ema(v, 12)
    slow = ema(v, 26)

    if fast is None or slow is None:
        return None, None, None, None

    macd_series = []

    for i in range(26, len(v) + 1):
        a = ema(v[:i], 12)
        b = ema(v[:i], 26)

        if a is not None and b is not None:
            macd_series.append(a - b)

    if not macd_series:
        return None, None, None, None

    line = fast - slow
    sig = ema(macd_series, 9)

    if sig is None:
        return line, None, None, None

    hist = line - sig

    previous_hist = None

    if len(macd_series) >= 10:
        previous_line = macd_series[-2]

        previous_signal = ema(macd_series[:-1], 9)

        if previous_signal is not None:
            previous_hist = previous_line - previous_signal

    return line, sig, hist, previous_hist


def volatility(v, p=20):
    if len(v) < p + 1:
        return None

    w = v[-p - 1:]

    returns = [
        b / a - 1
        for a, b in zip(w[:-1], w[1:])
        if a
    ]

    if len(returns) < 2:
        return None

    mean = sum(returns) / len(returns)

    return sqrt(
        sum((x - mean) ** 2 for x in returns)
        / (len(returns) - 1)
    )


def slope(v, p=5):
    """
    Mesure simple de pente en pourcentage.
    """
    if len(v) < p + 1:
        return None

    old = v[-p - 1]
    new = v[-1]

    if old == 0:
        return None

    return (new - old) / old * 100


def snapshot(c):
    closes = [x["close"] for x in c]
    highs = [x["high"] for x in c]
    lows = [x["low"] for x in c]

    m, ms, mh, mh_prev = macd(closes)

    e9 = ema(closes, 9)
    e21 = ema(closes, 21)
    e50 = ema(closes, 50)
    e200 = ema(closes, 200)

    # Structure récente
    recent_high = max(highs[-10:]) if len(highs) >= 10 else None
    recent_low = min(lows[-10:]) if len(lows) >= 10 else None

    return {
        "ema9": e9,
        "ema21": e21,
        "ema50": e50,
        "ema200": e200,

        "ema21_slope": slope(closes, 5),

        "rsi": rsi(closes),

        "macd": m,
        "macd_signal": ms,
        "macd_hist": mh,
        "macd_hist_prev": mh_prev,

        "atr": atr(highs, lows, closes),

        "volatility": volatility(closes),

        "recent_high": recent_high,
        "recent_low": recent_low,
    }