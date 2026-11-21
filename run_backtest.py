import argparse
from pathlib import Path
from nifty_algo.config import load_config
from nifty_algo.backtest import run_backtest

def main():
    p = argparse.ArgumentParser(description="NIFTY Futures V2.6 paper backtest")
    p.add_argument("--spot", required=True)
    p.add_argument("--futures", required=True)
    p.add_argument("--config", default="config.yaml")
    args = p.parse_args()
    cfg = load_config(args.config)
    trades = run_backtest(args.spot, args.futures, cfg)
    out = Path(cfg["backtest"]["output_dir"])
    out.mkdir(parents=True, exist_ok=True)
    path = out / "trades.csv"
    trades.to_csv(path, index=False)
    print(f"Trades: {len(trades)}")
    if len(trades):
        print(f"Net P&L (before full statutory charge model): ₹{trades['pnl_inr'].sum():,.2f}")
        print(f"Win rate: {(trades['pnl_inr'] > 0).mean()*100:.1f}%")
    print(f"Journal: {path}")

if __name__ == "__main__":
    main()
