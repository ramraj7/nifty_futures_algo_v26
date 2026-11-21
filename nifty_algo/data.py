import pandas as pd

REQUIRED = {"timestamp", "open", "high", "low", "close", "volume"}

def load_ohlcv(path):
    df = pd.read_csv(path)
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"{path}: missing columns {sorted(missing)}")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="raise")
    df = df.sort_values("timestamp").drop_duplicates("timestamp").set_index("timestamp")
    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="raise")
    if not (df["high"] >= df[["open", "close", "low"]].max(axis=1)).all():
        raise ValueError(f"{path}: invalid high values")
    if not (df["low"] <= df[["open", "close", "high"]].min(axis=1)).all():
        raise ValueError(f"{path}: invalid low values")
    return df

def resample_ohlcv(df, rule):
    # Input index is candle close time. Only completed source candles are aggregated.
    return df.resample(rule, label="right", closed="right", origin="start_day",
                       offset="9h15min").agg({
        "open": "first", "high": "max", "low": "min",
        "close": "last", "volume": "sum"
    }).dropna(subset=["open", "high", "low", "close"])
