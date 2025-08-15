
from __future__ import annotations
import math
from typing import List, Dict

def _fmt_minutes(minutes: float) -> str:
    m = int(round(minutes))
    if m < 60:
        return f"{m} min"
    h = m // 60
    r = m % 60
    return f"{h}h {r}m" if r else f"{h}h"

def estimate_time_gain(drain_before: float, drain_after: float, current_battery_pct: float) -> str:
    """Rough estimate of extra time gained at current battery level."""
    if drain_before <= 0 or drain_after <= 0:
        return "N/A"
    hours_before = current_battery_pct / drain_before
    hours_after = current_battery_pct / drain_after
    gain_h = max(0.0, hours_after - hours_before)
    return _fmt_minutes(gain_h * 60)

def generate_tips(row, drain_before: float, drain_after: float, battery_pct: float) -> List[Dict]:
    tips = []
    perf_mode = (row.get("intent") == "performance")

    # Brightness/Display
    if row["screen_min"] > 35:
        gain = estimate_time_gain(drain_before, max(drain_after*0.93, 0.1), battery_pct)
        tips.append({
            "title": "Reduce brightness 15–25%",
            "reason": "High screen time detected; display is a major power draw.",
            "est_gain": gain,
            "type": "display",
            "priority": 1
        })
        tips.append({
            "title": "Lower refresh rate to 60Hz",
            "reason": "High-motion content consumes extra display power.",
            "est_gain": estimate_time_gain(drain_before, max(drain_after*0.96, 0.1), battery_pct),
            "type": "display",
            "priority": 2
        })

    # CPU / Background
    if row["cpu_pct"] > 40:
        tips.append({
            "title": "Limit background CPU tasks",
            "reason": "Background computations above 40% detected.",
            "est_gain": estimate_time_gain(drain_before, max(drain_after*0.95, 0.1), battery_pct),
            "type": "cpu",
            "priority": 1
        })
    if row["cpu_pct"] > 60 and not perf_mode:
        tips.append({
            "title": "Cap peak CPU to 85%",
            "reason": "Sustained high CPU usage; capping prevents spikes.",
            "est_gain": estimate_time_gain(drain_before, max(drain_after*0.92, 0.1), battery_pct),
            "type": "cpu",
            "priority": 2
        })

    # Network
    if row["net_mb"] > 150:
        tips.append({
            "title": "Defer background sync & prefetch",
            "reason": "Heavy network transfers drain radio & CPU.",
            "est_gain": estimate_time_gain(drain_before, max(drain_after*0.95, 0.1), battery_pct),
            "type": "network",
            "priority": 1
        })

    # Sensors
    if row["sensors_util"] > 0.6:
        tips.append({
            "title": "Disable GPS when in background",
            "reason": "High sensor usage detected (likely GPS).",
            "est_gain": estimate_time_gain(drain_before, max(drain_after*0.92, 0.1), battery_pct),
            "type": "sensors",
            "priority": 1
        })

    # Low battery emergencies
    if battery_pct <= 20:
        tips.append({
            "title": "Enable Ultra Battery Saver",
            "reason": "Battery under 20%; aggressive savings recommended.",
            "est_gain": estimate_time_gain(drain_before, max(drain_after*0.85, 0.1), battery_pct),
            "type": "system",
            "priority": 0
        })

    # Sort by priority, then by estimated gain (rough heuristic by length of string minutes)
    def gain_to_minutes(g: str) -> int:
        if not g or g == "N/A": return 0
        # "1h 20m" or "45 min"
        if "h" in g:
            parts = g.replace("m","").split("h")
            h = int(parts[0].strip())
            m = int(parts[1].strip()) if parts[1].strip() else 0
            return h*60 + m
        return int(g.split()[0])
    tips.sort(key=lambda t: (t["priority"], -gain_to_minutes(t["est_gain"])))
    return tips[:5]  # top 5

def chatbot_reply(message: str, context: dict) -> str:
    message = (message or "").lower().strip()
    app = context.get("app", "the app")
    battery = context.get("battery", 50)
    extra = context.get("extra_hours", 0)
    if "save" in message or "battery" in message or "tips" in message:
        return f"Right now, {app} can gain about {extra} extra hour(s) above 20% if you apply my recommended optimizations. Start with brightness and background CPU limits."
    if "brightness" in message:
        return "Lowering brightness by 20% typically saves 5–10% drain per hour for screen-heavy apps. Try it when your screen time is high."
    if "network" in message or "wifi" in message or "data" in message:
        return "Heavy background sync can drain quickly. Defer sync and disable auto-play to reduce radio usage."
    if "gps" in message or "location" in message or "sensors" in message:
        return "If you don't need continuous navigation, disable GPS in background to cut sensor drain."
    if "cpu" in message or "performance" in message:
        return "Capping peak CPU to ~85% can smooth spikes with minimal impact on perceived performance in most apps."
    if "hello" in message or "hi" in message:
        return "Hi! Ask me how to save battery, or what to optimize right now."
    return "You can ask: 'How can I save battery now?', 'Should I lower brightness?', 'Is background sync draining power?'"
