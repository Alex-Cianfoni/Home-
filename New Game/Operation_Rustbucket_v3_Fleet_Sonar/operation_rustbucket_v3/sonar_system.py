"""Persistent fictional sonar simulation: moving targets, track uncertainty, passive
listening, active pings, relative bearings/ranges, aging, classification and saves.
Numbers are deliberately game-balanced, NOT real-world acoustic models.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from math import sin, cos, atan2, radians, degrees, hypot
from typing import Any


@dataclass
class Contact:
    key: str
    label: str
    kind: str
    side: str
    east: float
    north: float
    heading: float
    speed: float
    noise: float
    turn_rate: float
    confidence: float = 0.0
    last_seen: int = -10000
    measured_bearing: float = 0.0
    measured_range: float = 0.0
    last_strength: int = 0


class SonarWorld:
    # Positions in fabricated nautical miles on an abstract exercise chart.
    # Actual positions NEVER appear directly on the player's plot.
    STARTERS = [
        ("S01", "Possible Type 212A", "submarine", "blue", 2.5, 2.1, 203, 3.8, 3.2, +0.10),
        ("B17", "Blue-17 Patrol", "surface", "blue", 3.6, -0.6, 295, 5.1, 7.1, -0.10),
        ("BRV", "Frigate Bravo", "surface", "blue", -1.5, 3.1, 135, 5.0, 8.5, +0.12),
        ("DRN", "Exercise Drone", "drone", "blue", 1.8, -2.3, 48, 2.8, 4.0, -0.20),
        ("ALP", "Destroyer Alpha", "surface", "blue", 5.1, 2.9, 160, 7.3, 10.0, +0.07),
        ("TRW", "Civilian Trawler", "civilian", "neutral", -3.4, -1.2, 38, 3.5, 8.4, -0.06),
        ("NJ", "USS New Jersey", "surface", "friendly", 7.0, 4.3, 235, 5.0, 11.0, -0.07),
    ]

    def __init__(self, game: Any, saved: list[dict] | None = None) -> None:
        self.game = game
        if saved is not None:
            self.contacts = [Contact(**c) for c in saved]
        else:
            self.contacts = [Contact(*args) for args in self.STARTERS]
            self.scan(active=False, elapsed_min=0, bonus=4)

    def serialize(self) -> list[dict]:
        return [asdict(c) for c in self.contacts]

    @staticmethod
    def bearing(east: float, north: float) -> float:
        return (degrees(atan2(east, north)) + 360) % 360

    @staticmethod
    def vector(bearing: float, distance: float) -> tuple[float,float]:
        return sin(radians(bearing)) * distance, cos(radians(bearing)) * distance

    def advance(self, minutes: int, *, ownship_moved: bool) -> None:
        s = self.game.s
        if ownship_moved and not s.bottomed:
            dx, dy = self.vector(s.heading, s.speed * minutes / 60.0)
            s.pos_east += dx
            s.pos_north += dy
        for c in self.contacts:
            c.heading = (c.heading + c.turn_rate * minutes) % 360
            dx, dy = self.vector(c.heading, c.speed * minutes / 60.0)
            c.east += dx
            c.north += dy
            # Patrols turn toward the center of the fictional operating area.
            if abs(c.east) > 10.5 or abs(c.north) > 10.5:
                c.heading = self.bearing(-c.east, -c.north)
            if c.last_seen >= 0 and c.last_seen < s.elapsed - 20:
                c.confidence = max(0.0, c.confidence - 0.08 * minutes)

    def true_distance(self, c: Contact) -> float:
        return hypot(c.east - self.game.s.pos_east, c.north - self.game.s.pos_north)

    def nearest_enemy(self) -> float:
        return min((self.true_distance(c) for c in self.contacts if c.side == "blue"), default=99.0)

    def scan(self, *, active: bool = False, elapsed_min: int = 0, bonus: int = 0) -> list[str]:
        s = self.game.s
        low, high = self.game.thermal_layer()
        layer = low <= s.depth <= high
        rng = self.game.rng
        updates = []
        for c in self.contacts:
            real_range = self.true_distance(c)
            # Coarse fictional ranges tuned for a readable strategy game.
            base = (2.7 + self.game.sub.sonar * 0.29 + (c.noise - 6) * 0.22
                    - s.speed * .10 - (0.35 if layer else 0))
            radius = (base + 2.6) if active else base
            radius += 0.05 * bonus
            if c.kind == "submarine" and not active:
                radius -= .75
            if c.side == "friendly":
                radius += .3
            visible = real_range <= radius and (active or rng.random() > .06)
            if visible:
                was_lost = c.last_seen < s.elapsed - 28
                c.last_seen = s.elapsed
                gain = (36 if active else 13 + bonus) * (0.7 if c.kind == "submarine" else 1.0)
                c.confidence = min(100.0, c.confidence + gain)
                error_bearing = max(1.2, (100 - c.confidence) * .20)
                error_range = max(.05, (100 - c.confidence) / 100. * .43)
                rel_east, rel_north = c.east - s.pos_east, c.north - s.pos_north
                c.measured_bearing = (self.bearing(rel_east, rel_north) + rng.uniform(-error_bearing, error_bearing)) % 360
                c.measured_range = max(.1, real_range + rng.uniform(-error_range, error_range))
                c.last_strength = max(1, int(100 * (1 - real_range / max(1, radius))))
                if was_lost or c.confidence <= gain:
                    updates.append(f"SONAR: New {c.key} track at bearing {c.measured_bearing:03.0f}, estimated {c.measured_range:.1f} nm.")
            else:
                c.confidence = max(0.0, c.confidence - (6 if c.last_seen < s.elapsed - 15 else 2))
        return updates

    def observed(self) -> list[Contact]:
        # Tracks expire if stale; old bearings are not trusted indefinitely.
        return sorted((c for c in self.contacts
                       if c.confidence >= 14 and 0 <= self.game.s.elapsed - c.last_seen <= 32),
                      key=lambda c: c.measured_range)

    def display_label(self, c: Contact) -> str:
        if c.confidence < 50:
            return "UNCLASSIFIED"
        if c.confidence < 75:
            return {"submarine": "SUBMERGED CONTACT", "surface": "SURFACE CONTACT", "drone": "SMALL CONTACT", "civilian": "CIVILIAN CONTACT"}.get(c.kind,"CONTACT")
        return c.label

    def report(self) -> str:
        tracklines = [
            f"PASSIVE SONAR TRACKS — {self.game.sub.name}",
            f"Mode: {'ACTIVE ECHO / PING' if self.game.s.sonar_mode == 'active' else 'PASSIVE LISTENING'}",
            f"Sensor rating: {self.game.sub.sonar}/10 | Heading: {self.game.s.heading:03d}° true",
            "Ranges are imprecise game estimates, not real sonar data.",
        ]
        tracks = self.observed()
        if not tracks:
            tracklines.append("No usable tracks. Try LISTEN for analysis or ACTIVE PING (reveals our presence).")
        for c in tracks:
            age = self.game.s.elapsed - c.last_seen
            tracklines.append(f"  {c.key}  {c.measured_bearing:03.0f}°  ~{c.measured_range:.1f} nm  "
                              f"confidence {c.confidence:.0f}%  {self.display_label(c)}  "
                              f"{'STALE '+str(age)+'m' if age > 8 else 'CURRENT'}")
        tracklines.append(f"Blue Force assessment: {self.game.s.detection.upper()}.")
        return "\n".join(tracklines)
