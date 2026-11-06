#!/usr/bin/env python3
"""Operation Rustbucket - an interactive, fictional submarine command game.

Runs with Python 3.9+ standard library only. Launches a Tkinter desktop game
when a graphical display is available; pass --console for a terminal version.
All vessels, navigation, detection and incidents are fictional game mechanics.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple
from captains_orders import OrderPlan, parse_offline
from ai_captain import AICaptain, AIError
from submarine_catalog import SUBMARINES, DEFAULT_SUBMARINE, Submarine, groups, select_submarine
from sonar_system import SonarWorld
from fleet_menu import choose_submarine

VERSION = "3.0"
START_TIME = datetime(2026, 11, 3, 2, 15)
DEADLINE_MINUTES = 376  # 08:31 local, same day
DEFAULT_SAVE = Path.home() / "operation_rustbucket_save.json"

# Names evoke the 273-vessel alternate-history alliance; no actual ships are
# being commanded by this simulation.
FLEET_GROUPS = {
    "Carrier Command": ["USS Midway", "USS Lexington", "USS Intrepid", "USS Hornet", "USS Yorktown", "Kiev"],
    "Heavy Surface Command": ["USS New Jersey", "USS Iowa", "USS Missouri", "USS Wisconsin", "USS Texas", "HMS Belfast", "Mikhail Kutuzov"],
    "Submarine Command": ["USS Razorback", "USS Becuna", "USS Blueback", "USS Nautilus", "HMAS Onslow", "U-2540", "Le Redoutable"],
    "Escort Command": ["USS Edson", "USS Turner Joy", "Molders", "Bespokoynyy", "HMAS Vampire", "USS Aries"],
    "Support Command": ["LST-325", "USS Hazard", "USS Lucid", "SS Jeremiah O'Brien", "USCGC Mackinaw"],
}


@dataclass
class GameState:
    turn: int = 0
    elapsed: int = 0
    phase: str = "infiltration"  # infiltration, extraction, success, failure
    inbound_progress: float = 0.0
    escape_progress: float = 0.0
    battery: float = 94.0
    hull: int = 100
    crew_morale: int = 82
    depth: int = 90
    speed: float = 3.0
    heading: int = 90  # schematic exercise heading; not a geographical solver
    silent_running: bool = False
    bottomed: bool = False
    route: str = "original"
    sonar_confidence: int = 45
    suspicion: float = 0.0
    detection: str = "undetected"  # undetected / suspected / confirmed
    detected_before_marker: bool = False
    marker_sent: bool = False
    vintage_radio: bool = False
    torpedoes: int = 10
    report_interval: int = 0
    next_report: int = 0
    milestone_ids: List[str] = field(default_factory=list)
    previous_event: str = ""
    score: int = 0
    difficulty: str = "normal"
    submarine_id: str = DEFAULT_SUBMARINE
    pos_east: float = 0.0
    pos_north: float = 0.0
    sonar_mode: str = "passive"
    mission_note: str = "Enter Port Meridian, place the exercise marker, and extract."


@dataclass(frozen=True)
class Choice:
    key: str
    title: str
    summary: str
    command: str


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def clock(minute: int) -> str:
    return (START_TIME + timedelta(minutes=minute)).strftime("%H:%M")


class Game:
    def __init__(self, seed: Optional[int] = None, difficulty: str = "normal", submarine: str = DEFAULT_SUBMARINE) -> None:
        self.seed = seed if seed is not None else random.randrange(1, 10**9)
        self.rng = random.Random(self.seed)
        self.sub = select_submarine(submarine)
        self.state = GameState(difficulty=difficulty, submarine_id=self.sub.id,
                               battery=self.sub.battery, torpedoes=self.sub.torpedoes,
                               sonar_confidence=30 + self.sub.sonar * 2)
        self.sonar_world = SonarWorld(self)
        self.log = [self.opening()]

    def opening(self) -> str:
        return (
            "OPERATION RUSTBUCKET / PORT MERIDIAN / 02:15\n"
            "----------------------------------------------\n"
            f"You command {self.sub.name}, a fantastically restored or modernized "
            "submarine in a Down Periscope-style exercise.\n\n"
            "The 273-vessel Museum Alliance is conducting a joint wargame against "
            "a modern naval task force. Infiltrate a fictional defended harbor, "
            "transmit an authenticated exercise marker, then escape before 08:31.\n\n"
            'XO: "A whole modern fleet looking for one museum submarine, Captain."\n'
            'Chief Engineer: "If they can find our spare parts, they can find us."\n'
            'Sonar: "Passive sonar is online. Tracks will update as ships move."\n\n'
            "Choose A, B, or C, or type a complete sentence as your order. Optional AI mode understands longer conversations; type HELP."
        )

    @property
    def s(self) -> GameState:
        return self.state

    def remaining(self) -> int:
        return max(0, DEADLINE_MINUTES - self.s.elapsed)

    def water_depth(self) -> int:
        """Fictional changing seabed, deliberately not a real navigation model."""
        s = self.s
        if s.phase == "infiltration":
            base = 230 - 0.42 * s.inbound_progress
        else:
            base = 216 - 0.60 * s.escape_progress
            if s.route == "alternate":
                base += 26
        return int(base)

    def thermal_layer(self) -> Tuple[int, int]:
        if self.s.phase == "infiltration":
            return 120, 145
        return 115, 140

    def status_text(self) -> str:
        s = self.s
        phase = "INFILTRATION" if s.phase == "infiltration" else "EXTRACTION" if s.phase == "extraction" else s.phase.upper()
        progress = s.inbound_progress if s.phase == "infiltration" else s.escape_progress
        bottom = self.water_depth()
        clearance = max(0, bottom - s.depth - 10) if not s.bottomed else 0
        return (
            f"SUBMARINE: {self.sub.name} | {self.sub.country} | game dive limit {self.sub.depth} ft\n"
            f"TURN {s.turn} | {clock(s.elapsed)} | {phase}\n"
            f"Progress: {progress:.0f}% | Deadline: {clock(DEADLINE_MINUTES)} "
            f"| Time left: {self.remaining()} min\n"
            f"Hull: {s.hull}% | Battery: {s.battery:.0f}% | Depth: {s.depth} ft "
            f"| Bottom: {bottom} ft | Keel clearance: ~{clearance} ft\n"
            f"Speed: {s.speed:g} kt | Heading: {s.heading:03d} true | Silent: {'YES' if s.silent_running else 'NO'} "
            f"| Bottomed: {'YES' if s.bottomed else 'NO'}\n"
            f"Stealth: {s.detection.upper()} | Sonar: {s.sonar_mode.upper()} | Sensor confidence: {s.sonar_confidence}% "
            f"| Crew morale: {s.crew_morale}%\n"
            f"Exercise torpedoes: {s.torpedoes} | Route: {s.route} "
            f"| 30-minute report: {s.report_interval or 'OFF'}\n"
            f"Objective marker: {'SENT' if s.marker_sent else 'PENDING'}"
        )

    def environmental_report(self) -> str:
        low, high = self.thermal_layer()
        floor = self.water_depth()
        keel = floor - self.s.depth - 10
        layer = "inside" if low <= self.s.depth <= high else "above" if self.s.depth < low else "below"
        return (
            f"NAVIGATION / ENVIRONMENT at {clock(self.s.elapsed)}\n"
            f"Depth: {self.s.depth} ft | Estimated bottom: {floor} ft\n"
            f"Estimated keel clearance: {max(keel, 0)} ft\n"
            f"Thermal gradient: {low}-{high} ft | Razorback: {layer} layer\n"
            "Note: The thermal layer alters acoustic conditions, but does not "
            "guarantee the submarine can hide. All depths are fictional."
        )

    def sonar_report(self) -> str:
        return self.sonar_world.report()

    def fleet_report(self) -> str:
        lines = ["MUSEUM ALLIANCE / FLEET BRIEF", "273 upgraded historical vessels are available in this scenario."]
        for group, ships in FLEET_GROUPS.items():
            lines.append(f"{group}: " + ", ".join(ships))
        lines.append("USS Becuna is in a separate exercise sector. USS Midway coordinates fleet support.")
        return "\n".join(lines)

    def help_text(self) -> str:
        return (
            "CAPTAIN'S ORDERS\n"
            "Select A/B/C, or type one of these commands:\n"
            "  silent       - continue at 2 knots with quiet running\n"
            "  advance      - continue at 3 knots\n"
            "  speed 4      - set speed within the chosen submarine limit\n"
            "  depth 130    - request a depth change (safety checked)\n"
            "  thermal      - request to enter thermal layer, if safe\n"
            "  bottom       - settle in a surveyed exercise area, if permitted\n"
            "  depart       - depart from seabed after safety checks\n"
            "  wait         - hold position while events continue\n"
            "  analyze      - hold and refine passive contact identification\n"
            "  radio        - contact exercise control (may affect secrecy)\n"
            "  alternate    - request approved alternate extraction route\n"
            "  transmit 1944 - send authorized marker with vintage Morse-style ID\n"
            "  transmit     - send standard authorized marker\n"
            "  report 30    - set 30-minute depth reports (free standing order)\n"
            "  report off   - disable scheduled depth reports\n"
            "  sonar / depth report / status / fleet / map - inspect for free\n"
            "  listen       - spend time listening to actual moving tracks\n"
            "  ping / active sonar - transmit an active ping; increases detection risk\n"
            "  subs        - list available playable submarine classes\n"
            "  save / load / quit (console mode; GUI has buttons)\n"
            "Combine full sentences, e.g. 'Dive into the thermal layer, check the seabed every 30 minutes, and maintain two knots.'\n"
            "  heading 120   - simulated course change (not physical navigation)\n"
            "  ask XO... / inspect engine / periscope - crew & equipment interactions\n"
            f"Current boat: {self.sub.name}; game speed limit {self.sub.speed:g} kt; game dive limit {self.sub.depth} ft.\n"
            "OFFLINE MODE recognizes many phrases, but is not ChatGPT. Enable OPTIONAL AI in the desktop app "
            "or use --ai in console with OPENAI_API_KEY for open-ended orders and narrative. "
            "AI requires internet and separately billed API access. Everything is fictional."

        )

    def map_text(self) -> str:
        s = self.s
        p = s.inbound_progress if s.phase == "infiltration" else s.escape_progress
        bars = int(clamp(p, 0, 100) / 5)
        return (
            f"{s.phase.upper()} CHART / PORT MERIDIAN (fictional)\n"
            f"START [{'#' * bars}{'.' * (20-bars)}] {p:.0f}% TARGET\n"
            f"Route: {s.route} | No real geographic coordinates\n"
            "Sectors: OUTER APPROACHES > HARBOR SCREEN > OBJECTIVE > EXTRACTION\n"
            "Friendly sectors: USS Becuna (independent), USS Midway support, USS New Jersey offshore."
        )

    def choices(self) -> List[Choice]:
        s = self.s
        if s.phase in {"success", "failure"}:
            return []
        if s.bottomed:
            return [
                Choice("A", "Remain on seabed", "Hold quietly; the clock and battery keep moving.", "wait"),
                Choice("B", "Depart seabed", "Complete safety checks and resume the withdrawal.", "depart"),
                Choice("C", "Listen for contacts", "Analyze sonar before leaving the bottom.", "analyze"),
            ]
        if self.water_depth() - s.depth - 10 < 32:
            return [
                Choice("A", "Shallower operating depth", "Recover bottom clearance before proceeding.", "depth 90"),
                Choice("B", "Request alternate passage", "Switch to the cleared deeper-water route.", "alternate"),
                Choice("C", "Hold and reassess", "Stop forward progress to review conditions.", "wait"),
            ]
        if s.phase == "infiltration":
            if s.inbound_progress >= 95:
                return [
                    Choice("A", "Transmit 1944-style marker", "Use an authorized exercise marker with a vintage identification message.", "transmit 1944"),
                    Choice("B", "Transmit standard marker", "Complete the objective with normal exercise identification.", "transmit"),
                    Choice("C", "Hold and analyze sonar", "Confirm the nearby contacts before sending.", "analyze"),
                ]
            if s.inbound_progress < 27:
                return [
                    Choice("A", "Silent running", "Two knots; minimize unnecessary machinery noise.", "silent"),
                    Choice("B", "Hold and listen", "Gather passive acoustic information at the cost of time.", "analyze"),
                    Choice("C", "Proceed normally", "Three knots with standard propulsion.", "advance"),
                ]
            return [
                Choice("A", "Continue silent approach", "Maintain two knots toward the objective.", "silent"),
                Choice("B", "Identify contacts", "Stop to improve passive sonar classification.", "analyze"),
                Choice("C", "Request exercise update", "Use an authorized channel to clarify restrictions.", "radio"),
            ]
        if s.escape_progress > 72:
            return [
                Choice("A", "Complete silent withdrawal", "Stay on the assigned route and aim for extraction.", "silent"),
                Choice("B", "Hold and monitor", "Watch contacts before making the final leg.", "analyze"),
                Choice("C", "Proceed at three knots", "Faster progress but a larger acoustic signature.", "advance"),
            ]
        return [
            Choice("A", "Silent withdrawal", "Two knots through the authorized exit sector.", "silent"),
            Choice("B", "Hold for passive sonar", "Study incoming contacts without moving.", "analyze"),
            Choice("C", "Alternate extraction route", "Use a cleared route with better seabed clearance.", "alternate"),
        ]

    def _milestones(self, old_phase: str, old_progress: float) -> List[str]:
        s = self.s
        arr = []
        if old_phase == "infiltration" and s.phase == "infiltration":
            milestones = [
                (15, "i15", 'SONAR: "Modern electric contact, bearing zero-five-eight. No confirmed pursuit."'),
                (30, "i30", 'SONAR: "New repeating mechanical noise. Could be an underwater exercise drone."'),
                (48, "i48", 'XO: "Three surface contacts: Alpha, Bravo, and Charlie. We are entering the harbor screen."'),
                (64, "i64", 'RADIO: "Midway has started its separate fleet aviation exercise. Some Blue Force aircraft are busy."'),
                (84, "i84", 'RADIO: "Port Meridian electronic identification challenge is active. Exercise safety areas remain in force."'),
                (95, "i95", 'NAVIGATOR: "We are at the final scoring marker. Your authorized transmission can complete infiltration."'),
            ]
            prog = s.inbound_progress
        elif old_phase == "extraction" and s.phase == "extraction":
            milestones = [
                (18, "e18", 'SONAR: "Blue Force has expanded the exercise search. Still no reliable position report on us."'),
                (40, "e40", 'RADIO: "The opposing Type 212A has paused its search due to a minor exercise-equipment malfunction."'),
                (62, "e62", 'NAVIGATOR: "Seabed is shoaling along this approach; under-keel clearance deserves attention."'),
                (78, "e78", 'RADIO: "USS New Jersey is operating in an adjacent friendly exercise sector."'),
                (95, "e95", 'XO: "Captain, the extraction checkpoint is almost ours."'),
            ]
            prog = s.escape_progress
        else:
            return []
        for threshold, ident, line in milestones:
            if old_progress < threshold <= prog and ident not in s.milestone_ids:
                s.milestone_ids.append(ident)
                arr.append(line)
        return arr

    def _ambient(self) -> str:
        s = self.s
        if s.phase == "infiltration":
            if s.inbound_progress < 35:
                options = [
                    'SONAR: "Faint electric motor on the edge of the display. Classification remains uncertain."',
                    'XO: "The modern navy has better hardware. We can still make them work for every contact."',
                    'CHIEF ENGINEER: "Coffee maker secured. For the moment, discipline has prevailed."',
                ]
            elif s.inbound_progress < 80:
                options = [
                    'SONAR: "A distant exercise ping. No confirmed identification of Razorback."',
                    'RADIO: "Becuna reports no new restricted-sector notices."',
                    'CHIEF ENGINEER: "There are fewer moving parts in a museum. Mostly because we replaced them."',
                ]
            else:
                options = [
                    "XO: \"We\'re nearly at the objective, Captain. Their identification window is still a complication.\"",
                    'RADIO: "Harbor-control safety notice unchanged. Keep to cleared exercise water."',
                    'SONAR: "Blue-17 patrol still active somewhere ahead. No confirmed tracking."',
                ]
        else:
            options = [
                'RADIO: "Midway confirms the marker was accepted. Extract without being tagged."',
                'CHIEF ENGINEER: "If they find us, Captain, tell them we are an educational exhibit."',
                'SONAR: "Intermittent search transmissions. Classification uncertain."',
                "XO: \"They're searching for the boat that sent the 1944 greeting. Excellent.\"",
            ]
        return self.rng.choice(options)

    def _detection_check(self, noise_modifier: float, moved: bool) -> str:
        s = self.s
        if s.phase not in {"infiltration", "extraction"}:
            return ""
        base = 7 if s.phase == "infiltration" and s.inbound_progress < 35 else 13
        if s.phase == "infiltration" and s.inbound_progress >= 75:
            base = 17
        if s.phase == "extraction":
            base = 17
        if s.difficulty == "easy":
            base -= 5
        elif s.difficulty == "hard":
            base += 7
        extra = (s.speed - 2) * 3.4 if moved else -3
        low, high = self.thermal_layer()
        layer_effect = -2 if low <= s.depth <= high else 0
        near_enemy = self.sonar_world.nearest_enemy()
        proximity = 10 if near_enemy < 1.1 else 5 if near_enemy < 2.3 else -5 if near_enemy > 5 else 0
        vessel_signature = (self.sub.signature - 5) * 1.1
        chance = clamp(base + extra + noise_modifier + proximity + vessel_signature
                       + s.suspicion / 14 + layer_effect - (5 if s.silent_running else 0)
                       - (5 if s.bottomed else 0), 1.5, 75)
        roll = self.rng.random() * 100
        if roll < chance:
            s.suspicion = clamp(s.suspicion + 17 + self.rng.randint(0, 7), 0, 100)
            if s.detection == "undetected":
                s.detection = "suspected"
                return 'BLUE FORCE: "Unidentified underwater noise reported. No positive Razorback contact."'
            elif s.detection == "suspected":
                s.detection = "confirmed"
                if not s.marker_sent:
                    s.detected_before_marker = True
                s.crew_morale = max(20, s.crew_morale - 9)
                return f'EXERCISE CONTROL: "Blue Force has registered a confirmed detection of {self.sub.name}."'
            else:
                if self.rng.random() < .27:
                    damage = self.rng.randint(4, 14)
                    s.hull = max(0, s.hull - damage)
                    return f'EXERCISE CONTROL: "Simulated torpedo tag! Hull assessment reduced by {damage} points."'
                return 'BLUE FORCE: "Target tracking continues. No exercise-weapon hit scored this turn."'
        else:
            s.suspicion = max(0.0, s.suspicion - 4)
            if s.detection == "suspected" and s.suspicion < 12:
                s.detection = "undetected"
                return 'SONAR: "That suspicious contact report has been dropped. No confirmed detection."'
        return 'SONAR: "No confirmed new detection report."'

    def _score(self) -> int:
        s = self.s
        infiltration = 30 if not s.detected_before_marker else 14
        marker = 20 if s.marker_sent else 0
        extraction = 25 if s.detection != "confirmed" else 10
        safety = round(15 * s.hull / 100)
        resource = 10 if s.battery >= 12 and s.elapsed <= DEADLINE_MINUTES else 5 if s.elapsed <= DEADLINE_MINUTES else 0
        return infiltration + marker + extraction + safety + resource

    def _conclusion(self) -> str:
        s = self.s
        s.score = self._score()
        if s.phase == "success":
            return (
                "\n*** EXTRACTION BOUNDARY CROSSED ***\n"
                'NAVIGATOR: "Captain, we are across the exercise extraction line!"\n'
                'RADIO: "Meridian Control confirms objective marker, extraction and final scoring."\n'
                'XO: "We just infiltrated a defended harbor in a museum submarine."\n'
                'CHIEF ENGINEER: "Splendid. Does the 273-ship alliance have an espresso budget?"\n'
                f"MISSION COMPLETE: {s.score}/100 points aboard {self.sub.name}. "
                f"Confirmed detection: {'YES' if s.detection == 'confirmed' else 'NO'}. "
                f"Battery: {s.battery:.0f}%. Hull: {s.hull}%.\n"
                "The 1944-style stunt is remembered by Blue Force's baffled communications officer."
                if s.vintage_radio else
                "\n*** EXTRACTION BOUNDARY CROSSED ***\n"
                f"MISSION COMPLETE: {s.score}/100 points. {self.sub.name} returns to fleet command.\n"
                'XO: "Outstanding work, Captain." CHIEF ENGINEER: "Coffee first, debrief second."'
            )
        return (
            "\n*** MISSION ENDED ***\n"
            f"Reason: {s.mission_note}\n"
            'XO: "The mission is over, but Razorback and her crew have plenty of stories left."\n'
            "Use NEW GAME to try a different set of orders."
        )

    def _finish_if_needed(self) -> str:
        s = self.s
        if s.hull <= 0:
            s.phase = "failure"
            s.mission_note = "Simulated damage forced exercise termination."
        elif s.battery <= 3:
            s.phase = "failure"
            s.mission_note = "Critical electrical reserve: the safety controller terminated the exercise."
        elif s.elapsed > DEADLINE_MINUTES:
            s.phase = "failure"
            s.mission_note = "The 08:31 extraction deadline passed."
        elif s.phase == "extraction" and s.escape_progress >= 100:
            s.phase = "success"
        elif s.elapsed >= DEADLINE_MINUTES:
            s.phase = "failure"
            s.mission_note = "The 08:31 extraction deadline passed."
        return self._conclusion() if s.phase in {"success", "failure"} else ""

    def _action_with_clock(self, kind: str, arg: Optional[float] = None) -> str:
        s = self.s
        start = s.elapsed
        old_phase = s.phase
        old_progress = s.inbound_progress if s.phase == "infiltration" else s.escape_progress
        noise = 0.0
        moved = False
        movement_scale = 1.0
        lines: List[str] = []

        if kind == "cruise":
            if s.bottomed:
                return "XO: Razorback is resting on the bottom. Order DEPART before proceeding."
            elapsed = self.rng.randint(18, 23)
            moved = s.speed > 0
            lines.append(f'HELM: "Maintaining present course {s.heading:03d} true, {s.speed:g} knots. {"Silent" if s.silent_running else "Normal"} running."')
        elif kind == "silent":
            if s.bottomed:
                return "XO: Our boat is resting on the bottom. We must depart before resuming movement."
            s.speed, s.silent_running = 2.0, True
            elapsed = self.rng.randint(18, 23)
            moved = True
            lines.append('CAPTAIN: "Two knots. Silent running. Stay on our authorized route."')
            lines.append('HELM: "Aye, Captain. Two knots, minimum unnecessary machinery."')
        elif kind == "advance":
            if s.bottomed:
                return "XO: We cannot advance while bottomed. Order DEPART first."
            s.speed, s.silent_running = 3.0, False
            elapsed = self.rng.randint(17, 22)
            moved = True
            lines.append('CAPTAIN: "Maintain the exercise course. Three knots."')
        elif kind == "speed":
            if s.bottomed:
                return "XO: We are bottomed. Depart before setting underway speed."
            assert arg is not None
            if not 0 <= arg <= self.sub.speed:
                return f"HELM: This submarine has an exercise speed limit of {self.sub.speed:g} knots."
            s.speed = float(arg)
            s.silent_running = s.speed <= 2
            elapsed = self.rng.randint(16, 22)
            moved = s.speed > 0
            noise = 5 if s.speed >= 5 else 0
            lines.append(f'HELM: "Speed set to {s.speed:g} knots. {"Silent" if s.silent_running else "Standard"} running."')
        elif kind == "talk":
            elapsed = 2
            s.speed = s.speed  # conversations do not alter ordered motion
            lines.append('XO: "Aye, Captain. Crew briefing acknowledged. Our orders and mission remain in effect."')
            lines.append('CHIEF ENGINEER: "The coffee situation remains an ongoing tactical emergency."')
        elif kind == "inspect":
            elapsed = 6
            s.sonar_confidence = min(100, s.sonar_confidence + 3)
            lines.append('XO: "Inspection completed within the scope of the exercise. No immediate safety fault indicated."')
            lines.append('NAVIGATOR: "Current approved navigation limits are unchanged."')
        elif kind == "repair":
            elapsed = self.rng.randint(12, 18)
            s.speed = 0
            restored = min(4, 100 - s.hull) if s.hull > 0 else 0
            s.hull += restored
            lines.append(f'CHIEF ENGINEER: "Diagnostics and authorized minor maintenance complete. Restored {restored}% simulated hull condition."')
        elif kind == "periscope":
            if s.depth > 60:
                return "XO: Periscope inspection is not authorized at our present depth. Request a safety-cleared shallow depth first."
            elapsed = 8
            noise = 3
            s.sonar_confidence = min(100, s.sonar_confidence + 4)
            lines.append('OFFICER OF THE DECK: "Brief fictional periscope observation completed; no visual confirmation of Razorback by Blue Force."')
        elif kind == "ping":
            elapsed = 5
            noise = 26
            s.sonar_mode = "active"
            s.suspicion = clamp(s.suspicion + 24, 0, 100)
            lines.append('SONAR CHIEF: "ACTIVE PING TRANSMITTED. Incoming echoes are being classified."')
            lines.append('XO: "That improved our information, Captain, but Blue Force may have heard us."')
        elif kind == "analyze":
            s.sonar_mode = "passive"
            elapsed = self.rng.randint(12, 16)
            s.speed = 0
            s.sonar_confidence = min(100, s.sonar_confidence + 14)
            lines.append('SONAR: "Holding station to study contacts. Bearings and estimated ranges are updating."')
            lines.append('CHIEF ENGINEER: "Good, a stationary mission. My specialty."')
        elif kind == "wait":
            elapsed = self.rng.randint(16, 22)
            s.speed = 0
            s.sonar_confidence = min(100, s.sonar_confidence + 5)
            lines.append('XO: "Holding in the cleared exercise sector. The clock is still running."')
        elif kind == "bottom":
            if s.bottomed:
                return "HELM: Razorback is already settled on the exercise seabed."
            if self.water_depth() < 160 or s.phase == "infiltration" and s.inbound_progress >= 90:
                return "NAVIGATOR: Bottoming is not approved at this location. The seabed or mission area is unsuitable."
            s.bottomed = True
            s.speed = 0
            s.silent_running = True
            s.depth = self.water_depth() - 12
            elapsed = 12
            lines.append('NAVIGATOR: "Exercise safety approves the surveyed sandy patch. Clear of restrictions."')
            lines.append('HELM: "Simulated gentle seabed contact completed. Propulsion secured."')
            lines.append("CHIEF ENGINEER: \"The world's most expensive lawn ornament, reporting for duty.\"")
        elif kind == "depart":
            if not s.bottomed:
                return "NAVIGATOR: Razorback is not bottomed. No departure checks are required."
            s.bottomed = False
            s.speed, s.silent_running = 2.0, True
            s.depth = min(90, self.water_depth() - 60)
            elapsed = 17
            moved = True
            movement_scale = .45
            lines.append('XO: "Hull and navigation checks complete. Clear to depart surveyed seabed."')
            lines.append('CHIEF ENGINEER: "Tell the barnacles their lease has expired."')
        elif kind == "depth":
            assert arg is not None
            if s.bottomed:
                return "NAVIGATOR: Depart the bottom before changing operating depth."
            goal = round(arg)
            max_authorized = min(self.water_depth() - 40, self.sub.depth)
            if goal < 25 or goal > max_authorized:
                return f"NAVIGATOR: Depth {goal} ft is not cleared. Allowed now: 25-{max_authorized} ft. No order executed."
            s.depth = goal
            elapsed = 11
            moved = s.speed > 0
            movement_scale = .55
            lines.append(f'HELM: "Depth {s.depth} feet, steady. Seabed clearance verified."')
            low, high = self.thermal_layer()
            if low <= goal <= high:
                lines.append('SONAR: "We are inside the temperature gradient; acoustic results may change."')
        elif kind == "alternate":
            if s.bottomed:
                return "NAVIGATOR: Depart the bottom before changing the withdrawal route."
            s.route = "alternate"
            elapsed = 14
            moved = s.speed > 0
            movement_scale = .32
            lines.append('RADIO: "Alternate extraction sector authorized by exercise control."')
            lines.append('NAVIGATOR: "Route updated. Better forecast bottom clearance but different transit time."')
        elif kind == "radio":
            elapsed = 9
            noise = 7
            lines.append('RADIO: "Secure exercise-controller status requested. Safe water remains available."')
            lines.append('XO: "Exercise safety confirmed. We may have surrendered a little stealth score."')
        elif kind == "transmit":
            if s.phase != "infiltration":
                return "RADIO: The objective marker has already been transmitted. Continue extraction."
            if s.inbound_progress < 95:
                return f"NAVIGATOR: We are only at {s.inbound_progress:.0f}% of the approach. The exercise marker is not in range."
            elapsed = 8
            noise = 11 if arg == 1944 else 4
            s.marker_sent = True
            s.vintage_radio = arg == 1944
            if s.vintage_radio:
                lines.extend([
                    'CAPTAIN: "Hold the last second. Put the old 1944-style ID in our authorized exercise packet."',
                    f'RADIO: "... .-.-. ... {self.sub.name} / HISTORICAL VESSEL ID / MISSION ACCOMPLISHED"',
                    'BLUE FORCE COMMS: "Admiral, our harbor just received a message from 1944."',
                    'BLUE ADMIRAL: "I can read the DATE, Lieutenant! Find the submarine!"',
                ])
            else:
                lines.append('RADIO: "Standard authenticated exercise marker accepted by Port Meridian Control."')
            s.phase = "extraction"
            s.escape_progress = 0
            s.suspicion = clamp(s.suspicion + (14 if s.vintage_radio else 5), 0, 100)
            lines.append('EXERCISE CONTROL: "Objective COMPLETE. Exit the authorized extraction boundary before the deadline."')
        elif kind == "fire":
            if s.torpedoes == 0:
                return "WEAPONS: No simulated torpedoes remain."
            valid = [c for c in self.sonar_world.observed()
                     if c.side == "blue" and c.confidence >= 65 and c.measured_range <= 3.5]
            if not valid:
                return ("XO: No confidently classified nearby Blue Force sonar track. "
                        "Simulated launch denied; listen or use active sonar to identify a target.")
            target = min(valid, key=lambda c: c.measured_range)
            s.torpedoes -= 1
            elapsed = 12
            noise = 15
            outcome = "SIMULATED TARGET TAG" if self.rng.random() < min(.85, target.confidence / 120) else "SIMULATED MISS"
            lines.append(f'WEAPONS: "Authorized inert exercise torpedo against track {target.key}; result: {outcome}."')
            lines.append('XO: "Our infiltration mission awards no attack points. They may start searching harder now."')
        else:
            return "I did not recognize that command. Type HELP for supported captain's orders."

        s.turn += 1
        s.elapsed += elapsed
        if kind != "ping":
            s.sonar_mode = "passive"
        self.sonar_world.advance(elapsed, ownship_moved=(moved and s.speed > 0))
        low, high = self.thermal_layer()
        was_move = moved and s.speed > 0
        if moved and kind not in {"transmit"}:
            distance = elapsed * s.speed * .32 * movement_scale
            if s.route == "alternate":
                distance *= .91
            if s.phase == "infiltration":
                s.inbound_progress = min(100, s.inbound_progress + distance)
            elif s.phase == "extraction":
                s.escape_progress = min(100, s.escape_progress + distance)
        consumption = elapsed * (0.08 + 0.018 * (s.speed if was_move else 0) ** 2)
        if s.bottomed:
            consumption *= .70
        s.battery = max(0, s.battery - consumption)
        if kind in {"radio", "transmit", "fire"}:
            s.suspicion = clamp(s.suspicion + noise * .4, 0, 100)
        s.sonar_confidence = min(100, max(20, s.sonar_confidence + (1 if was_move else 0)))
        s.crew_morale = int(clamp(s.crew_morale + (1 if s.inbound_progress >= 95 else 0), 20, 100))
        if not s.bottomed and s.depth > self.water_depth() - 40:
            s.depth = min(90, self.water_depth() - 55)
            lines.append(f'NAVIGATOR: "SAFETY ALERT: seabed is rising. Returning to {s.depth} feet for approved clearance."')
        # Sensor updates are authoritative simulation data. Passive scans only
        # reveal detectable moving vessels; ping improves contact quality at a cost.
        sonar_notes = self.sonar_world.scan(active=(kind == "ping"),
                                            bonus=(14 if kind == "analyze" else 0))
        lines.extend(sonar_notes[:3])
        if kind != "transmit":
            lines.append(self._ambient())
        lines.extend(self._milestones(old_phase, old_progress))
        lines.append(self._detection_check(noise, was_move))
        if s.report_interval:
            while s.elapsed >= s.next_report:
                lines.append("SCHEDULED REPORT: " + self.environmental_report().replace("\n", " | "))
                s.next_report += s.report_interval
        result = self._finish_if_needed()
        if result:
            lines.append(result)
        if s.phase not in {"success", "failure"} and s.phase == "infiltration" and s.inbound_progress >= 95:
            lines.append('XO: "Captain, the scoring marker is ready. Transmit now or take another observation."')
        if s.phase not in {"success", "failure"} and s.phase == "extraction":
            lines.append('XO: "Marker confirmed. Now get this old boat safely to the extraction boundary."')
        lines.append(f"\nTIME {clock(start)} -> {clock(s.elapsed)} | TURN {s.turn} | {self.remaining()} min to deadline")
        lines.append(f"Battery {s.battery:.0f}% | Depth {s.depth} ft | Hull {s.hull}% | Detection {s.detection}")
        text = "\n\n".join(lines)
        self.log.append(text)
        if len(self.log) > 100:
            self.log = self.log[-100:]
        return text

    def _readout(self, name: str) -> str:
        return {
            "sonar": self.sonar_report,
            "environment": self.environmental_report,
            "status": self.status_text,
            "map": self.map_text,
            "fleet": self.fleet_report,
        }[name]()

    def apply_plan(self, plan: OrderPlan, raw: str = "") -> str:
        """Execute one interpreted order; only this function can mutate game state.

        The model, if enabled, selects bounded commands, never writes stats.
        Validate safety and resources before applying standing instructions.
        """
        s = self.s
        if s.phase in {"success", "failure"}:
            return "Mission concluded. Start NEW GAME for another operation."
        problem = plan.validate()
        if problem:
            return "XO: " + problem + " No order executed."
        if plan.action == "speed" and plan.speed_knots is None:
            return "HELM: Specify a speed in knots. No order executed."
        if plan.speed_knots is not None and plan.speed_knots > self.sub.speed:
            return f"HELM: Maximum exercise speed for {self.sub.name} is {self.sub.speed:g} kt. No order executed."
        if plan.action == "transmit" and s.phase == "infiltration" and s.inbound_progress < 95:
            return f"NAVIGATOR: Only {s.inbound_progress:.0f}% of the approach is complete. The objective marker is out of range."
        if plan.action == "bottom" and (self.water_depth() < 160 or
                (s.phase == "infiltration" and s.inbound_progress >= 90)):
            return "NAVIGATOR: Seabed hold is not approved in this exercise sector. No order executed."
        if plan.action in {"depth", "cruise", "silent", "advance", "speed"} and s.bottomed:
            return "XO: We are bottomed. Depart the surveyed seabed first."
        if plan.depth_ft is not None:
            if s.bottomed:
                return "NAVIGATOR: Depart the seabed before changing depth. No order executed."
            max_depth = min(self.water_depth() - 40, self.sub.depth)
            if not 25 <= plan.depth_ft <= max_depth:
                return f"NAVIGATOR: {plan.depth_ft} feet is not cleared. Safe exercise range: 25-{max_depth} ft. No order executed."
        if plan.action == "periscope" and (plan.depth_ft if plan.depth_ft is not None else s.depth) > 60:
            return "XO: Periscope observation not cleared at that depth. No order executed."
        notices = []
        if plan.acknowledgement:
            notices.append("XO (interpreted): " + plan.acknowledgement)
        if plan.report_interval_min is not None:
            s.report_interval = plan.report_interval_min
            s.next_report = s.elapsed + s.report_interval
            notices.append(f'NAVIGATOR: Environmental and depth reports scheduled every {s.report_interval} simulated minutes; safety checks continue between reports.')
        elif plan.disable_reports:
            s.report_interval = 0
            s.next_report = 0
            notices.append('NAVIGATOR: Scheduled reports cancelled. Continuous safety monitoring remains active.')
        if plan.heading_deg is not None:
            s.heading = plan.heading_deg
            notices.append(f'HELM: New schematic heading {s.heading:03d} true. Route stays within exercise-control limits.')
        actual_action = "depth" if plan.action == "none" and plan.depth_ft is not None else plan.action
        if plan.depth_ft is not None and actual_action != "depth":
            s.depth = plan.depth_ft
            notices.append(f'HELM: Operating depth {s.depth} feet authorized and achieved while carrying out the main order.')
            low, high = self.thermal_layer()
            if low <= s.depth <= high:
                notices.append('SONAR: Inside the simulated thermal gradient. Sound propagation may change; no concealment guaranteed.')
        if plan.speed_knots is not None and plan.action not in {"silent", "advance"}:
            s.speed = plan.speed_knots
            s.silent_running = s.speed <= 2
            notices.append(f'HELM: Speed ordered {s.speed:g} knots.')
        if plan.readouts:
            for name in dict.fromkeys(plan.readouts):
                notices.append(self._readout(name))
        main = actual_action
        if main == "none":
            return "\n\n".join(notices) or "XO: No changes to the standing orders, Captain."
        if main == "depth" and plan.depth_ft is None:
            return "HELM: What operating depth would you like, Captain?"
        arg = (1944 if plan.vintage_id else 0) if main == "transmit" else plan.depth_ft if main == "depth" else plan.speed_knots if main == "speed" else None
        result = self._action_with_clock(main, arg)
        if main in {"talk", "inspect", "repair"} and plan.topic:
            notices.append(f'XO: Your request regarding "{plan.topic[:120]}" has been noted for this exercise. Detailed ship systems beyond the model remain abstracted.')
        return "\n\n".join(notices + [result])

    def command(self, raw: str) -> str:
        order = raw.strip()
        if not order:
            return "XO: I need an order, Captain. A, B, or C works too."
        if order.lower() in {"help", "?"}:
            return self.help_text()
        if order.lower() in {"subs", "submarines", "ship list"}:
            return "PLAYABLE SUBMARINES (choose from Fleet Menu or --submarine):\n" + "\n".join(
                f" - {ship.name} [{ship.country}]" for ship in SUBMARINES.values())
        choices = {item.key: item.command for item in self.choices()}
        if order.upper() in choices:
            order = choices[order.upper()]
        plan = parse_offline(order, layer_low=self.thermal_layer()[0], layer_high=self.thermal_layer()[1])
        return self.apply_plan(plan, order)

    def command_ai(self, raw: str, client: AICaptain) -> str:
        """Plan an open-ended order with AI, apply deterministic game rules,
        then (if a turn advanced) request story-style crew narration.
        """
        order = raw.strip()
        if not order:
            return "XO: I need an order, Captain."
        if order.lower() in {"help", "?"}:
            return self.help_text()
        if order.lower() in {"subs", "submarines", "ship list"}:
            return "PLAYABLE SUBMARINES (choose from Fleet Menu or --submarine):\n" + "\n".join(
                f" - {ship.name} [{ship.country}]" for ship in SUBMARINES.values())
        choices = {item.key: item.command for item in self.choices()}
        if order.upper() in choices:
            order = choices[order.upper()]
        prior = {
            "turn": self.s.turn, "time": clock(self.s.elapsed),
            "depth": self.s.depth, "battery": round(self.s.battery),
            "detection": self.s.detection, "phase": self.s.phase,
        }
        plan = client.plan(order, self)
        before_turn = self.s.turn
        engine_result = self.apply_plan(plan, order)
        # No state change from a rejected order: avoid inventing a scene.
        if self.s.turn == before_turn:
            return engine_result
        try:
            scene = client.narrate(order, prior, self, engine_result)
        except AIError as exc:
            return engine_result + "\n\nAI narration unavailable: " + str(exc)
        # Story first; mechanics and score stay visibly authoritative.
        combined = "CREW / NARRATED TURN\n" + scene + "\n\n--- VERIFIED SIMULATION RESULTS ---\n" + engine_result
        if self.log:
            self.log[-1] = combined[-9000:]
        return combined

    def save(self, destination: Path) -> None:
        # The random state is stored as a JSON-compatible nested list structure;
        # no pickle or executable deserialization is involved.
        data = {
            "version": VERSION,
            "seed": self.seed,
            "state": asdict(self.state),
            "contacts": self.sonar_world.serialize(),
            "rng_state": self.rng.getstate(),
            "log": self.log[-80:],
        }
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, destination: Path) -> "Game":
        data = json.loads(destination.read_text(encoding="utf-8"))
        if data.get("version") not in {VERSION, "2.0", "1.0"}:
            raise ValueError("This save belongs to an unsupported version of the game.")
        if not isinstance(data.get("state"), dict):
            raise ValueError("Save file does not contain game state.")
        fields = GameState.__dataclass_fields__
        saved = {k:v for k,v in data["state"].items() if k in fields}
        game = cls(seed=int(data["seed"]), submarine=saved.get("submarine_id", DEFAULT_SUBMARINE))
        game.state = GameState(**saved)
        game.sonar_world = SonarWorld(game, saved=data.get("contacts") if data.get("version") == VERSION else None)
        def convert_to_tuple(x):
            return tuple(convert_to_tuple(v) for v in x) if isinstance(x, list) else x
        game.rng.setstate(convert_to_tuple(data["rng_state"]))
        game.log = list(data.get("log", []))[-80:]
        return game


def play_console(seed: Optional[int] = None, difficulty: str = "normal", ai: bool = False, model: str = "gpt-4.1-mini", submarine: str = DEFAULT_SUBMARINE) -> None:
    game = Game(seed, difficulty, submarine=submarine)
    client = None
    if ai:
        try:
            client = AICaptain(os.environ.get("OPENAI_API_KEY", ""), model=model)
            print("OPTIONAL AI CAPTAIN ENABLED. Requests use a separately billed OpenAI API key.")
        except AIError as exc:
            print("AI UNAVAILABLE:", exc, "\nOffline mode will be used.")
    print("\n" + game.opening())
    while True:
        print("\n" + "-" * 66)
        print(game.status_text())
        print("-" * 66)
        for choice in game.choices():
            print(f" {choice.key}) {choice.title}: {choice.summary}")
        if game.s.phase in {"success", "failure"}:
            answer = input("\n[N]ew game or [Q]uit? ").strip().lower()
            if answer in {"n", "new"}:
                game = Game(None, difficulty, submarine=game.sub.id)
                print(game.opening())
                continue
            break
        try:
            response = input("\nCaptain's order (HELP for commands): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nMission paused.")
            return
        if response.lower() in {"menu", "switch", "choose boat"}:
            ships = list(SUBMARINES.values())
            print("\nFLEET MENU  |  enter number or search by class name")
            for i, ship in enumerate(ships,1):
                print(f" {i:3d}  {ship.name} [{ship.country}]")
            try:
                name = input("Choose number or submarine name (Enter cancels): ").strip()
                if name:
                    picked = ships[int(name)-1] if name.isdecimal() and 1 <= int(name) <= len(ships) else select_submarine(name)
                    game = Game(None, difficulty, submarine=picked.id)
                    print(game.opening())
            except (ValueError,IndexError) as exc:
                print("Invalid selection:",exc)
            continue
        if response.lower() in {"quit", "q", "exit"}:
            print("Mission paused. Use SAVE before quitting to keep progress.")
            break
        if response.lower().startswith("save"):
            parts = response.split(maxsplit=1)
            path = Path(parts[1]).expanduser() if len(parts) == 2 else DEFAULT_SAVE
            try:
                game.save(path)
                print("Game saved to", path)
            except Exception as exc:
                print("Unable to save:", exc)
            continue
        if response.lower().startswith("load"):
            parts = response.split(maxsplit=1)
            path = Path(parts[1]).expanduser() if len(parts) == 2 else DEFAULT_SAVE
            try:
                game = Game.load(path)
                print("Save restored from", path)
            except Exception as exc:
                print("Unable to load:", exc)
            continue
        if client is not None:
            try:
                print("\n" + game.command_ai(response, client))
            except AIError as exc:
                print("AI ERROR:", exc, "\nNo action executed. Use --console without --ai for offline mode.")
        else:
            print("\n" + game.command(response))


def launch_gui(seed: Optional[int] = None, difficulty: str = "normal", ai: bool = False, model: str = "gpt-4.1-mini", submarine: str = DEFAULT_SUBMARINE) -> None:
    import queue
    import threading
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, simpledialog

    NAVY = "#071827"
    PANEL = "#10283b"
    PANEL_2 = "#0c2030"
    TEXT = "#e3f1f5"
    MUTED = "#a9c5cf"
    GREEN = "#76efbd"
    GOLD = "#f4c676"

    root = tk.Tk()
    root.title("Operation Rustbucket | Naval Command Simulation")
    root.geometry("1260x880")
    root.minsize(1000, 720)
    root.configure(bg=NAVY)
    root.withdraw()
    selected = choose_submarine(root, initial=submarine)
    if selected is None:
        root.destroy()
        return
    game = Game(seed, difficulty, submarine=selected)
    root.deiconify()
    client = None
    busy = False
    queue_results = queue.Queue()
    if ai and os.environ.get("OPENAI_API_KEY"):
        client = AICaptain(os.environ["OPENAI_API_KEY"], model=model)

    header = tk.Frame(root, bg=NAVY, pady=10)
    header.pack(side="top", fill="x", padx=16)
    tk.Label(header, text="OPERATION RUSTBUCKET", fg=GREEN, bg=NAVY, font=("Consolas", 20, "bold")).pack(side="left")
    phase_var = tk.StringVar()
    tk.Label(header, textvariable=phase_var, fg=GOLD, bg=NAVY, font=("Consolas", 11)).pack(side="right")

    content = tk.PanedWindow(root, orient="horizontal", bg=NAVY, sashwidth=7, borderwidth=0, relief="flat")
    content.pack(fill="both", expand=True, padx=12, pady=(0, 10))
    sidebar = tk.Frame(content, bg=PANEL, width=325)
    center = tk.Frame(content, bg=NAVY)
    content.add(sidebar, minsize=300, stretch="never")
    content.add(center, minsize=460)

    sub_name_var=tk.StringVar()
    tk.Label(sidebar,textvariable=sub_name_var,bg=PANEL,fg=GREEN,font=("Consolas",11,"bold"),
             wraplength=290,pady=8).pack(fill="x")
    stat_vars = {}
    for label in ["Current time", "Phase", "Heading", "Mission progress", "Time remaining", "Hull integrity", "Battery", "Depth / seabed", "Under-keel", "Speed", "Max game speed", "Dive limit", "Stealth", "Sonar confidence", "Morale", "Exercise torpedoes", "Depth reports"]:
        row = tk.Frame(sidebar, bg=PANEL, pady=1)
        row.pack(fill="x", padx=14)
        tk.Label(row, text=label, fg=MUTED, bg=PANEL, font=("Arial", 10)).pack(side="left")
        var = tk.StringVar()
        tk.Label(row, textvariable=var, fg=TEXT, bg=PANEL, font=("Consolas", 10, "bold")).pack(side="right")
        stat_vars[label] = var
    tk.Label(sidebar, text="SONAR  |  REAL SIMULATED CONTACT TRACKS", fg=MUTED, bg=PANEL, font=("Consolas", 9), pady=3).pack()
    sonar_canvas = tk.Canvas(sidebar, height=235, bg="#061c1c", highlightthickness=0, cursor="crosshair")
    sonar_canvas.pack(fill="x", padx=12, pady=(0, 4))
    selected_track=tk.StringVar(value="Select a contact on the sonar display")
    tk.Label(sidebar,textvariable=selected_track,bg=PANEL,fg=MUTED,font=("Consolas",9),
             wraplength=290,justify="left",anchor="w").pack(fill="x",padx=12,pady=(0,4))
    sonar_targets={}
    sonar_window=[None]

    top_row = tk.Frame(center, bg=NAVY)
    top_row.pack(fill="both", expand=True, padx=10)
    tk.Label(top_row, text="CONTROL ROOM / MISSION LOG", fg=GREEN, bg=NAVY, font=("Consolas", 12, "bold"), anchor="w").pack(fill="x", pady=(5, 8))
    narrative = scrolledtext.ScrolledText(top_row, wrap="word", bg=PANEL_2, fg=TEXT, insertbackground=TEXT, font=("Consolas", 10), relief="flat", padx=14, pady=14)
    narrative.pack(fill="both", expand=True)
    narrative.configure(state="disabled")

    choice_panel = tk.Frame(center, bg=NAVY)
    choice_panel.pack(fill="x", padx=10, pady=8)
    tk.Label(choice_panel, text="YOUR NEXT ORDER  |  CHOOSE A, B, C OR TYPE A CUSTOM COMMAND", fg=GOLD, bg=NAVY, font=("Consolas", 10, "bold"), anchor="w").pack(fill="x", pady=(2, 5))
    choices_buttons = []
    for j in range(3):
        b = tk.Button(choice_panel, bg=PANEL, fg=TEXT, activebackground="#20425a", activeforeground=TEXT,
                      relief="flat", bd=0, anchor="w", justify="left", wraplength=730,
                      padx=10, pady=8, font=("Arial", 10), cursor="hand2")
        b.pack(fill="x", pady=3)
        choices_buttons.append(b)

    bottom = tk.Frame(center, bg=NAVY)
    bottom.pack(fill="x", padx=10, pady=(0, 6))
    order_var = tk.StringVar()
    order_entry = tk.Entry(bottom, textvariable=order_var, font=("Consolas", 11), bg="#143347", fg=TEXT,
                           insertbackground=TEXT, relief="flat", highlightthickness=1, highlightbackground="#23556b")
    order_entry.pack(side="left", fill="x", expand=True, ipady=9)

    def show_output(text: str) -> None:
        narrative.configure(state="normal")
        narrative.insert("end", "\n\n" + ("=" * 56) + "\n" + text)
        narrative.see("end")
        narrative.configure(state="disabled")

    def draw_sonar(canvas, *, full_size=False):
        canvas.delete("all")
        w=max(220,canvas.winfo_width())
        h=max(245,canvas.winfo_height())
        cx,cy=w/2,h/2
        radius=max(75,min(w,h)/2-24)
        color_grid="#245b52"
        for fraction, label in [(1/3,"2"),(2/3,"4"),(1,"6 NM")]:
            r=radius*fraction
            canvas.create_oval(cx-r,cy-r,cx+r,cy+r,outline=color_grid,width=1)
            canvas.create_text(cx+r-2,cy+3,text=label,fill="#4b8f81",font=("Consolas",8),anchor="e")
        canvas.create_line(cx,cy-radius-10,cx,cy+radius+10,fill="#295c52")
        canvas.create_line(cx-radius-10,cy,cx+radius+10,cy,fill="#295c52")
        for a, label in [(0,"N"),(90,"E"),(180,"S"),(270,"W")]:
            from math import radians,sin,cos
            x=cx+sin(radians(a))*(radius+12)
            y=cy-cos(radians(a))*(radius+12)
            canvas.create_text(x,y,text=label,fill="#7dd0a0",font=("Consolas",8,"bold"))
        canvas.create_oval(cx-5,cy-5,cx+5,cy+5,fill=GREEN,outline="")
        # Green heading vector indicates the commanded course.
        from math import radians,sin,cos
        head=radians(game.s.heading)
        canvas.create_line(cx,cy,cx+sin(head)*radius*.7,cy-cos(head)*radius*.7,fill="#225e46",width=2,arrow="last")
        local_targets={}
        for c in game.sonar_world.observed():
            if c.measured_range > 6:
                continue
            angle=radians(c.measured_bearing)
            dist=radius*c.measured_range/6
            x,y=cx+sin(angle)*dist,cy-cos(angle)*dist
            known=c.confidence >= 75
            tone=("#7beaba" if c.side=="friendly" else "#eaa76c" if known else "#f2d16e")
            stale=game.s.elapsed-c.last_seen>8
            symbol=6 if known else 4
            canvas.create_oval(x-symbol,y-symbol,x+symbol,y+symbol,
                               outline=tone,fill="" if stale else tone,width=2,tags=("track",c.key))
            if stale:
                canvas.create_line(x-8,y-8,x+8,y+8,fill=tone,tags=("track",c.key))
            caption=c.key if not full_size else f"{c.key} {c.measured_range:.1f} nm"
            canvas.create_text(x+9,y-9,text=caption,fill=tone,anchor="sw",font=("Consolas",8),tags=("track",c.key))
            local_targets[c.key]=(x,y,c)
        if not full_size:
            sonar_targets.clear()
            sonar_targets.update(local_targets)
        canvas.create_text(8,7,text=f"{clock(game.s.elapsed)}  {game.s.sonar_mode.upper()}  •  6 NM",fill=GREEN,
                           anchor="nw",font=("Consolas",8,"bold"))
        if not local_targets:
            canvas.create_text(cx,cy+38,text="NO TRACKS IN RANGE",fill="#76a89b",font=("Consolas",9))
        return local_targets

    def redraw_sonar():
        draw_sonar(sonar_canvas)
        if sonar_window[0] is not None and sonar_window[0].winfo_exists():
            radar, rows=sonar_window[0].radar_canvas,sonar_window[0].rows_widget
            draw_sonar(radar,full_size=True)
            rows.delete("1.0","end")
            rows.insert("end",game.sonar_report())

    def click_sonar(event):
        import math
        if not sonar_targets:
            selected_track.set("No current contacts. Try LISTEN or ACTIVE PING.")
            return
        near=min(sonar_targets.values(),key=lambda t:math.hypot(t[0]-event.x,t[1]-event.y))
        if math.hypot(near[0]-event.x,near[1]-event.y)>24:
            return
        c=near[2]
        selected_track.set(f"{c.key}: {game.sonar_world.display_label(c)} | {c.measured_bearing:.0f}° | ~{c.measured_range:.1f} nm | {c.confidence:.0f}% confidence")

    sonar_canvas.bind("<Button-1>",click_sonar)

    def refresh() -> None:
        s=game.s
        p=s.inbound_progress if s.phase=="infiltration" else s.escape_progress
        floor=game.water_depth()
        vals={
            "Current time":clock(s.elapsed), "Phase":s.phase.upper(),"Mission progress":f"{p:.0f}%",
            "Time remaining":f"{game.remaining()} min", "Heading":f"{s.heading:03d} true", "Hull integrity":f"{s.hull}%",
            "Battery":f"{s.battery:.0f}%", "Depth / seabed":f"{s.depth}/{floor} ft",
            "Under-keel":f"~{max(0,floor-s.depth-10)} ft" if not s.bottomed else "On seabed",
            "Speed":f"{s.speed:g} kt", "Max game speed":f"{game.sub.speed:g} kt", "Dive limit":f"{game.sub.depth} ft", "Stealth":s.detection.upper(),
            "Sonar confidence":f"{s.sonar_confidence}%", "Morale":f"{s.crew_morale}%",
            "Exercise torpedoes":f"{s.torpedoes}", "Depth reports":f"{s.report_interval} min" if s.report_interval else "OFF",
        }
        sub_name_var.set(game.sub.name)
        for label,var in stat_vars.items(): var.set(vals[label])
        phase_var.set(f"TURN {s.turn:02d} | {s.phase.upper()} | {'AI CONNECTED' if client else 'OFFLINE'} | SEED {game.seed}")
        options=game.choices()
        for i,b in enumerate(choices_buttons):
            if i < len(options):
                c=options[i]
                b.configure(text=f"{c.key}. {c.title}  -  {c.summary}", command=lambda cmd=c.command: order(cmd), state="normal")
            else:
                b.configure(text="MISSION COMPLETE - Choose New Game",state="disabled")
        redraw_sonar()

    def order(value: Optional[str]=None) -> None:
        nonlocal busy
        if busy:
            return
        cmd=order_var.get().strip() if value is None else value
        if not cmd:
            return
        order_var.set("")
        if client and cmd.lower() not in {"help", "?", "sonar", "status", "depth report", "fleet", "map", "chart", "environment"}:
            busy = True
            show_output(f"CAPTAIN'S ORDER: {cmd}\n\nConsulting AI crew interpreter (mission status remains controlled by the local game)...")
            refresh()
            def worker():
                try:
                    result = game.command_ai(cmd, client)
                except AIError as exc:
                    result = "AI MODE ERROR: " + str(exc) + "\nNo order was applied. Disable AI to use offline interpretation."
                except Exception as exc:
                    result = "GAME ERROR: " + type(exc).__name__ + ": " + str(exc)
                queue_results.put((cmd, result))
            threading.Thread(target=worker, daemon=True).start()
        else:
            result=game.command(cmd)
            show_output(f"YOUR ORDER: {cmd.upper()}\n\n{result}")
            refresh()
        order_entry.focus_set()

    def poll_ai_results() -> None:
        nonlocal busy
        try:
            while True:
                cmd, result = queue_results.get_nowait()
                show_output(f"YOUR ORDER: {cmd.upper()}\n\n{result}")
                busy = False
                refresh()
        except queue.Empty:
            pass
        root.after(120, poll_ai_results)

    root.after(120, poll_ai_results)

    tk.Button(bottom, text="ISSUE ORDER", command=order, bg="#16674e", fg="white", activebackground="#258963", relief="flat", bd=0, padx=14, pady=10, font=("Consolas",10,"bold")).pack(side="right", padx=(7,0))
    order_entry.bind("<Return>", lambda _: order())

    tools_frame = tk.Frame(center, bg=NAVY)
    tools_frame.pack(fill="x", padx=10, pady=(0, 8))
    def info(command: str) -> None: order(command)
    for label, cmd in [("Sonar","sonar"),("Depth","depth report"),("Chart","map"),("Fleet","fleet"),("Help","help")]:
        tk.Button(tools_frame,text=label,command=lambda c=cmd: info(c),bg=PANEL,fg=TEXT,activebackground="#23526b",relief="flat",padx=10,pady=6).pack(side="left",padx=(0,5))
    sonar_buttons=tk.Frame(sidebar,bg=PANEL)
    sonar_buttons.pack(fill="x",padx=10,pady=(3,5))
    tk.Button(sonar_buttons,text="LISTEN",command=lambda:order("analyze sonar contacts"),bg="#204c52",fg=TEXT,
              relief="flat",padx=8,pady=5).pack(side="left",expand=True,fill="x",padx=2)
    tk.Button(sonar_buttons,text="ACTIVE PING",command=lambda:order("ping"),bg="#673f33",fg=TEXT,
              relief="flat",padx=8,pady=5).pack(side="left",expand=True,fill="x",padx=2)

    def open_sonar_console():
        if sonar_window[0] is not None and sonar_window[0].winfo_exists():
            sonar_window[0].lift()
            return
        top=tk.Toplevel(root)
        top.title("Sonar Room  |  " + game.sub.name)
        top.geometry("840x680")
        top.minsize(650,520)
        top.configure(bg=NAVY)
        tk.Label(top,text="SONAR ROOM  •  DETECT / CLASSIFY / TRACK",fg=GREEN,bg=NAVY,
                 font=("Consolas",15,"bold")).pack(pady=14)
        radar=tk.Canvas(top,height=355,bg="#061c1c",highlightthickness=0)
        radar.pack(fill="both",expand=True,padx=16)
        rows=scrolledtext.ScrolledText(top,bg=PANEL_2,fg=TEXT,font=("Consolas",10),height=9,
                                      relief="flat",wrap="word",padx=8,pady=8)
        rows.pack(fill="both",padx=16,pady=10)
        controls=tk.Frame(top,bg=NAVY)
        controls.pack(fill="x",padx=15,pady=(0,15))
        for label,cmd in [("PASSIVE LISTEN","analyze sonar contacts"),("ACTIVE PING","ping"),("REFRESH TRACKS","sonar")]:
            tk.Button(controls,text=label,command=lambda c=cmd:order(c),bg=PANEL,fg=TEXT,
                      relief="flat",padx=15,pady=9).pack(side="left",padx=5)
        top.radar_canvas=radar
        top.rows_widget=rows
        sonar_window[0]=top
        radar.bind("<Configure>",lambda _:draw_sonar(radar,full_size=True))
        redraw_sonar()

    tk.Button(tools_frame,text="Sonar Console",command=open_sonar_console,bg="#21445a",fg=TEXT,
              relief="flat",padx=10,pady=6).pack(side="left",padx=5)

    def do_save() -> None:
        if busy:
            messagebox.showinfo("AI running", "An AI turn is in progress. Save after it completes.")
            return
        path=filedialog.asksaveasfilename(title="Save Operation Rustbucket",initialfile="rustbucket_save.json",defaultextension=".json",filetypes=[("JSON save","*.json")])
        if path:
            try:
                game.save(Path(path))
                show_output("SAVE COMPLETE: " + path)
            except Exception as exc:
                messagebox.showerror("Save error",str(exc))
    def do_load() -> None:
        nonlocal game
        if busy:
            messagebox.showinfo("AI running", "An AI turn is in progress. Load after it completes.")
            return
        path=filedialog.askopenfilename(title="Load Operation Rustbucket",filetypes=[("JSON save","*.json")])
        if path:
            try:
                game=Game.load(Path(path))
                narrative.configure(state="normal")
                narrative.delete("1.0","end")
                narrative.configure(state="disabled")
                show_output("LOADED SAVE\n"+(game.log[-1] if game.log else game.opening()))
                refresh()
            except Exception as exc:
                messagebox.showerror("Load error",str(exc))
    def new_game() -> None:
        nonlocal game
        if busy:
            messagebox.showinfo("AI running", "An AI turn is in progress. Start another game afterward.")
            return
        if not messagebox.askyesno("New game", "Start a new Operation Rustbucket mission?"):
            return
        ship_id=choose_submarine(root,game.sub.id)
        if ship_id is None:
            return
        game=Game(None, difficulty, submarine=ship_id)
        narrative.configure(state="normal")
        narrative.delete("1.0","end")
        narrative.configure(state="disabled")
        show_output(game.opening())
        refresh()
    ai_button = tk.Button(tools_frame, text="AI MODE: ON" if client else "AI MODE: OFF", bg="#195c4c" if client else "#21445a", fg=TEXT, relief="flat", padx=10, pady=6)
    ai_button.pack(side="right", padx=(5, 0))
    def toggle_ai():
        nonlocal client
        if busy:
            messagebox.showinfo("AI running", "Finish this turn before changing the mode.")
            return
        if client:
            client = None
            show_output("OFFLINE MODE enabled. Flexible phrase matching remains available; no API requests are made.")
        else:
            key = os.environ.get("OPENAI_API_KEY", "").strip()
            if not key:
                key = simpledialog.askstring("Optional AI captain", "Enter your OpenAI API key (separately billed).\nUsed in memory only; never saved to your game file.\nCancel to keep offline mode.", show="*", parent=root)
            if not key:
                return
            try:
                client = AICaptain(key, model=model)
            except AIError as exc:
                messagebox.showerror("AI setup error", str(exc))
                return
            show_output("AI CAPTAIN ENABLED. Your orders and recent game context will be sent to OpenAI.\nAPI usage is billed separately from ChatGPT subscriptions.\nThe game engine still enforces status and mission rules. Turn off AI anytime.")
        ai_button.configure(text="AI MODE: ON" if client else "AI MODE: OFF", bg="#195c4c" if client else "#21445a")
        refresh()
    ai_button.configure(command=toggle_ai)
    for label, action in [("Save",do_save),("Load",do_load),("New Game",new_game)]:
        tk.Button(tools_frame,text=label,command=action,bg="#21445a",fg=TEXT,relief="flat",padx=10,pady=6).pack(side="right",padx=(5,0))
    menu_bar=tk.Menu(root)
    mission_menu=tk.Menu(menu_bar,tearoff=0)
    mission_menu.add_command(label="Choose Submarine / New Mission...",command=new_game)
    mission_menu.add_separator()
    mission_menu.add_command(label="Save Mission...",command=do_save)
    mission_menu.add_command(label="Load Mission...",command=do_load)
    mission_menu.add_separator()
    mission_menu.add_command(label="Quit",command=root.destroy)
    menu_bar.add_cascade(label="Game",menu=mission_menu)
    sonar_menu=tk.Menu(menu_bar,tearoff=0)
    sonar_menu.add_command(label="Open Sonar Console",command=open_sonar_console)
    sonar_menu.add_command(label="Passive Listening",command=lambda:order("analyze sonar contacts"))
    sonar_menu.add_command(label="Active Ping",command=lambda:order("ping"))
    menu_bar.add_cascade(label="Sonar",menu=sonar_menu)
    root.configure(menu=menu_bar)
    sonar_canvas.bind("<Configure>", lambda _: redraw_sonar())
    show_output(game.opening())
    refresh()
    order_entry.focus_set()
    root.mainloop()


def demo() -> None:
    """Noninteractive deterministic demo for automated smoke testing."""
    game=Game(seed=1944, difficulty="easy")
    print(game.opening())
    for step in range(45):
        if game.s.phase in {"success","failure"}: break
        if game.s.phase=="infiltration" and game.s.inbound_progress>=95:
            cmd="transmit 1944"
        elif game.s.bottomed:
            cmd="depart"
        elif game.water_depth()-game.s.depth-10<35:
            cmd="depth 75"
        else:
            cmd="silent"
        result=game.command(cmd)
        print(f"\nTURN {game.s.turn}: {cmd} -> {game.s.phase} / {game.s.inbound_progress:.0f} in / {game.s.escape_progress:.0f} out / {game.s.battery:.0f}% battery")
        if game.s.phase in {"success","failure"}:
            print(result)
    if game.s.phase not in {"success","failure"}:
        raise RuntimeError("Demo did not reach a conclusion")


def main() -> None:
    parser=argparse.ArgumentParser(description="Operation Rustbucket: a Python submarine adventure requiring no third-party packages")
    parser.add_argument("--console",action="store_true",help="Use the text-only terminal game")
    parser.add_argument("--ai", action="store_true", help="Enable optional OpenAI API mode (requires OPENAI_API_KEY and API billing)")
    parser.add_argument("--model", default="gpt-4.1-mini", help="AI model used with --ai (default: gpt-4.1-mini)")
    parser.add_argument("--demo",action="store_true",help="Run a noninteractive smoke-test mission")
    parser.add_argument("--seed",type=int,help="Set deterministic scenario seed")
    parser.add_argument("--submarine",default=DEFAULT_SUBMARINE,
                        help="Choose submarine by unique name or ID, e.g. 'Type XXI' (console or menu default)")
    parser.add_argument("--list-subs",action="store_true",help="List all playable submarines")
    parser.add_argument("--difficulty",choices=["easy","normal","hard"],default="normal")
    args=parser.parse_args()
    if args.list_subs:
        for i,sub in enumerate(SUBMARINES.values(),1):
            print(f"{i:3d}. {sub.name}  [{sub.country}; {sub.era}]")
        return
    try:
        select_submarine(args.submarine)
    except ValueError as exc:
        parser.error(str(exc))
    if args.demo:
        demo()
        return
    if args.console:
        play_console(args.seed,args.difficulty, ai=args.ai, model=args.model, submarine=args.submarine)
        return
    try:
        launch_gui(args.seed,args.difficulty, ai=args.ai, model=args.model, submarine=args.submarine)
    except (ImportError, RuntimeError) as exc:
        print(f"Desktop UI unavailable ({exc}). Starting console mode.")
        play_console(args.seed,args.difficulty, ai=args.ai, model=args.model, submarine=args.submarine)
    except Exception as exc:
        # Only fall back when the display cannot be created; do not hide GUI bugs.
        if exc.__class__.__name__ == "TclError":
            print(f"No graphical desktop available ({exc}); starting console mode.")
            play_console(args.seed,args.difficulty, ai=args.ai, model=args.model, submarine=args.submarine)
        else:
            raise


if __name__ == "__main__":
    main()
