
from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass

@dataclass
class Action:
    agent: str
    description: str
    est_saving_pct: float  # proportional saving on drain rate, e.g. 0.05 = 5%

def optimize_frame(row: pd.Series, aggressiveness: float = 0.6) -> list[Action]:
    actions: list[Action] = []
    # CPU agent
    if row["cpu_pct"] > 30:
        actions.append(Action("CPU", "Throttle background tasks by 20%", 0.05*aggressiveness))
    if row["cpu_pct"] > 50:
        actions.append(Action("CPU", "Limit peak CPU to 85%", 0.06*aggressiveness))

    # Display agent
    if row["screen_min"] > 40:
        actions.append(Action("Display", "Lower brightness by 20%", 0.07*aggressiveness))
        actions.append(Action("Display", "Reduce refresh rate to 60Hz", 0.04*aggressiveness))

    # Network agent
    if row["net_mb"] > 150:
        actions.append(Action("Network", "Defer background sync", 0.05*aggressiveness))

    # Sensor agent
    if row["sensors_util"] > 0.6:
        actions.append(Action("Sensors", "Disable GPS in background", 0.08*aggressiveness))

    # Intent-aware override (prefer performance)
    if row.get("intent") == "performance":
        # reduce overall aggressiveness
        for a in actions:
            a.est_saving_pct *= 0.6

    return actions

def apply_actions_to_drain(base_drain: float, actions: list[Action]) -> float:
    # Combine multiplicatively for diminishing returns
    new_drain = base_drain
    for a in actions:
        new_drain *= (1.0 - max(0.0, min(0.4, a.est_saving_pct)))
    return max(new_drain, 0.1)

def explain_actions(actions: list[Action]) -> list[dict]:
    return [dict(agent=a.agent, description=a.description, est_saving_pct=round(a.est_saving_pct*100, 2)) for a in actions]
