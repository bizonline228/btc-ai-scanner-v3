import asyncio
import json
import logging
import httpx
import websockets
from collections import deque

from .config import WS_URL, KLINES_URL, SYMBOL, MAX_CANDLES

log = logging.getLogger(__name__)


class Market:

    def __init__(self):
        self.candles = deque(maxlen=MAX_CANDLES)
        self.last_price = None
        self.bid_depth = 0
        self.ask_depth = 0

    async def history(self):
        log.info("BINANCE: téléchargement de l'historique...")

        try:
            async with httpx.AsyncClient(timeout=15) as c:

                r = await c.get(
                    KLINES_URL,
                    params={
                        "symbol": SYMBOL,
                        "interval": "1m",
                        "limit": MAX_CANDLES
                    }
                )

                log.info("BINANCE HTTP: %s", r.status_code)

                r.raise_for_status()

                rows = r.json()

            for x in rows:
                self.candles.append({
                    "ts": int(x[0]) // 1000,
                    "open": float(x[1]),
                    "high": float(x[2]),
                    "low": float(x[3]),
                    "close": float(x[4]),
                    "volume": float(x[5])
                })

            if self.candles:
                self.last_price = self.candles[-1]["close"]

            log.info(
                "BINANCE: %s bougies chargées | prix=%s",
                len(self.candles),
                self.last_price
            )

        except Exception:
            log.exception("BINANCE HISTORY ERROR")

    def trade(self, ts, price, qty):

        bucket = (ts // 1000) // 60 * 60

        if not self.candles or self.candles[-1]["ts"] != bucket:

            prev = (
                self.candles[-1]["close"]
                if self.candles
                else price
            )

            self.candles.append({
                "ts": bucket,
                "open": prev,
                "high": price,
                "low": price,
                "close": price,
                "volume": qty
            })

        else:

            x = self.candles[-1]

            x["high"] = max(x["high"], price)
            x["low"] = min(x["low"], price)
            x["close"] = price
            x["volume"] += qty

        self.last_price = price

    async def handle(self, msg):

        d = msg.get("data", msg)
        e = d.get("e")

        if e == "aggTrade":

            self.trade(
                int(d["T"]),
                float(d["p"]),
                float(d["q"])
            )

        elif e == "depthUpdate":

            self.bid_depth = sum(
                float(q)
                for _, q in d.get("b", [])
            )

            self.ask_depth = sum(
                float(q)
                for _, q in d.get("a", [])
            )

    async def run(self):

        await self.history()

        while True:

            try:

                log.info("BINANCE WS: connexion...")

                async with websockets.connect(
                    WS_URL,
                    ping_interval=20,
                    ping_timeout=20
                ) as ws:

                    log.info("BINANCE WS: connecté")

                    async for raw in ws:

                        await self.handle(
                            json.loads(raw)
                        )

            except Exception:

                log.exception("BINANCE WS ERROR")

                await asyncio.sleep(3)