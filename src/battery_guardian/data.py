
from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass

@dataclass
class AppProfile:
    name: str
    base_cpu: float        # %
    base_net: float        # MB/h
    base_screen: float     # minutes/h (proxy for brightness/activity)
    base_sensors: float    # 0..1 (GPS/IMU usage)
    intent: str            # "performance" or "eco"

def sample_catalog() -> list[AppProfile]:
    return [
        AppProfile("YouTube", 35, 400, 55, 0.2, "performance"),
        AppProfile("Instagram", 28, 250, 50, 0.1, "performance"),
        AppProfile("BGMI / Gaming", 55, 120, 60, 0.4, "performance"),
        AppProfile("Maps / Navigation", 30, 80, 50, 0.9, "performance"),
        AppProfile("Chrome / Reading", 12, 60, 40, 0.1, "eco"),
        AppProfile("WhatsApp", 6, 20, 25, 0.0, "eco"),
    ]

def generate_synthetic_usage(profile: AppProfile, hours: int = 12, noise: float = 0.1, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    t = np.arange(hours)
    # simulate diurnal variation & user bursts
    burst = (np.sin((t / hours) * 2*np.pi) + 1) / 2  # 0..1
    cpu = profile.base_cpu * (0.8 + 0.4*burst) * (1 + noise*rng.normal(size=hours))
    net = profile.base_net * (0.6 + 0.8*burst) * (1 + noise*rng.normal(size=hours))
    screen = profile.base_screen * (0.7 + 0.6*burst) * (1 + noise*rng.normal(size=hours))
    sensors = profile.base_sensors * (0.7 + 0.6*burst) * (1 + noise*rng.normal(size=hours))
    # clamp
    cpu = np.clip(cpu, 0, 100)
    net = np.clip(net, 0, None)
    screen = np.clip(screen, 0, 60)
    sensors = np.clip(sensors, 0, 1)
    df = pd.DataFrame({
        "hour": t,
        "cpu_pct": cpu,
        "net_mb": net,
        "screen_min": screen,
        "sensors_util": sensors,
        "intent": profile.intent
    })
    return df
