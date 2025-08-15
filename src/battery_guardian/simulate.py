
from __future__ import annotations
import numpy as np
import pandas as pd
from .model import predict_drain
from .optimizer import optimize_frame, apply_actions_to_drain, explain_actions

def simulate_curves(model, df: pd.DataFrame, start_battery: float = 100.0, hours: int | None = None, aggressiveness: float = 0.6):
    if hours is None:
        hours = len(df)
    df = df.head(hours).copy()
    base_drain = predict_drain(model, df)
    # optimized drain per hour
    actions_list = []
    opt_drain = []
    for i, row in df.iterrows():
        actions = optimize_frame(row, aggressiveness=aggressiveness)
        new_d = apply_actions_to_drain(base_drain[i], actions)
        opt_drain.append(new_d)
        actions_list.append(explain_actions(actions))

    # Integrate to battery percentage
    def integrate(drain_rates):
        b = [start_battery]
        for d in drain_rates:
            b.append(max(0.0, b[-1] - d))  # drain is % per hour
        return b[1:]

    baseline_curve = integrate(base_drain)
    optimized_curve = integrate(opt_drain)

    out = pd.DataFrame({
        "hour": df["hour"].values,
        "baseline_drain_pct_per_h": base_drain,
        "optimized_drain_pct_per_h": opt_drain,
        "baseline_battery_pct": baseline_curve,
        "optimized_battery_pct": optimized_curve,
        "actions": actions_list
    })
    return out
