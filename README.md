# BTC AI Scanner V3

Prototype de recherche / paper-trading pour BTC/USDT.

## Ajouts de cette version

- Un seul trade/signale à la fois.
- Tant que le trade est ouvert, le scanner affiche `TRADE ACTIVE` et **ne crée aucun nouveau signal**.
- Le trade se clôture automatiquement sur :
  - Stop Loss
  - Take Profit
  - sortie au temps prévu
- Après la clôture, le scanner peut chercher un nouveau signal.
- Historique persistant des trades clôturés dans `backend/trade_history.json`.
- Tableau de statistiques :
  - nombre total de trades
  - gains
  - pertes
  - taux de réussite
  - P&L cumulé en %
  - trade actuellement ouvert
- Page `Historique & Résultats` pour suivre chaque trade.
- Paper trading uniquement : aucun ordre réel n'est envoyé.

## Installation

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

Puis ouvrir `http://127.0.0.1:8000`.

### Important

Le P&L est calculé en pourcentage sur chaque signal, sans frais ni slippage. Il s'agit d'un suivi de performance du scanner, pas d'un relevé de compte Binance.


## Déploiement Render — V3

### Build Command
```bash
pip install -r backend/requirements.txt
```

### Start Command
```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

### Health Check
```text
/healthz
```

Le fichier `render.yaml` contient déjà cette configuration. Le scanner reste en paper trading : aucun ordre réel Binance n'est envoyé.

### Persistance
`backend/trade_history.json` reste un stockage local de prototype. Pour une persistance durable sur Render, migrer l'historique vers PostgreSQL dans une prochaine version.
