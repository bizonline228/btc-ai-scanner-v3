# ============================================================
# BTC AI SCANNER V2.2
# CONFIGURATION
# ============================================================

SYMBOL = "BTCUSDT"

WS_URL = (
    "wss://data-stream.binance.vision/"
    "stream?streams=btcusdt@aggTrade/btcusdt@depth20@100ms"
)

KLINES_URL = "https://data-api.binance.vision/api/v3/klines"

MAX_CANDLES = 500
CANDLE_SECONDS = 60
LOCAL_TZ = "Africa/Lome"


# ============================================================
# SIGNAL ENGINE
# ============================================================

MIN_SIGNAL_SCORE = 70
MIN_EDGE = 15

# Nombre minimum de confirmations techniques
MIN_CONFIRMATIONS = 3


# ============================================================
# RISK MANAGEMENT V2.2
# ============================================================

# Risque par trade.
# Exemple :
# 2$ de risque avec R:R 1:3
# = perte maximale 2$
# = gain potentiel 6$

DEFAULT_MAX_RISK_USD = 2.0

DEFAULT_RISK_REWARD = 3.0

ALLOWED_RISK_REWARDS = [
    1.0,
    1.5,
    2.0,
    2.5,
    3.0,
    4.0,
]


# ============================================================
# COMPATIBILITÉ AVEC MAIN.PY V2.2
# ============================================================
#
# Le champ trade_amount_usd existe encore dans main.py V2.2.
# Il n'est plus utilisé comme limite de position par le moteur.
#
# On le conserve uniquement pour éviter de casser l'API existante.

DEFAULT_TRADE_AMOUNT_USD = 1_000_000_000.0