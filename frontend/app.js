// ============================================================
// BTC AI SCANNER V2.2
// FRONTEND
// ============================================================

"use strict";


// ============================================================
// DOM
// ============================================================

const connectionStatus =
    document.getElementById("connectionStatus");

const direction =
    document.getElementById("direction");

const confidence =
    document.getElementById("confidence");

const signalMessage =
    document.getElementById("signalMessage");

const entryPrice =
    document.getElementById("entryPrice");

const currentPrice =
    document.getElementById("currentPrice");

const stopPrice =
    document.getElementById("stopPrice");

const targetPrice =
    document.getElementById("targetPrice");

const estimatedExit =
    document.getElementById("estimatedExit");

const duration =
    document.getElementById("duration");

const riskAmount =
    document.getElementById("riskAmount");

const potentialProfit =
    document.getElementById("potentialProfit");

const positionSize =
    document.getElementById("positionSize");

const btcQuantity =
    document.getElementById("btcQuantity");

const riskReward =
    document.getElementById("riskReward");

const analysis =
    document.getElementById("analysis");

const ema9 =
    document.getElementById("ema9");

const ema21 =
    document.getElementById("ema21");

const ema50 =
    document.getElementById("ema50");

const ema200 =
    document.getElementById("ema200");

const rsi =
    document.getElementById("rsi");

const macd =
    document.getElementById("macd");

const atr =
    document.getElementById("atr");

const orderBook =
    document.getElementById("orderBook");

const totalTrades =
    document.getElementById("totalTrades");

const wins =
    document.getElementById("wins");

const losses =
    document.getElementById("losses");

const winRate =
    document.getElementById("winRate");

const totalPnl =
    document.getElementById("totalPnl");

const historyBody =
    document.getElementById("historyBody");

const riskInput =
    document.getElementById("riskInput");

const rrInput =
    document.getElementById("rrInput");

const applySettings =
    document.getElementById("applySettings");

const settingsMessage =
    document.getElementById("settingsMessage");

const refreshHistory =
    document.getElementById("refreshHistory");


// ============================================================
// HELPERS
// ============================================================

function formatNumber(value, decimals = 2) {

    if (
        value === null ||
        value === undefined ||
        value === "" ||
        !Number.isFinite(Number(value))
    ) {
        return "—";
    }

    return Number(value).toLocaleString(
        "en-US",
        {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }
    );
}


function formatUSD(value, decimals = 2) {

    if (
        value === null ||
        value === undefined ||
        value === "" ||
        !Number.isFinite(Number(value))
    ) {
        return "—";
    }

    return (
        formatNumber(value, decimals) +
        " $"
    );
}


function formatBTC(value) {

    if (
        value === null ||
        value === undefined ||
        value === "" ||
        !Number.isFinite(Number(value))
    ) {
        return "—";
    }

    return Number(value).toFixed(6);
}


function formatPercent(value) {

    if (
        value === null ||
        value === undefined ||
        value === "" ||
        !Number.isFinite(Number(value))
    ) {
        return "0%";
    }

    return (
        Number(value).toFixed(1) +
        "%"
    );
}


function getRatioText(value) {

    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "1:3";
    }

    return "1:" + number;
}


function setText(element, value) {

    if (element) {
        element.textContent =
            value === null ||
            value === undefined ||
            value === ""
                ? "—"
                : value;
    }
}


// ============================================================
// SETTINGS
// ============================================================

async function loadSettings() {

    try {

        const response =
            await fetch("/api/settings");

        if (!response.ok) {
            throw new Error(
                "Impossible de charger les paramètres."
            );
        }

        const data =
            await response.json();


        const risk =
            Number(
                data.max_risk_usd ??
                data.maxRiskUsd ??
                2
            );


        const rr =
            Number(
                data.risk_reward ??
                data.riskReward ??
                3
            );


        riskInput.value =
            Number.isFinite(risk)
                ? risk
                : 2;


        rrInput.value =
            String(
                Number.isFinite(rr)
                    ? rr
                    : 3
            );


        updateRiskPreview(
            riskInput.value,
            rrInput.value
        );

    } catch (error) {

        console.error(
            "SETTINGS LOAD ERROR:",
            error
        );

    }
}


async function saveSettings() {

    const maxRisk =
        Number(riskInput.value);

    const rr =
        Number(rrInput.value);


    if (
        !Number.isFinite(maxRisk) ||
        maxRisk <= 0
    ) {

        settingsMessage.textContent =
            "Le risque doit être supérieur à 0 $.";

        return;
    }


    const allowedRR = [
        1,
        1.5,
        2,
        2.5,
        3,
        4
    ];


    if (!allowedRR.includes(rr)) {

        settingsMessage.textContent =
            "Risk / Reward invalide.";

        return;
    }


    applySettings.disabled = true;

    settingsMessage.textContent =
        "Application...";


    try {

        const response =
            await fetch(
                "/api/settings",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        max_risk_usd:
                            maxRisk,

                        risk_reward:
                            rr
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Erreur lors de l'application."
            );
        }


        settingsMessage.textContent =
            "Paramètres appliqués.";


        updateRiskPreview(
            maxRisk,
            rr
        );


    } catch (error) {

        console.error(
            "SETTINGS ERROR:",
            error
        );


        settingsMessage.textContent =
            error.message ||
            "Erreur serveur.";

    } finally {

        applySettings.disabled = false;
    }
}


function updateRiskPreview(
    risk,
    rr
) {

    const r =
        Number(risk);

    const ratio =
        Number(rr);


    if (
        !Number.isFinite(r) ||
        !Number.isFinite(ratio)
    ) {
        return;
    }


    setText(
        riskAmount,
        formatUSD(r)
    );


    setText(
        potentialProfit,
        formatUSD(
            r * ratio
        )
    );


    setText(
        riskReward,
        getRatioText(ratio)
    );
}


applySettings.addEventListener(
    "click",
    saveSettings
);


riskInput.addEventListener(
    "input",
    () => {

        updateRiskPreview(
            riskInput.value,
            rrInput.value
        );

    }
);


rrInput.addEventListener(
    "change",
    () => {

        updateRiskPreview(
            riskInput.value,
            rrInput.value
        );

    }
);


// ============================================================
// CONNECTION
// ============================================================

let socket = null;

let reconnectTimer = null;


function setConnection(
    connected
) {

    if (!connectionStatus) {
        return;
    }


    if (connected) {

        connectionStatus.textContent =
            "● Connecté";

        connectionStatus.classList.remove(
            "offline"
        );

        connectionStatus.classList.add(
            "online"
        );

    } else {

        connectionStatus.textContent =
            "● Déconnexion";

        connectionStatus.classList.remove(
            "online"
        );

        connectionStatus.classList.add(
            "offline"
        );
    }
}


function connectWebSocket() {

    if (socket) {

        try {
            socket.close();
        } catch (_) {}

    }


    const protocol =
        location.protocol === "https:"
            ? "wss:"
            : "ws:";


    const wsUrl =
        protocol +
        "//" +
        location.host +
        "/ws";


    console.log(
        "WS CONNECT:",
        wsUrl
    );


    socket =
        new WebSocket(wsUrl);


    socket.onopen = () => {

        console.log(
            "WebSocket connecté."
        );

        setConnection(true);

        if (reconnectTimer) {

            clearTimeout(
                reconnectTimer
            );

            reconnectTimer = null;
        }
    };


    socket.onmessage = (
        event
    ) => {

        try {

            const data =
                JSON.parse(
                    event.data
                );


            updateScanner(
                data
            );

        } catch (error) {

            console.error(
                "WS DATA ERROR:",
                error
            );

        }
    };


    socket.onerror = (
        error
    ) => {

        console.error(
            "WebSocket error:",
            error
        );

        setConnection(false);
    };


    socket.onclose = () => {

        console.log(
            "WebSocket fermé."
        );

        setConnection(false);


        if (!reconnectTimer) {

            reconnectTimer =
                setTimeout(
                    () => {

                        reconnectTimer =
                            null;

                        connectWebSocket();

                    },
                    3000
                );
        }
    };
}


// ============================================================
// SCANNER UPDATE
// ============================================================

function updateScanner(data) {

    if (!data) {
        return;
    }


    /*
     * Certaines versions du backend
     * peuvent envoyer les informations
     * directement ou dans "signal".
     */

    const signal =
        data.signal ||
        data;


    const trade =
        data.active_trade ||
        data.activeTrade ||
        null;


    const price =
        data.price ??
        data.current_price ??
        signal.price;


    // --------------------------------------------------------
    // PRIX
    // --------------------------------------------------------

    if (
        price !== null &&
        price !== undefined
    ) {

        setText(
            currentPrice,
            formatUSD(price)
        );

    }


    // --------------------------------------------------------
    // DIRECTION
    // --------------------------------------------------------

    const dir =
        (
            signal.direction ||
            data.direction ||
            "—"
        ).toUpperCase();


    setText(
        direction,
        dir
    );


    direction.classList.remove(
        "long",
        "short",
        "neutral"
    );


    if (dir === "LONG") {

        direction.classList.add(
            "long"
        );

    } else if (dir === "SHORT") {

        direction.classList.add(
            "short"
        );

    } else {

        direction.classList.add(
            "neutral"
        );
    }


    // --------------------------------------------------------
    // CONFIDENCE
    // --------------------------------------------------------

    const conf =
        signal.confidence ??
        data.confidence ??
        signal.score ??
        0;


    setText(
        confidence,
        formatPercent(conf)
    );


    // --------------------------------------------------------
    // SIGNAL MESSAGE
    // --------------------------------------------------------

    const message =
        signal.message ||
        signal.reason ||
        data.message ||
        data.status ||
        "Analyse en cours...";


    setText(
        signalMessage,
        message
    );


    // --------------------------------------------------------
    // ANALYSIS
    // --------------------------------------------------------

    const longScore =
        signal.long_score ??
        signal.longScore ??
        data.long_score ??
        0;


    const shortScore =
        signal.short_score ??
        signal.shortScore ??
        data.short_score ??
        0;


    const confirmations =
        signal.confirmations ??
        data.confirmations ??
        0;


    let analysisText =
        "LONG " +
        formatNumber(longScore, 0) +
        " · SHORT " +
        formatNumber(shortScore, 0);


    if (confirmations) {

        analysisText +=
            " · " +
            confirmations +
            " confirmations";
    }


    if (signal.confirmed) {

        analysisText +=
            " · LONG confirmé";

    }


    setText(
        analysis,
        analysisText
    );


    // --------------------------------------------------------
    // INDICATORS
    // --------------------------------------------------------

    const indicators =
        signal.indicators ||
        data.indicators ||
        signal;


    setText(
        ema9,
        formatUSD(
            indicators.ema9,
            2
        )
    );


    setText(
        ema21,
        formatUSD(
            indicators.ema21,
            2
        )
    );


    setText(
        ema50,
        formatUSD(
            indicators.ema50,
            2
        )
    );


    setText(
        ema200,
        formatUSD(
            indicators.ema200,
            2
        )
    );


    setText(
        rsi,
        Number.isFinite(
            Number(indicators.rsi)
        )
            ? Number(
                indicators.rsi
            ).toFixed(4)
            : "—"
    );


    setText(
        macd,
        Number.isFinite(
            Number(indicators.macd)
        )
            ? Number(
                indicators.macd
            ).toFixed(4)
            : "—"
    );


    setText(
        atr,
        formatUSD(
            indicators.atr,
            2
        )
    );


    const orderRatio =
        indicators.orderbook_ratio ??
        indicators.orderBookRatio ??
        signal.orderbook_ratio;


    setText(
        orderBook,
        Number.isFinite(
            Number(orderRatio)
        )
            ? Number(
                orderRatio
            ).toFixed(3)
            : "—"
    );


    // --------------------------------------------------------
    // SETTINGS DISPLAY
    // --------------------------------------------------------

    const maxRisk =
        signal.max_risk_usd ??
        data.max_risk_usd ??
        riskInput.value;


    const rr =
        signal.risk_reward ??
        data.risk_reward ??
        rrInput.value;


    updateRiskPreview(
        maxRisk,
        rr
    );


    // --------------------------------------------------------
    // ACTIVE TRADE
    // --------------------------------------------------------

    if (trade) {

        updateActiveTrade(
            trade
        );

    } else {

        resetActiveTrade();
    }
}


// ============================================================
// ACTIVE TRADE
// ============================================================

function updateActiveTrade(
    trade
) {

    setText(
        entryPrice,
        formatUSD(
            trade.entry_price ??
            trade.entryPrice
        )
    );


    setText(
        stopPrice,
        formatUSD(
            trade.stop_price ??
            trade.stopPrice
        )
    );


    setText(
        targetPrice,
        formatUSD(
            trade.target_price ??
            trade.targetPrice
        )
    );


    setText(
        estimatedExit,
        trade.planned_exit ??
        trade.plannedExit ??
        "—"
    );


    setText(
        duration,
        trade.hold_minutes !== undefined
            ? trade.hold_minutes + " min"
            : "—"
    );


    setText(
        riskAmount,
        formatUSD(
            trade.max_risk_usd ??
            trade.maxRiskUsd
        )
    );


    setText(
        potentialProfit,
        formatUSD(
            trade.potential_profit_usd ??
            trade.potentialProfitUsd
        )
    );


    setText(
        positionSize,
        formatUSD(
            trade.position_notional_usd ??
            trade.positionNotionalUsd
        )
    );


    setText(
        btcQuantity,
        formatBTC(
            trade.position_quantity ??
            trade.positionQuantity
        )
    );


    setText(
        riskReward,
        getRatioText(
            trade.risk_reward ??
            trade.riskReward
        )
    );


    if (
        trade.current_price !== undefined
    ) {

        setText(
            currentPrice,
            formatUSD(
                trade.current_price
            )
        );
    }
}


// ============================================================
// RESET TRADE
// ============================================================

function resetActiveTrade() {

    setText(
        entryPrice,
        "—"
    );


    setText(
        stopPrice,
        "—"
    );


    setText(
        targetPrice,
        "—"
    );


    setText(
        estimatedExit,
        "—"
    );


    setText(
        duration,
        "—"
    );


    /*
     * Même lorsqu'il n'y a pas de trade actif,
     * le risque choisi et le gain potentiel
     * restent affichés.
     */

    const risk =
        Number(
            riskInput.value
        );


    const rr =
        Number(
            rrInput.value
        );


    updateRiskPreview(
        risk,
        rr
    );


    setText(
        positionSize,
        "—"
    );


    setText(
        btcQuantity,
        "—"
    );
}


// ============================================================
// HISTORY
// ============================================================

async function loadHistory() {

    try {

        const response =
            await fetch(
                "/api/history"
            );


        if (!response.ok) {

            throw new Error(
                "Erreur historique."
            );
        }


        const data =
            await response.json();


        /*
         * Le backend peut envoyer :
         *
         * [
         *   {...}
         * ]
         *
         * ou
         *
         * {
         *   history: [...]
         * }
         */

        let history =
            Array.isArray(data)
                ? data
                : (
                    data.history ||
                    data.trades ||
                    []
                );


        updateHistory(
            history
        );


    } catch (error) {

        console.error(
            "HISTORY ERROR:",
            error
        );

    }
}


function updateHistory(
    history
) {

    if (!Array.isArray(history)) {
        history = [];
    }


    const total =
        history.length;


    let winCount = 0;
    let lossCount = 0;
    let pnl = 0;


    history.forEach(
        trade => {

            const result =
                String(
                    trade.status ||
                    trade.result ||
                    ""
                ).toUpperCase();


            if (
                result === "WIN" ||
                result === "WON"
            ) {

                winCount++;

            } else if (
                result === "LOSS" ||
                result === "LOST"
            ) {

                lossCount++;
            }


            const value =
                Number(
                    trade.pnl_usd ??
                    trade.pnl ??
                    trade.profit_loss_usd ??
                    0
                );


            if (
                Number.isFinite(value)
            ) {

                pnl += value;
            }

        }
    );


    const rate =
        total > 0
            ? (
                winCount /
                total *
                100
            )
            : 0;


    setText(
        totalTrades,
        total
    );


    setText(
        wins,
        winCount
    );


    setText(
        losses,
        lossCount
    );


    setText(
        winRate,
        rate.toFixed(1) + "%"
    );


    setText(
        totalPnl,
        formatUSD(pnl)
    );


    historyBody.innerHTML = "";


    if (history.length === 0) {

        historyBody.innerHTML = `
            <tr>
                <td colspan="6" class="empty">
                    Aucun trade enregistré.
                </td>
            </tr>
        `;

        return;
    }


    /*
     * Plus récent en premier.
     */

    const sorted =
        [...history].reverse();


    sorted.forEach(
        trade => {

            const row =
                document.createElement(
                    "tr"
                );


            const id =
                trade.id ??
                "—";


            const dir =
                String(
                    trade.direction ||
                    "—"
                ).toUpperCase();


            const entry =
                trade.entry_price ??
                trade.entryPrice;


            const exit =
                trade.exit_price ??
                trade.exitPrice;


            const result =
                String(
                    trade.status ||
                    trade.result ||
                    "—"
                ).toUpperCase();


            const pnlValue =
                Number(
                    trade.pnl_usd ??
                    trade.pnl ??
                    0
                );


            let pnlText = "—";


            if (
                Number.isFinite(
                    pnlValue
                )
            ) {

                pnlText =
                    formatUSD(
                        pnlValue
                    );
            }


            row.innerHTML = `

                <td>
                    #${escapeHtml(id)}
                </td>

                <td class="${dir.toLowerCase()}">
                    ${escapeHtml(dir)}
                </td>

                <td>
                    ${escapeHtml(
                        formatUSD(entry)
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        formatUSD(exit)
                    )}
                </td>

                <td>
                    ${escapeHtml(result)}
                </td>

                <td>
                    ${escapeHtml(pnlText)}
                </td>
            `;


            historyBody.appendChild(
                row
            );
        }
    );
}


// ============================================================
// HTML SECURITY
// ============================================================

function escapeHtml(
    value
) {

    return String(value)
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );
}


// ============================================================
// REFRESH HISTORY
// ============================================================

refreshHistory.addEventListener(
    "click",
    loadHistory
);


// ============================================================
// INITIALISATION
// ============================================================

async function init() {

    await loadSettings();

    await loadHistory();

    connectWebSocket();
}


init();