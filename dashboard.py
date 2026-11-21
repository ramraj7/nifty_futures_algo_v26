from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="NIFTY Algo V2.6", layout="wide")
st.title("NIFTY Futures Algo — V2.6")
st.caption("Backtest / paper-trading journal viewer. No live orders are placed.")
path = Path("outputs/trades.csv")
if not path.exists():
    st.info("Run a backtest first to create outputs/trades.csv.")
else:
    df = pd.read_csv(path)
    if df.empty:
        st.warning("No trades found.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Trades", len(df))
        c2.metric("Net P&L", f"₹{df.pnl_inr.sum():,.2f}")
        c3.metric("Win rate", f"{(df.pnl_inr > 0).mean()*100:.1f}%")
        st.dataframe(df, use_container_width=True)
        st.line_chart(df["pnl_inr"].cumsum())
