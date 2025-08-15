
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Tuple
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor

def _make_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    X = df[["cpu_pct", "net_mb", "screen_min", "sensors_util"]].copy()
    # simple interactions
    X["cpu_screen"] = X["cpu_pct"] * X["screen_min"]
    X["net_screen"] = X["net_mb"] * X["screen_min"]
    # intent flag
    X["intent_perf"] = (df.get("intent", "eco") == "performance").astype(int)
    # target: battery drain rate %/h
    # If 'drain_pct_per_h' not provided, synthesize using heuristic
    if "drain_pct_per_h" in df.columns:
        y = df["drain_pct_per_h"]
    else:
        # heuristic generator for synthetic target
        y = 0.03*X["cpu_pct"] + 0.01*X["net_mb"] + 0.05*X["screen_min"] + 7.5*X["sensors_util"] \
            + 0.0002*X["cpu_screen"] + 0.00005*X["net_screen"] + 2.0*X["intent_perf"] + 1.0
    return X, y

def train_model(train_df: pd.DataFrame):
    X, y = _make_features(train_df)
    try:
        model = RandomForestRegressor(n_estimators=150, random_state=0)
        model.fit(X, y)
    except Exception:
        model = LinearRegression()
        model.fit(X, y)
    return model

def predict_drain(model, df: pd.DataFrame) -> np.ndarray:
    X, _ = _make_features(df)
    return model.predict(X)
