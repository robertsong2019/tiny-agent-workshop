#!/usr/bin/env python3
"""
Edge Agent — Sensor → Reason → Act Loop
Simulates an AI agent running on a resource-constrained edge device.

No LLM API needed. Pure local simulation of the embedded agent pattern:
  1. Read sensors (temperature, humidity, etc.)
  2. Apply lightweight reasoning (rule-based + state machine)
  3. Control actuators (fan, heater, valve)
  4. Manage battery/power (sleep modes, adaptive scheduling)

This is how agents work on microcontrollers — no cloud, no GPU, just logic.

Usage: python edge_agent.py [ticks] [--verbose]

Inspired by TAP (Tiny Agent Protocol) and edge-agent-runtime patterns.
"""

import json, random, time, sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# ─── Hardware Abstraction ───────────────────────────────────────────

class PowerMode(Enum):
    ACTIVE = "active"       # Full speed, all sensors on
    IDLE = "idle"           # Reduced sensor frequency
    SLEEP = "sleep"         # Minimal, wake on threshold breach

@dataclass
class SensorReading:
    temperature: float   # °C
    humidity: float       # %
    soil_moisture: float  # % (0 = dry, 100 = saturated)
    light: float          # lux (0 = dark, 1000 = full sun)
    battery: float        # % (0-100)
    timestamp: float = 0.0

@dataclass
class ActuatorState:
    fan: bool = False
    heater: bool = False
    valve: bool = False   # Water valve
    light_on: bool = False

class Sensors:
    """Simulates hardware sensors with realistic drift + occasional extreme events."""
    def __init__(self):
        self._temp = 22.0
        self._hum = 55.0
        self._soil = 40.0
        self._light = 500.0
        self._battery = 85.0
        self._tick = 0

    def read(self) -> SensorReading:
        self._tick += 1

        # Simulate environmental drift
        self._temp += random.gauss(0, 0.3)
        self._hum += random.gauss(0, 1.0)
        self._soil += random.gauss(-0.2, 0.5)  # Slowly drying
        self._light += random.gauss(0, 20)
        self._battery -= random.uniform(0.1, 0.5)

        # Dramatic events at specific ticks (for demo purposes)
        if self._tick == 8:
            self._temp += 12   # Heat wave!
            self._soil -= 15   # Sudden dry spell
        elif self._tick == 18:
            self._temp -= 10   # Cold snap!
            self._light = 10   # Dark storm
        elif self._tick == 25:
            self._soil += 35   # Heavy rain
        elif self._tick == 30:
            self._battery = 18  # Battery crisis

        # Clamp
        self._temp = max(5, min(45, self._temp))
        self._hum = max(10, min(99, self._hum))
        self._soil = max(0, min(100, self._soil))
        self._light = max(0, min(1000, self._light))
        self._battery = max(0, min(100, self._battery))

        return SensorReading(
            temperature=round(self._temp, 1),
            humidity=round(self._hum, 1),
            soil_moisture=round(self._soil, 1),
            light=round(self._light, 1),
            battery=round(self._battery, 1),
            timestamp=time.time(),
        )

# ─── Lightweight Reasoner ───────────────────────────────────────────

class EdgeReasoner:
    """
    Rule-based reasoner that fits in < 10KB on a microcontroller.
    This is the 'AI' part — simple rules that create emergent behavior.
    """
    def __init__(self):
        self.history: list[SensorReading] = []
        self.max_history = 10  # Circular buffer size (memory-constrained)
        self.anomaly_count = 0

    def observe(self, reading: SensorReading):
        self.history.append(reading)
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def reason(self, reading: SensorReading, actuators: ActuatorState) -> dict:
        """
        Returns action plan: {actuator_changes, alerts, power_mode}
        """
        actions = {}
        alerts = []

        # ── Temperature control ──
        if reading.temperature > 30:
            if not actuators.fan:
                actions["fan"] = True
                alerts.append(f"🌡️ High temp {reading.temperature}°C → fan ON")
        elif reading.temperature < 15:
            if not actuators.heater:
                actions["heater"] = True
                alerts.append(f"🥶 Low temp {reading.temperature}°C → heater ON")
        else:
            if actuators.fan:
                actions["fan"] = False
            if actuators.heater:
                actions["heater"] = False

        # ── Soil moisture ──
        if reading.soil_moisture < 25:
            if not actuators.valve:
                actions["valve"] = True
                alerts.append(f"💧 Dry soil {reading.soil_moisture}% → valve OPEN")
        elif reading.soil_moisture > 70:
            if actuators.valve:
                actions["valve"] = False
                alerts.append(f"🌊 Soil saturated {reading.soil_moisture}% → valve CLOSED")
        elif reading.soil_moisture > 40:
            if actuators.valve:
                actions["valve"] = False

        # ── Light ──
        if reading.light < 50 and reading.temperature < 20:
            if not actuators.light_on:
                actions["light_on"] = True
        elif reading.light > 200:
            if actuators.light_on:
                actions["light_on"] = False

        # ── Anomaly detection (simple statistical) ──
        if len(self.history) >= 3:
            temps = [h.temperature for h in self.history[-5:]]
            avg = sum(temps) / len(temps)
            if abs(reading.temperature - avg) > 5:
                self.anomaly_count += 1
                alerts.append(f"⚠️ Temp anomaly: {reading.temperature}°C (avg {avg:.1f}°C) [{self.anomaly_count}]")
            else:
                self.anomaly_count = max(0, self.anomaly_count - 1)

        # ── Power management ──
        power_mode = PowerMode.ACTIVE
        if reading.battery < 20:
            power_mode = PowerMode.SLEEP
            alerts.append(f"🔋 Low battery {reading.battery}% → SLEEP mode")
        elif reading.battery < 40:
            power_mode = PowerMode.IDLE

        # ── Critical alerts ──
        if reading.battery < 10:
            alerts.append("🚨 CRITICAL: Battery near death!")
        if reading.temperature > 40:
            alerts.append("🚨 CRITICAL: Overheating!")

        return {
            "actions": actions,
            "alerts": alerts,
            "power_mode": power_mode,
        }

# ─── Memory (EEPROM-like) ──────────────────────────────────────────

class EdgeMemory:
    """Simulates persistent storage on embedded device (like EEPROM)."""
    def __init__(self, capacity: int = 256):
        self.capacity = capacity  # bytes (simulated)
        self.store: dict[str, str] = {}
        self._used = 0

    def write(self, key: str, value: str) -> bool:
        entry_size = len(key) + len(value) + 2
        if self._used + entry_size > self.capacity:
            # Evict oldest
            if self.store:
                oldest = next(iter(self.store))
                evicted_size = len(oldest) + len(self.store[oldest]) + 2
                del self.store[oldest]
                self._used -= evicted_size
            else:
                return False
        self.store[key] = value
        self._used += entry_size
        return True

    def read(self, key: str) -> Optional[str]:
        return self.store.get(key)

    def dump(self) -> dict:
        return dict(self.store)

# ─── Agent Loop ─────────────────────────────────────────────────────

class EdgeAgent:
    """
    The main agent loop: Sense → Think → Act → Remember
    Runs in a single thread, like on a microcontroller.
    """
    def __init__(self, verbose: bool = False):
        self.sensors = Sensors()
        self.actuators = ActuatorState()
        self.reasoner = EdgeReasoner()
        self.memory = EdgeMemory(capacity=512)
        self.verbose = verbose
        self.tick = 0
        self.log: list[str] = []

    def _apply_actions(self, actions: dict):
        for attr, value in actions.items():
            if hasattr(self.actuators, attr):
                setattr(self.actuators, attr, value)

    def run_tick(self) -> str:
        self.tick += 1
        lines = [f"\n{'═'*50}", f"  TICK {self.tick}", f"{'═'*50}"]

        # 1. SENSE
        reading = self.sensors.read()
        self.reasoner.observe(reading)

        lines.append(f"\n📡 Sensors:")
        lines.append(f"   Temp: {reading.temperature}°C | Humidity: {reading.humidity}%")
        lines.append(f"   Soil: {reading.soil_moisture}% | Light: {reading.light} lux")
        lines.append(f"   🔋 Battery: {reading.battery}%")

        # 2. THINK
        plan = self.reasoner.reason(reading, self.actuators)

        # 3. ACT
        self._apply_actions(plan["actions"])

        lines.append(f"\n⚡ Actuators:")
        lines.append(f"   Fan: {'ON' if self.actuators.fan else 'off'} | Heater: {'ON' if self.actuators.heater else 'off'}")
        lines.append(f"   Valve: {'OPEN' if self.actuators.valve else 'closed'} | Light: {'ON' if self.actuators.light_on else 'off'}")
        lines.append(f"   Mode: {plan['power_mode'].value}")

        # 4. REMEMBER
        summary = json.dumps({
            "t": reading.temperature,
            "s": reading.soil_moisture,
            "b": reading.battery,
            "a": len(plan["alerts"]),
        })
        self.memory.write(f"tick_{self.tick}", summary)

        # Alerts
        if plan["alerts"]:
            lines.append(f"\n📢 Alerts:")
            for alert in plan["alerts"]:
                lines.append(f"   {alert}")

        output = "\n".join(lines)
        self.log.append(output)
        return output

    def run(self, ticks: int = 10, delay: float = 0.5):
        """Run the agent loop for N ticks."""
        print("🤖 Edge Agent Starting...")
        print(f"   Memory: {self.memory.capacity} bytes | History: {self.reasoner.max_history} slots")
        print(f"   Running {ticks} ticks with {delay}s delay")

        for _ in range(ticks):
            output = self.run_tick()
            if self.verbose:
                print(output)
            else:
                # Compact: show tick number, battery, and alerts only
                reading = self.sensors.read()  # re-read for display (already advanced)
                alerts = []
                plan = self.reasoner.reason(
                    self.reasoner.history[-1] if self.reasoner.history else SensorReading(0,0,0,0,0),
                    self.actuators
                )
                compact = f"  Tick {self.tick:>3} | 🔋 {self.reasoner.history[-1].battery if self.reasoner.history else '?':>5}% | Mode: {plan['power_mode'].value}"
                if plan["alerts"]:
                    compact += f" | {len(plan['alerts'])} alert(s)"
                print(compact)
            time.sleep(delay)

        print(f"\n{'═'*50}")
        print(f"  Agent finished. {self.tick} ticks completed.")
        if self.verbose:
            print(f"\n💾 Memory dump ({self.memory._used}/{self.memory.capacity} bytes):")
            for k, v in self.memory.dump().items():
                print(f"   {k}: {v}")

# ─── CLI ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]
    ticks = 10
    verbose = "--verbose" in args or "-v" in args

    for arg in args:
        if arg.isdigit():
            ticks = int(arg)

    # Seed some environmental drama for an interesting demo
    random.seed(7)  # Produces interesting temp/moisture swings

    agent = EdgeAgent(verbose=verbose)
    agent.run(ticks=ticks, delay=0.3)
