from pathlib import Path
import pandas as pd
from .data import load_ohlcv, resample_ohlcv
from .levels import previous_day_levels
from .strategy import Strategy
from .execution import PaperBroker
from .risk import DailyRisk

def run_backtest(spot_path, futures_path, cfg):
    spot, fut = load_ohlcv(spot_path), load_ohlcv(futures_path)
    common = spot.index.intersection(fut.index)
    spot, fut = spot.loc[common], fut.loc[common]
    if len(common) == 0:
        raise ValueError("Spot and futures CSVs have no matching timestamps.")
    bars15, bars1h = resample_ohlcv(spot, "15min"), resample_ohlcv(spot, "1h")
    day_levels = previous_day_levels(spot)
    strategy = Strategy(cfg)
    risk_cfg = cfg["risk"]
    units = int(risk_cfg["units_per_lot"])
    if units <= 0:
        raise ValueError("Set risk.units_per_lot in config.yaml to the actual contract lot quantity.")
    broker = PaperBroker(units, risk_cfg["lots_per_trade"],
                         cfg["costs"]["estimated_round_trip_cost_per_unit_inr"])
    risk = DailyRisk(risk_cfg["max_daily_loss_inr"], risk_cfg["max_trades_per_day"])
    for ts in common:
        day = ts.date()
        risk.reset_if_new_day(day)
        # Manage open position first, using futures OHLC.
        if broker.position is not None:
            broker.on_bar(ts, fut.loc[ts], risk)
        if broker.position is not None:
            mtm = broker.mark_to_market(float(fut.loc[ts]["close"]))
            if risk.loss_limit_hit(unrealized=mtm):
                closed = broker.force_close(ts, float(fut.loc[ts]["close"]), "daily_loss_limit")
                if closed:
                    risk.record_exit(closed["pnl_inr"])
                continue
        if broker.position is not None or not risk.can_enter(day):
            continue
        prev = day_levels.get(day, [])
        signal = strategy.generate(spot, fut, ts, bars15, bars1h, prev)
        if signal:
            if risk.can_enter(day):
                broker.enter(signal)
                risk.record_entry()
    # Close any remaining position at final available futures close.
    if broker.position is not None:
        ts = common[-1]
        bar = fut.loc[ts]
        p = broker.position
        exit_price = float(bar["close"])
        points = exit_price - p.entry if p.side == "BUY" else p.entry - exit_price
        pnl = points * units * p.lots - broker.cost_per_unit * units * p.lots
        broker.trades.append({"entry_time": p.entry_time, "exit_time": ts, "side": p.side,
                              "entry": p.entry, "exit": exit_price, "pnl_points": points,
                              "pnl_inr": pnl, "exit_reason": "end_of_data"})
    trades = pd.DataFrame(broker.trades)
    return trades
