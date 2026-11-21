import pandas as pd

def confirmed_swings(df, left=3, right=3):
    """Return pivot events indexed by confirmation time, never by pivot time."""
    events = []
    highs = df["high"].tolist()
    lows = df["low"].tolist()
    idx = list(df.index)
    for pivot_i in range(left, len(df) - right):
        hi = highs[pivot_i]
        lo = lows[pivot_i]
        window_hi = highs[pivot_i-left:pivot_i+right+1]
        window_lo = lows[pivot_i-left:pivot_i+right+1]
        # Strict pivot; ties are not treated as a swing.
        if hi == max(window_hi) and window_hi.count(hi) == 1:
            events.append((idx[pivot_i+right], "resistance", float(hi), "swing"))
        if lo == min(window_lo) and window_lo.count(lo) == 1:
            events.append((idx[pivot_i+right], "support", float(lo), "swing"))
    return sorted(events, key=lambda x: x[0])

def previous_day_levels(spot_5m):
    """Map each session's prior-day levels and prior session's final 15m candle levels."""
    x = spot_5m.copy()
    x["session"] = x.index.date
    days = sorted(x["session"].unique())
    result = {}
    for i in range(1, len(days)):
        prev_day, day = days[i-1], days[i]
        prev = x[x["session"] == prev_day]
        prev15 = prev.resample("15min", label="right", closed="right",
                               origin="start_day", offset="9h15min").agg({
            "open":"first","high":"max","low":"min","close":"last"
        }).dropna()
        if prev.empty or prev15.empty:
            continue
        last15 = prev15.iloc[-1]
        result[day] = [
            ("resistance", float(prev["high"].max()), "previous_day_high"),
            ("support", float(prev["low"].min()), "previous_day_low"),
            ("resistance", float(last15["high"]), "previous_day_final_15m_high"),
            ("support", float(last15["low"]), "previous_day_final_15m_low"),
        ]
    return result
