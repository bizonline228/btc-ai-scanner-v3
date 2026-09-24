import asyncio
import json
import logging
import os

from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from .market_data import Market
from .signal_engine import signal
from .config import LOCAL_TZ


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)


# ============================================================
# MARKET
# ============================================================

market = Market()

clients = set()

latest = {}


# ============================================================
# HISTORY
# ============================================================

HISTORY_FILE = os.path.join(
    os.path.dirname(__file__),
    "trade_history.json"
)

tz = ZoneInfo(LOCAL_TZ)


# ============================================================
# COOLDOWNS
# ============================================================

LOSS_COOLDOWN_MINUTES = 10
WIN_COOLDOWN_MINUTES = 3
BREAKEVEN_COOLDOWN_MINUTES = 2


# ============================================================
# SIGNAL CONFIRMATION
# ============================================================

SIGNAL_CONFIRM_SECONDS = 1


# ============================================================
# USER SETTINGS
# ============================================================

settings = {
    "max_risk_usd": 2.0,
    "risk_reward": 3.0
}


# ============================================================
# STATE
# ============================================================

state = {
    "active_trade": None,
    "history": [],
    "next_id": 1,
    "cooldown_until": None,
    "candidate_direction": None,
    "candidate_since": None,
}


# ============================================================
# TIME
# ============================================================

def now_utc():
    return datetime.now(timezone.utc)


def now_iso():
    return now_utc().astimezone(tz).isoformat()


# ============================================================
# HISTORY
# ============================================================

def load_history():

    if not os.path.exists(HISTORY_FILE):
        return

    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        state["history"] = data.get(
            "history",
            []
        )

        state["next_id"] = int(
            data.get(
                "next_id",
                len(state["history"]) + 1
            )
        )

    except Exception:

        logging.exception(
            "Impossible de charger l'historique"
        )


def save_history():

    tmp = HISTORY_FILE + ".tmp"

    with open(
        tmp,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            {
                "history": state["history"],
                "next_id": state["next_id"]
            },
            f,
            ensure_ascii=False,
            indent=2
        )

    os.replace(
        tmp,
        HISTORY_FILE
    )


# ============================================================
# STATISTICS
# ============================================================

def stats():

    h = state["history"]

    wins = sum(
        1
        for x in h
        if x.get("result") == "WIN"
    )

    losses = sum(
        1
        for x in h
        if x.get("result") == "LOSS"
    )

    pnl_pct = sum(
        float(
            x.get(
                "pnl_pct",
                0
            )
        )
        for x in h
    )

    pnl_usd = sum(
        float(
            x.get(
                "pnl_usd",
                0
            )
        )
        for x in h
    )

    return {

        "total": len(h),

        "wins": wins,

        "losses": losses,

        "win_rate": (
            round(
                wins / len(h) * 100,
                2
            )
            if h
            else 0
        ),

        "pnl_pct": round(
            pnl_pct,
            4
        ),

        "pnl_usd": round(
            pnl_usd,
            4
        ),

        "open": (
            state["active_trade"] is not None
        ),

        "cooldown_until": (
            state["cooldown_until"].isoformat()
            if state["cooldown_until"]
            else None
        ),

        "settings": dict(settings)

    }


# ============================================================
# COOLDOWN
# ============================================================

def set_cooldown(result):

    now = now_utc()

    if result == "LOSS":

        duration = timedelta(
            minutes=LOSS_COOLDOWN_MINUTES
        )

    elif result == "WIN":

        duration = timedelta(
            minutes=WIN_COOLDOWN_MINUTES
        )

    else:

        duration = timedelta(
            minutes=BREAKEVEN_COOLDOWN_MINUTES
        )

    state["cooldown_until"] = (
        now + duration
    )


def cooldown_active():

    until = state["cooldown_until"]

    if not until:
        return False

    if now_utc() >= until:

        state["cooldown_until"] = None

        return False

    return True


# ============================================================
# OPEN TRADE
# ============================================================

def open_trade(sig):

    trade = {

        "id": state["next_id"],

        "direction": sig.get(
            "direction"
        ),

        "entry_price": sig.get(
            "entry_price"
        ),

        "stop_price": sig.get(
            "stop_price"
        ),

        "target_price": sig.get(
            "target_price"
        ),

        "opened_at": now_iso(),

        "planned_exit": sig.get(
            "exit_time"
        ),

        "hold_minutes": sig.get(
            "hold_minutes"
        ),

        "confidence": sig.get(
            "confidence"
        ),

        "long_score": sig.get(
            "long_score"
        ),

        "short_score": sig.get(
            "short_score"
        ),

        "reason": sig.get(
            "reason",
            ""
        ),

        "max_risk_usd": sig.get(
            "max_risk_usd"
        ),

        "actual_risk_usd": sig.get(
            "actual_risk_usd"
        ),

        "potential_profit_usd": sig.get(
            "potential_profit_usd"
        ),

        "position_quantity": sig.get(
            "position_quantity"
        ),

        "position_notional_usd": sig.get(
            "position_notional_usd"
        ),

        "risk_reward": sig.get(
            "risk_reward"
        ),

        "status": "OPEN"

    }

    state["next_id"] += 1

    state["active_trade"] = trade

    logging.info(
        "TRADE #%s OPEN %s @ %.2f | "
        "risk=%.2f | RR=1:%.1f",

        trade["id"],

        trade["direction"],

        float(
            trade["entry_price"] or 0
        ),

        float(
            trade["actual_risk_usd"] or 0
        ),

        float(
            trade["risk_reward"] or 0
        )
    )

    return trade


# ============================================================
# CLOSE TRADE
# ============================================================

def close_trade(
    reason,
    exit_price
):

    trade = state["active_trade"]

    if not trade:
        return None

    entry = float(
        trade["entry_price"]
    )

    exit_p = float(
        exit_price
    )

    direction = trade["direction"]

    quantity = float(
        trade.get(
            "position_quantity",
            0
        )
    )

    if direction == "LONG":

        pnl_price = (
            exit_p - entry
        )

    else:

        pnl_price = (
            entry - exit_p
        )

    pnl_pct = (
        pnl_price / entry * 100
    )

    pnl_usd = (
        pnl_price * quantity
    )

    if pnl_usd > 0:

        result = "WIN"

    elif pnl_usd < 0:

        result = "LOSS"

    else:

        result = "BREAKEVEN"

    closed = {
        **trade,

        "status": "CLOSED",

        "result": result,

        "exit_reason": reason,

        "exit_price": exit_p,

        "closed_at": now_iso(),

        "pnl_pct": round(
            pnl_pct,
            4
        ),

        "pnl_usd": round(
            pnl_usd,
            4
        )

    }

    state["history"].insert(
        0,
        closed
    )

    state["history"] = (
        state["history"][:500]
    )

    state["active_trade"] = None

    set_cooldown(result)

    state["candidate_direction"] = None

    state["candidate_since"] = None

    save_history()

    logging.info(
        "TRADE #%s CLOSED | %s | "
        "%.2f $ | %.4f%% | %s",

        closed["id"],
        result,
        pnl_usd,
        pnl_pct,
        reason
    )

    return closed


# ============================================================
# MONITOR ACTIVE TRADE
# ============================================================

def monitor_active():

    trade = state["active_trade"]

    if not trade:
        return None

    if market.last_price is None:
        return None

    p = float(
        market.last_price
    )

    direction = trade["direction"]

    if direction == "LONG":

        if p <= float(
            trade["stop_price"]
        ):

            return close_trade(
                "STOP LOSS",
                p
            )

        if p >= float(
            trade["target_price"]
        ):

            return close_trade(
                "TAKE PROFIT",
                p
            )

    else:

        if p >= float(
            trade["stop_price"]
        ):

            return close_trade(
                "STOP LOSS",
                p
            )

        if p <= float(
            trade["target_price"]
        ):

            return close_trade(
                "TAKE PROFIT",
                p
            )

    planned = trade.get(
        "planned_exit"
    )

    if planned:

        try:

            exit_time = datetime.fromisoformat(
                planned
            )

            if (
                exit_time.timestamp()
                <= now_utc().timestamp()
            ):

                return close_trade(
                    "TIME EXIT",
                    p
                )

        except Exception:

            logging.exception(
                "Erreur TIME EXIT"
            )

    return None


# ============================================================
# SIGNAL CONFIRMATION
# ============================================================

def confirmed_signal(base):

    direction = base.get(
        "direction"
    )

    if direction not in (
        "LONG",
        "SHORT"
    ):

        state["candidate_direction"] = None

        state["candidate_since"] = None

        return False

    now = now_utc()

    if (
        state["candidate_direction"]
        != direction
    ):

        state["candidate_direction"] = direction

        state["candidate_since"] = now

        return False

    started = state[
        "candidate_since"
    ]

    if not started:
        return False

    elapsed = (
        now - started
    ).total_seconds()

    return (
        elapsed >= SIGNAL_CONFIRM_SECONDS
    )


# ============================================================
# BUILD PAYLOAD
# ============================================================

def build_payload():

    # --------------------------------------------------------
    # SIGNAL ENGINE
    # --------------------------------------------------------

    candles = list(
        market.candles
    )

    base = signal(

        candles,

        bid_depth=market.bid_depth,

        ask_depth=market.ask_depth,

        max_risk_usd=settings[
            "max_risk_usd"
        ],

        risk_reward=settings[
            "risk_reward"
        ]

    )

    # --------------------------------------------------------
    # ACTIVE TRADE
    # --------------------------------------------------------

    if state["active_trade"]:

        active = state[
            "active_trade"
        ]

        payload = dict(base)

        payload.update({

            "direction": active[
                "direction"
            ],

            "status": "TRADE ACTIVE",

            "price": market.last_price,

            "entry_price": active[
                "entry_price"
            ],

            "entry_start": active[
                "opened_at"
            ],

            "entry_end": active[
                "planned_exit"
            ],

            "stop_price": active[
                "stop_price"
            ],

            "target_price": active[
                "target_price"
            ],

            "exit_time": active[
                "planned_exit"
            ],

            "hold_minutes": active[
                "hold_minutes"
            ],

            "confidence": active[
                "confidence"
            ],

            "reason": (
                "Trade actif : "
                "aucun nouveau signal."
            ),

            "active_trade": active

        })

        return payload

    # --------------------------------------------------------
    # COOLDOWN
    # --------------------------------------------------------

    if cooldown_active():

        until = state[
            "cooldown_until"
        ]

        payload = dict(base)

        payload.update({

            "direction": "NO TRADE",

            "status": "COOLDOWN",

            "price": market.last_price,

            "reason": (
                "Protection après "
                "le dernier trade."
            ),

            "cooldown_until":
                until.astimezone(
                    tz
                ).isoformat()

        })

        return payload

    # --------------------------------------------------------
    # NO ENTRY WINDOW
    #
    # IMPORTANT:
    # signal_engine.py returns:
    #
    #     "signal": "ENTRY WINDOW"
    #
    # NOT:
    #
    #     "status": "ENTRY WINDOW"
    # --------------------------------------------------------

    if base.get(
        "signal"
    ) != "ENTRY WINDOW":

        state["candidate_direction"] = None

        state["candidate_since"] = None

        base["active_trade"] = None

        return base

    # --------------------------------------------------------
    # CONFIRMATION
    # --------------------------------------------------------

    if not confirmed_signal(base):

        payload = dict(base)

        payload.update({

            "direction": "NO TRADE",

            "status": "CONFIRMING",

            "reason": (
                "Signal détecté. "
                "Attente de confirmation."
            ),

            "active_trade": None

        })

        return payload

    # --------------------------------------------------------
    # OPEN PAPER TRADE
    # --------------------------------------------------------

    active = open_trade(
        base
    )

    state["candidate_direction"] = None

    state["candidate_since"] = None

    payload = dict(base)

    payload.update({

        "status": "TRADE ACTIVE",

        "active_trade": active

    })

    return payload


# ============================================================
# MAIN LOOP
# ============================================================

async def loop():

    global latest

    while True:

        try:

            monitor_active()

            latest = build_payload()

            latest["stats"] = stats()

            dead = []

            for ws in clients:

                try:

                    await ws.send_text(
                        json.dumps(
                            latest
                        )
                    )

                except Exception:

                    dead.append(ws)

            for ws in dead:

                clients.discard(ws)

        except Exception:

            logging.exception(
                "LOOP ERROR"
            )

        await asyncio.sleep(1)


# ============================================================
# LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app):

    load_history()

    market_task = asyncio.create_task(
        market.run()
    )

    loop_task = asyncio.create_task(
        loop()
    )

    yield

    market_task.cancel()

    loop_task.cancel()


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="BTC AI Scanner V3",
    lifespan=lifespan
)


# ============================================================
# STATIC FILES
# ============================================================

@app.get("/style.css")
async def style_css():

    return FileResponse(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "style.css"),
        media_type="text/css"
    )


@app.get("/app.js")
async def app_js():

    return FileResponse(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "app.js"),
        media_type="application/javascript"
    )


# ============================================================
# HOME
# ============================================================

@app.get("/")
async def root():

    return FileResponse(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "index.html")
    )


# ============================================================
# STATUS
# ============================================================

@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "btc-ai-scanner-v3"}


@app.get("/api/status")
async def status():

    return latest or {
        "status": "STARTING"
    }


# ============================================================
# HISTORY
# ============================================================

@app.get("/api/history")
async def history():

    return {

        "history": state["history"],

        "active_trade": state["active_trade"],

        "stats": stats()

    }


# ============================================================
# SETTINGS GET
# ============================================================

@app.get("/api/settings")
async def get_settings():

    return settings


# ============================================================
# SETTINGS UPDATE
# ============================================================

@app.post("/api/settings")
async def update_settings(
    data: dict
):

    try:

        max_risk = float(
            data.get(
                "max_risk_usd",
                settings["max_risk_usd"]
            )
        )

        risk_reward = float(
            data.get(
                "risk_reward",
                settings["risk_reward"]
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return {
            "error": "Paramètres invalides."
        }

    # --------------------------------------------------------
    # RISK
    # --------------------------------------------------------

    if max_risk <= 0:

        return {
            "error": "Risque invalide."
        }

    # --------------------------------------------------------
    # RR
    # --------------------------------------------------------

    allowed_rr = [
        1.0,
        1.5,
        2.0,
        2.5,
        3.0,
        4.0
    ]

    if risk_reward not in allowed_rr:

        return {
            "error": "Ratio Risk/Reward invalide."
        }

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    settings["max_risk_usd"] = max_risk

    settings["risk_reward"] = risk_reward

    logging.info(
        "SETTINGS | risk=%.2f | RR=1:%.1f",
        max_risk,
        risk_reward
    )

    return {

        "success": True,

        "settings": settings

    }


# ============================================================
# WEBSOCKET
# ============================================================

@app.websocket("/ws")
async def ws(
    websocket: WebSocket
):

    await websocket.accept()

    clients.add(
        websocket
    )

    try:

        while True:

            await websocket.receive_text()

    except WebSocketDisconnect:

        clients.discard(
            websocket
        )

    except Exception:

        clients.discard(
            websocket
        )
