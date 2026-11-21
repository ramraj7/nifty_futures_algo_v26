# NIFTY Futures Algo — Strategy V2.6

A **paper-trading/backtesting starter system** implementing the agreed V2.6 rules.
It does not place live orders and does not connect to a broker.

## What is included

- NIFTY 50 spot candles for signals; NIFTY Futures candles for simulated fills/P&L.
- 5-minute entry signals, 15-minute and 1-hour swing levels.
- Confirmed swing points: 3 candles on either side; a pivot is available only after the 3 right-side candles close.
- Previous session high/low and previous session's final 15-minute candle high/low as S/R references.
- Opening-gap detection and 15-minute opening-candle confirmation.
- 5-point breakout/breakdown buffer.
- Opposing-level reward/risk filter; fixed 1:2 fallback if no opposing level is found.
- Initial stop from the 5-minute breakout/breakdown candle.
- 5-minute trailing after 1:2 is reached; no partial exits.
- 1 lot per trade, maximum 3 entries/day, one open position, ₹3,500 daily loss cutoff.
- CSV trade journal and a basic Streamlit dashboard.

## Important assumptions requiring validation

1. Input timestamps represent **candle close times**, in `Asia/Kolkata`.
2. Opening gap is calculated from the first 5-minute spot candle open versus the previous session's close.
3. A gap session requires a subsequent completed 15-minute candle to close above the first 15-minute candle's high for BUY eligibility, or below its low for SELL eligibility. This confirmation is required for both gap-up and gap-down sessions.
4. For a gap greater than 75 NIFTY points, no entry is allowed until the relevant opening-range confirmation and a normal S/R breakout/breakdown are confirmed.
5. All S/R levels (1H, 15M and previous-day references) are considered as possible opposing levels. If no valid opposing level exists, the target falls back to 1:2.
6. Signal levels are calculated from NIFTY spot. The backtest maps the spot entry/stop/target distances onto futures using the futures-minus-spot basis at signal time. This is an approximation and must be validated.
7. If stop and target are both touched within the same 5-minute bar, the backtest assumes the stop is hit first (conservative).
8. Daily loss is a cutoff trigger, not a guaranteed maximum loss; gaps/slippage can exceed it.
9. The final 15-minute candle is the last completed 15-minute bar of the previous session.
10. The 75-point gap threshold is applied to absolute gap size; both gap-up and gap-down sessions are subject to the opening-range confirmation.

## Data format

Create two CSV files:

- `data/nifty_spot_5m.csv`
- `data/nifty_futures_5m.csv`

Required columns:

`timestamp,open,high,low,close,volume`

- Timestamps must be parseable and represent candle close time.
- Both files must contain matching 5-minute timestamps.
- Use actual historical NIFTY spot and the selected NIFTY futures contract data.
- Do not mix continuous futures back-adjusted data with a live contract without accounting for roll differences.

## Install

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
```

## Run a backtest

```bash
python run_backtest.py --spot data/nifty_spot_5m.csv --futures data/nifty_futures_5m.csv
```

Set the actual current contract lot quantity in `config.yaml` before interpreting rupee P&L.
`lots_per_trade` remains 1; `units_per_lot` must be updated from the exchange/broker instrument master because lot sizes can change.

## Dashboard

```bash
streamlit run dashboard.py
```

## Next step for live market data

A broker adapter is intentionally not included in this first safe release. A Zerodha Kite Connect adapter can be added after confirming the account/API setup and current instrument-token/contract selection process. Keep API keys and access tokens in environment variables; never commit them to Git.

## Safety

This is software scaffolding, not a validated profitable strategy. Before any live use:
- Verify candle alignment and all rules against chart examples.
- Run out-of-sample backtests across multiple market regimes.
- Include brokerage, STT, exchange charges, GST, SEBI fees, stamp duty, spread and slippage.
- Paper trade for a sustained period.
- Add reconnect handling, order-state reconciliation, kill switch and broker-side safeguards.
- Review applicable exchange/broker and SEBI requirements.
