import pandas as pd
from nifty_algo.levels import confirmed_swings

def test_swing_confirmation_is_delayed():
    idx = pd.date_range("2026-01-01", periods=7, freq="h")
    df = pd.DataFrame({"high":[1,2,3,9,4,3,2], "low":[0,-1,-2,0,-1,-2,-3]}, index=idx)
    events = confirmed_swings(df, 3, 3)
    assert any(t == idx[6] and kind == "resistance" and price == 9
               for t, kind, price, _ in events)
