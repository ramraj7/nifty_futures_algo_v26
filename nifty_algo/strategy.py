from dataclasses import dataclass
from math import isfinite
import pandas as pd
from .levels import confirmed_swings, previous_day_levels
from .data import resample_ohlcv

@dataclass
class Signal:
    side: str
    timestamp: pd.Timestamp
    spot_entry: float
    spot_stop: float
    spot_target: float
    reason: str
    opposing_level: float | None
    risk_points: float
    reward_points: float

class Strategy:
    def __init__(self, cfg):
        self.cfg = cfg["strategy"]
        self.left = int(self.cfg["swing_left_bars"])
        self.right = int(self.cfg["swing_right_bars"])
        self.buffer = float(self.cfg["breakout_buffer_points"])
        self.gap_threshold = float(self.cfg["large_gap_points"])
        self.min_rr = float(self.cfg["min_level_reward_risk"])
        self.fallback_rr = float(self.cfg["fallback_reward_risk"])

    def build_timeframes(self, spot):
        return resample_ohlcv(spot, "15min"), resample_ohlcv(spot, "1h")

    def _levels_asof(self, bars, timestamp, side):
        available = bars.loc[bars.index <= timestamp]
        if len(available) < self.left + self.right + 1:
            return []
        events = confirmed_swings(available, self.left, self.right)
        kind = "resistance" if side == "BUY" else "support"
        return [price for t, k, price, _ in events if t <= timestamp and k == kind]

    def _opening_confirmation(self, bars15, timestamp, side, day):
        day_bars = bars15[(bars15.index.date == day) & (bars15.index <= timestamp)]
        if len(day_bars) < 2:
            return False
        opening = day_bars.iloc[0]
        later = day_bars.iloc[1:]
        if side == "BUY":
            return bool((later["close"] > opening["high"]).any())
        return bool((later["close"] < opening["low"]).any())

    def generate(self, spot, futures, timestamp, bars15, bars1h, prev_levels):
        # A decision is made only after a completed 5m spot candle.
        s = spot.loc[timestamp]
        pos = spot.index.get_loc(timestamp)
        if not isinstance(pos, int) or pos == 0:
            return None
        previous_spot_close = float(spot.iloc[pos - 1]["close"])
        day = timestamp.date()
        prior = spot[spot.index.date < day]
        if prior.empty:
            return None
        previous_close = float(prior.iloc[-1]["close"])
        gap = float(s["open"]) - previous_close
        gap_abs = abs(gap)

        # For any non-flat gap, the direction-specific 15m opening-range
        # confirmation is mandatory. A later 15m candle must close fully
        # above the opening candle high (BUY) or below its low (SELL).
        # The >75-point rule is an additional explicit wait condition.
        for side in ("BUY", "SELL"):
            if gap_abs > 0 and not self._opening_confirmation(bars15, timestamp, side, day):
                continue
            if gap_abs > self.gap_threshold:
                if side == "BUY" and not self._opening_confirmation(bars15, timestamp, "BUY", day):
                    continue
                if side == "SELL" and not self._opening_confirmation(bars15, timestamp, "SELL", day):
                    continue

            level_kind = "resistance" if side == "BUY" else "support"
            candidates = self._levels_asof(bars15, timestamp, side) + self._levels_asof(bars1h, timestamp, side)
            candidates += [p for k, p, _ in prev_levels if k == level_kind]
            if side == "BUY":
                crossed = [p for p in candidates
                           if previous_spot_close <= p + self.buffer
                           and float(s["close"]) > p + self.buffer]
                if not crossed:
                    continue
                trigger = max(crossed)
                stop = float(s["low"])
                entry = float(s["close"])
                risk = entry - stop
                future_levels = [p for k, p, _ in prev_levels if k == "resistance" and p > entry]
                future_levels += [p for p in self._levels_asof(bars15, timestamp, side) + self._levels_asof(bars1h, timestamp, side) if p > entry]
                opposing = min(future_levels) if future_levels else None
                reward = (opposing - entry) if opposing is not None else risk * self.fallback_rr
                target = entry + risk * self.fallback_rr
            else:
                crossed = [p for p in candidates
                           if previous_spot_close >= p - self.buffer
                           and float(s["close"]) < p - self.buffer]
                if not crossed:
                    continue
                trigger = min(crossed)
                stop = float(s["high"])
                entry = float(s["close"])
                risk = stop - entry
                future_levels = [p for k, p, _ in prev_levels if k == "support" and p < entry]
                future_levels += [p for p in self._levels_asof(bars15, timestamp, side) + self._levels_asof(bars1h, timestamp, side) if p < entry]
                opposing = max(future_levels) if future_levels else None
                reward = (entry - opposing) if opposing is not None else risk * self.fallback_rr
                target = entry - risk * self.fallback_rr

            if risk <= 0 or not isfinite(risk) or reward <= 0:
                continue
            rr = reward / risk
            if opposing is not None and rr < self.min_rr:
                continue
            basis = float(futures.loc[timestamp]["close"]) - float(s["close"])
            return Signal(side, timestamp, entry + basis, stop + basis, target + basis,
                          f"{side} breakout of {trigger:.2f}; RR={rr:.2f}", opposing,
                          risk, reward)
        return None
