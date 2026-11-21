from dataclasses import dataclass
import pandas as pd

@dataclass
class Position:
    side: str
    entry_time: pd.Timestamp
    entry: float
    stop: float
    target: float
    initial_risk: float
    trailing_active: bool = False
    lots: int = 1

class PaperBroker:
    def __init__(self, units_per_lot, lots_per_trade=1, round_trip_cost_per_unit=0.0):
        self.units_per_lot = int(units_per_lot)
        self.lots_per_trade = int(lots_per_trade)
        self.cost_per_unit = float(round_trip_cost_per_unit)
        self.position = None
        self.trades = []

    def enter(self, signal):
        if self.position is not None:
            return False
        self.position = Position(signal.side, signal.timestamp, signal.spot_entry,
                                  signal.spot_stop, signal.spot_target,
                                  abs(signal.spot_entry - signal.spot_stop),
                                  lots=self.lots_per_trade)
        return True

    def mark_to_market(self, last_price):
        p = self.position
        if p is None:
            return 0.0
        points = float(last_price) - p.entry if p.side == "BUY" else p.entry - float(last_price)
        units = self.units_per_lot * p.lots
        return points * units - self.cost_per_unit * units

    def force_close(self, timestamp, price, reason="daily_loss_limit"):
        p = self.position
        if p is None:
            return None
        exit_price = float(price)
        points = exit_price - p.entry if p.side == "BUY" else p.entry - exit_price
        units = self.units_per_lot * p.lots
        pnl = points * units - self.cost_per_unit * units
        trade = {"entry_time": p.entry_time, "exit_time": timestamp, "side": p.side,
                 "entry": p.entry, "exit": exit_price, "pnl_points": points,
                 "pnl_inr": pnl, "exit_reason": reason}
        self.trades.append(trade)
        self.position = None
        return trade

    def on_bar(self, timestamp, bar, risk):
        p = self.position
        if p is None:
            return None
        # Conservative: stop takes priority if both stop and target touched in same bar.
        if p.side == "BUY":
            stop_hit = float(bar["low"]) <= p.stop
            target_hit = float(bar["high"]) >= p.target
        else:
            stop_hit = float(bar["high"]) >= p.stop
            target_hit = float(bar["low"]) <= p.target

        if not p.trailing_active and target_hit and not stop_hit:
            p.trailing_active = True
            return None

        if stop_hit:
            exit_price = p.stop
            pnl_points = exit_price - p.entry if p.side == "BUY" else p.entry - exit_price
            units = self.units_per_lot * p.lots
            pnl = pnl_points * units - self.cost_per_unit * units
            trade = {"entry_time": p.entry_time, "exit_time": timestamp, "side": p.side,
                     "entry": p.entry, "exit": exit_price, "pnl_points": pnl_points,
                     "pnl_inr": pnl, "exit_reason": "trailing_stop" if p.trailing_active else "initial_stop"}
            self.trades.append(trade)
            self.position = None
            risk.record_exit(pnl)
            return trade

        if p.trailing_active:
            if p.side == "BUY":
                p.stop = max(p.stop, float(bar["low"]))
            else:
                p.stop = min(p.stop, float(bar["high"]))
        return None
