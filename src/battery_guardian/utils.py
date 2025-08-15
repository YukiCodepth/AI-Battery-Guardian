
from __future__ import annotations
import pandas as pd

def compute_savings(df: pd.DataFrame) -> dict:
    base_end = df["baseline_battery_pct"].iloc[-1]
    opt_end = df["optimized_battery_pct"].iloc[-1]
    saved_pct = max(0.0, opt_end - base_end)
    # "extra hours" until reaching 20% threshold
    th = 20.0
    def hours_until(bcurve):
        ok = (bcurve > th).astype(int)
        return ok.sum()
    extra_hours = hours_until(df["optimized_battery_pct"]) - hours_until(df["baseline_battery_pct"])
    return {
        "battery_saved_pct": round(saved_pct, 2),
        "extra_hours_above_20pct": int(max(0, extra_hours))
    }
