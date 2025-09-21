#!/usr/bin/env python3
"""
Exogenous Data Loader (Top 25 Leaders + Sectors + Risk + Macro)
================================================================
Builds a weekly, stationary feature matrix for an S&P 500 forecast project,
**excluding the S&P target** (you'll merge your own flat file).

Key features:
- Top-25 company returns (log) with user-supplied **weights** and a **weighted composite**
- Sector ETFs (all 11 GICS) weekly log-returns
- Breadth/Concentration proxies: SPY−RSP and XLK−SPY weekly return spreads
- Risk/Commodities/FX: VIX, DXY, WTI, GOLD weekly log-returns
- Macro (FRED): 10y & 2y yields, CPI, Unemployment, PMI, HY/IG OAS → weekly first differences
- All aligned to weekly W-FRI index
- Outputs a single CSV for modeling

Usage
-----
python exogenous_loader_top25.py --start 2015-01-01 --end 2025-12-31 \
    --outfile exogenous_features_top25_weekly.csv

Options
-------
--weights equal      -> use equal weights (1/N) for Top-25 composite
--weights supplied   -> (default) use weights embedded in this script
"""

import argparse
from datetime import datetime
import sys
from typing import Dict, List

import numpy as np
import pandas as pd

# dependencies
try:
    import yfinance as yf
except Exception as e:
    print("Missing dependency yfinance. Install with: pip install yfinance", file=sys.stderr)
    raise

try:
    from pandas_datareader import data as pdr
except Exception as e:
    print("Missing dependency pandas_datareader. Install with: pip install pandas_datareader", file=sys.stderr)
    raise


# -----------------------------
# Top 25 tickers with weights
# -----------------------------
# Note: Berkshire Hathaway Class B is "BRK-B" in Yahoo Finance.
TOP25_WEIGHTS = {
    "NVDA": 8.06,
    "MSFT": 7.37,
    "AAPL": 5.76,
    "AMZN": 4.11,
    "META": 3.12,
    "AVGO": 2.57,
    "GOOGL": 2.08,
    "GOOG": 1.68,
    "BRK-B": 1.61,
    "TSLA": 1.61,
    "JPM": 1.53,
    "V": 1.10,
    "LLY": 1.08,
    "NFLX": 0.92,
    "XOM": 0.89,
    "MA": 0.85,
    "WMT": 0.79,
    "COST": 0.77,
    "ORCL": 0.77,
    "JNJ": 0.74,
    "HD": 0.68,
    "PG": 0.66,
    "PLTR": 0.63,
    "ABBV": 0.62,
    "BAC": 0.58,
}
TOP25_TICKERS = list(TOP25_WEIGHTS.keys())

# -----------------------------
# Sector ETFs (11 GICS sectors)
# -----------------------------
SECTOR_ETFS = ["XLK","XLY","XLC","XLF","XLE","XLV","XLI","XLP","XLU","XLRE","XLB"]

# -----------------------------
# Risk/FX/Commodities
# -----------------------------
RISK_FX_CMDTY = {
    "VIX": "^VIX",
    "DXY": "DX-Y.NYB",
    "WTI": "CL=F",
    "GOLD": "GC=F",
}

# -----------------------------
# Macro from FRED
# -----------------------------
FRED_SERIES = {
    "DGS10": "DGS10",
    "DGS2": "DGS2",
    "CPI": "CPIAUCSL",
    "UNRATE": "UNRATE",
    "PMI": "NAPM",
    "HY_OAS": "BAMLH0A0HYM2",
    "IG_OAS": "BAMLC0A0CM",
}


# -----------------------------
# Helpers
# -----------------------------
def to_weekly_last(df: pd.DataFrame) -> pd.DataFrame:
    return df.resample("W-FRI").last()

def log_returns(df: pd.DataFrame) -> pd.DataFrame:
    lr = np.log(df).diff()
    return lr.dropna(how="all")

def first_difference(df: pd.DataFrame) -> pd.DataFrame:
    d = df.diff()
    return d.dropna(how="all")

def fetch_yf_prices(tickers: List[str], start: str, end: str) -> pd.DataFrame:
    df = yf.download(tickers, start=start, end=end, auto_adjust=False, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        if "Adj Close" in df.columns.get_level_values(0):
            df = df["Adj Close"]
        elif "Close" in df.columns.get_level_values(0):
            df = df["Close"]
    if isinstance(df, pd.Series):
        df = df.to_frame()
    return df

def fetch_fred(series_map: Dict[str,str], start: str, end: str) -> pd.DataFrame:
    frames = []
    for name, code in series_map.items():
        s = pdr.DataReader(code, "fred", start, end).rename(columns={code: name})
        frames.append(s)
    return pd.concat(frames, axis=1)

def safe_join(left: pd.DataFrame, right: pd.DataFrame) -> pd.DataFrame:
    return left.join(right, how="outer").sort_index()

def normalize_weights(w: Dict[str, float]) -> Dict[str, float]:
    arr = np.array(list(w.values()), dtype=float)
    s = arr.sum()
    return {k: (float(v)/s if s != 0 else 1.0/len(w)) for k,v in w.items()}


# -----------------------------
# Pipeline
# -----------------------------
def build_features(start: str, end: str, use_equal_weights: bool=False) -> pd.DataFrame:
    # 1) Top-25 returns
    top25_px = fetch_yf_prices(TOP25_TICKERS, start, end)
    top25_px.columns = [f"{c}_PX" for c in top25_px.columns]
    top25_w = to_weekly_last(top25_px)
    top25_lr = log_returns(top25_w)
    top25_lr.columns = [c.replace("_PX","_LR") for c in top25_lr.columns]

    # Composite
    weights = normalize_weights(TOP25_WEIGHTS) if not use_equal_weights else {k:1/len(TOP25_WEIGHTS) for k in TOP25_WEIGHTS}
    composite = pd.Series(0.0, index=top25_lr.index)
    for col in top25_lr.columns:
        tkr = col.replace("_LR","")
        composite = composite.add(top25_lr[col].fillna(0.0) * weights.get(tkr,0.0), fill_value=0.0)
    top25_lr["TOP25_WEIGHTED_LR"] = composite

    # 2) Sector ETFs
    sectors_px = fetch_yf_prices(SECTOR_ETFS, start, end)
    sectors_px.columns = [f"{c}_PX" for c in sectors_px.columns]
    sectors_w = to_weekly_last(sectors_px)
    sectors_lr = log_returns(sectors_w)
    sectors_lr.columns = [c.replace("_PX","_LR") for c in sectors_lr.columns]

    # 3) Breadth/Concentration
    spreads_px = fetch_yf_prices(["SPY","RSP","XLK"], start, end)
    spreads_px.columns = [f"{c}_PX" for c in spreads_px.columns]
    spreads_w = to_weekly_last(spreads_px)
    spreads_lr = log_returns(spreads_w)
    spreads_lr.columns = [c.replace("_PX","_LR") for c in spreads_lr.columns]
    spreads_lr["SPY_minus_RSP_LR"] = spreads_lr["SPY_LR"] - spreads_lr["RSP_LR"]
    spreads_lr["XLK_minus_SPY_LR"] = spreads_lr["XLK_LR"] - spreads_lr["SPY_LR"]
    spreads_only = spreads_lr[["SPY_minus_RSP_LR","XLK_minus_SPY_LR"]]

    # 4) Risk/Commodities
    risk_frames = []
    for name, ticker in RISK_FX_CMDTY.items():
        px = fetch_yf_prices([ticker], start, end)
        px.columns = [f"{name}_PX"]
        w = to_weekly_last(px)
        lr = log_returns(w).rename(columns={f"{name}_PX": f"{name}_LR"})
        risk_frames.append(lr)
    risk_lr = pd.concat(risk_frames, axis=1)

    # 5) Macro
    fred = fetch_fred(FRED_SERIES, start, end)
    if {"DGS10","DGS2"}.issubset(fred.columns):
        fred["SPREAD_2s10s"] = fred["DGS10"] - fred["DGS2"]
    fred_w = to_weekly_last(fred).ffill()
    fred_diff = first_difference(fred_w).add_suffix("_CHG")

    # Merge
    feat = top25_lr
    feat = safe_join(feat, sectors_lr)
    feat = safe_join(feat, spreads_only)
    feat = safe_join(feat, risk_lr)
    feat = safe_join(feat, fred_diff)

    return feat.dropna(how="all")


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=str, default="2015-01-01")
    ap.add_argument("--end", type=str, default=None)
    ap.add_argument("--outfile", type=str, default="exogenous_features_top25_weekly.csv")
    ap.add_argument("--weights", choices=["supplied","equal"], default="supplied")
    return ap.parse_args()


def main():
    args = parse_args()
    end = args.end or datetime.today().strftime("%Y-%m-%d")
    use_equal = (args.weights=="equal")
    feat = build_features(args.start, end, use_equal_weights=use_equal)
    print(f"[INFO] Final shape {feat.shape}")
    feat.to_csv(args.outfile)
    print(f"[DONE] Wrote {args.outfile}")


if __name__ == "__main__":
    main()
