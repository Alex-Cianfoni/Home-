#!/usr/bin/env python3
"""Operation Rustbucket - an interactive, fictional submarine command game.

Runs with Python 3.9+ standard library only. Launches a Tkinter desktop game
when a graphical display is available; pass --console for a terminal version.
All vessels, navigation, detection and incidents are fictional game mechanics.
"""
from __future__ import annotations

import argparse
import json
import random
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

VERSION = "1.0"
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
    def __init__(self, seed: Optional[int] = None, difficulty: str = "normal") -> None:
        self.seed = seed if seed is not None else random.randrange(1, 10**9)
        self.rng = random.Random(self.seed)
        self.state = GameState(difficulty=difficulty)
        self.log = [self.opening()]

    def opening(self) -> str:
        return (
            "OPERATION RUSTBUCKET / PORT MERIDIAN / 02:15\n"
            "----------------------------------------------\n"
            "You command USS Razorback (SS-394), a fantastically restored GUPPY IIA "
            "diesel-electric submarine, in a Down Periscope-style exercise.\n\n"
            "The 273-vessel Museum Alliance is conducting a joint wargame against "
            "a modern naval task force. Infiltrate a fictional defended harbor, "
            "transmit an authenticated exercise marker, then escape before 08:31.\n\n"
            'XO: "A whole modern fleet looking for one museum submarine, Captain."\n'
            'Chief Engineer: "If they can find our spare parts, they can find us."\n'
            'Sonar: "Unknown electric contact, bearing zero-five-eight. No confirmation of detection."\n\n'
            "Choose A, B, or C, or type a custom captain's order. Type HELP for commands."
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
            f"TURN {s.turn} | {clock(s.elapsed)} | {phase}\n"
            f"Progress: {progress:.0f}% | Deadline: {clock(DEADLINE_MINUTES)} "
            f"| Time left: {self.remaining()} min\n"
            f"Hull: {s.hull}% | Battery: {s.battery:.0f}% | Depth: {s.depth} ft "
            f"| Bottom: {bottom} ft | Keel clearance: ~{clearance} ft\n"
            f"Speed: {s.speed:g} kt | Silent: {'YES' if s.silent_running else 'NO'} "
            f"| Bottomed: {'YES' if s.bottomed else 'NO'}\n"
            f"Stealth: {s.detection.upper()} | Sensor confidence: {s.sonar_confidence}% "
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
        s = self.s
        if s.phase == "infiltration":
            if s.inbound_progress < 30:
                tracks = ["Track 01: faint electric propulsion; possible modern submarine", "Track 02: intermittent mechanical noise; classification uncertain"]
            elif s.inbound_progress < 75:
                tracks = ["Track ALPHA: distant surface machinery", "Track BRAVO: intermittent exercise patrol transmissions", "Track CHARLIE: possible autonomous underwater craft"]
            else:
                tracks = ["Track BLUE-17: surface patrol, unconfirmed proximity", "Track UNKNOWN: faint submerged acoustic contact"]
        else:
            tracks = ["Track BRAVO: intermittent search activity", "Track SUB-01: faint underwater contact; identity uncertain"]
            if s.escape_progress > 75:
                tracks = ["Surface contact near extraction: potential friendly vessel", "Distant sonar reports; no closing contact confirmed"]
        if s.sonar_confidence > 75:
            tracks.append("Passive analysis: classification confidence improved; no exact range available")
        return "PASSIVE SONAR REPORT\n" + "\n".join("- " + track for track in tracks) + f"\nBlue Force detection: {s.detection}."

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
            "  speed 4      - set speed (0 to 8 knots) and advance\n"
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
            "  save / load / quit (console mode; GUI has buttons)\n"
            "Combine orders with semicolons, e.g. 'depth 130; report 30; silent'.\n"
            "Everything is fictional and uses game-abstracted systems."
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
        chance = clamp(base + extra + noise_modifier + s.suspicion / 14 + layer_effect - (5 if s.silent_running else 0) - (5 if s.bottomed else 0), 1.5, 75)
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
                return 'EXERCISE CONTROL: "Blue Force has registered a confirmed detection of Razorback."'
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
                f"MISSION COMPLETE: {s.score}/100 points. "
                f"Confirmed detection: {'YES' if s.detection == 'confirmed' else 'NO'}. "
                f"Battery: {s.battery:.0f}%. Hull: {s.hull}%.\n"
                "The 1944-style stunt is remembered by Blue Force's baffled communications officer."
                if s.vintage_radio else
                "\n*** EXTRACTION BOUNDARY CROSSED ***\n"
                f"MISSION COMPLETE: {s.score}/100 points. USS Razorback returns to fleet command.\n"
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

        if kind == "silent":
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
            if not 0 <= arg <= 8:
                return "HELM: Speed must be between zero and eight knots in this exercise."
            s.speed = float(arg)
            s.silent_running = s.speed <= 2
            elapsed = self.rng.randint(16, 22)
            moved = s.speed > 0
            noise = 5 if s.speed >= 5 else 0
            lines.append(f'HELM: "Speed set to {s.speed:g} knots. {"Silent" if s.silent_running else "Standard"} running."')
        elif kind == "analyze":
            elapsed = self.rng.randint(12, 16)
            s.speed = 0
            s.sonar_confidence = min(100, s.sonar_confidence + 14)
            lines.append('SONAR: "Holding station to study contacts. Confidence improving; exact ranges still uncertain."')
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
            max_authorized = self.water_depth() - 40
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
                    'RADIO: "... .-.-. ... USS RAZORBACK SS-394 / COMMISSIONED 1944 / MISSION ACCOMPLISHED"',
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
            if s.sonar_confidence < 55:
                return "XO: No positively classified exercise target. Simulated launch denied. Analyze sonar first."
            s.torpedoes -= 1
            elapsed = 12
            noise = 15
            lines.append('WEAPONS: "One inert exercise torpedo adjudicated. No combat scoring objective is active."')
            lines.append('XO: "We can avoid firing these, Captain. Stealth scores better than bravado."')
        else:
            return "I did not recognize that command. Type HELP for supported captain's orders."

        s.turn += 1
        s.elapsed += elapsed
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

    def command(self, raw: str) -> str:
        s = self.s
        order = raw.strip()
        if not order:
            return "XO: I need an order, Captain. A, B, or C works too."
        if s.phase in {"success", "failure"}:
            return "The mission is over. Choose NEW GAME to launch another operation."
        short = order.upper()
        choices = {item.key: item.command for item in self.choices()}
        if short in choices:
            order = choices[short]
        # Permit compound standing orders plus one time-advancing command.
        segments = [p.strip().lower() for p in re.split(r"\s*;\s*|\s+and\s+", order) if p.strip()]
        time_actions = []
        notices = []
        for seg in segments:
            if seg in {"lay on bottom of sea floor turn off engines", "lay on the sea floor and turn off engines", "lay on the bottom and turn off engines"}:
                seg = "bottom"
            if seg in {"help", "?"}:
                return self.help_text()
            if seg in {"status", "st"}:
                return self.status_text()
            if seg in {"sonar", "contacts", "passive sonar"}:
                return self.sonar_report()
            if seg in {"depth report", "environment", "check depth", "thermal report"}:
                return self.environmental_report()
            if seg in {"fleet", "allies"}:
                return self.fleet_report()
            if seg in {"map", "chart"}:
                return self.map_text()
            match_report = re.fullmatch(r"(?:report|check depth every|depth checks every)\s+(\d+)\s*(?:min|mins|minute|minutes)?", seg)
            if match_report:
                interval = int(match_report.group(1))
                if not 5 <= interval <= 120:
                    return "NAVIGATOR: Reporting interval must be between 5 and 120 minutes."
                s.report_interval = interval
                s.next_report = s.elapsed + interval
                notices.append(f"NAVIGATOR: Depth and keel-clearance reports scheduled every {interval} minutes.")
                continue
            if seg in {"report off", "stop reports"}:
                s.report_interval = 0
                s.next_report = 0
                notices.append("NAVIGATOR: Scheduled environmental reports disabled; safety monitoring continues.")
                continue
            if seg in {"silent", "silent running", "quiet", "two knots", "maintain silent", "silent running at two knots", "maintain two knots", "continue silent running", "go silent", "maintain silent withdrawal"}:
                time_actions.append(("silent", None))
            elif seg in {"advance", "proceed", "continue", "maintain course", "present course", "continue on present course", "continue on the present course", "maintain present course", "maintain our present course"}:
                time_actions.append(("advance", None))
            elif seg in {"hold", "wait", "stop", "engines off", "turn off engines", "propulsion off", "hold position"}:
                time_actions.append(("wait", None))
            elif seg in {"analyze", "listen", "hold and listen", "passive contact analysis"}:
                time_actions.append(("analyze", None))
            elif seg in {"bottom", "lay on bottom", "lay on bottom of sea floor", "lay on bottom of seabed", "settle on seabed", "seabed"}:
                time_actions.append(("bottom", None))
            elif seg in {"depart", "leave bottom", "depart bottom", "lift off seabed"}:
                time_actions.append(("depart", None))
            elif seg in {"thermal", "thermal layer", "enter thermal layer", "go into thermal layer", "go into the thermal layer", "enter the thermal layer"}:
                low, high = self.thermal_layer()
                time_actions.append(("depth", (low + high) // 2))
            elif seg in {"radio", "request clearance", "exercise control", "coordinate", "contact becuna"}:
                time_actions.append(("radio", None))
            elif seg in {"alternate", "alternate route", "alternate extraction", "request deeper route"}:
                time_actions.append(("alternate", None))
            elif seg in {"transmit 1944", "1944", "vintage", "vintage id", "morse", "send 1944", "transmit at last second in 1944 identification", "1944 identification transmission"}:
                time_actions.append(("transmit", 1944))
            elif seg in {"transmit", "marker", "send marker", "send identification"}:
                time_actions.append(("transmit", 0))
            elif seg in {"fire", "fire torpedo", "exercise fire"}:
                time_actions.append(("fire", None))
            elif re.fullmatch(r"(?:depth|dive to|ascend to)\s*\d+\s*(?:ft|feet)?", seg):
                val = float(re.search(r"\d+", seg).group())
                time_actions.append(("depth", val))
            elif re.fullmatch(r"(?:speed|make)\s*\d+(?:\.\d+)?\s*(?:kt|knots)?", seg):
                val = float(re.search(r"\d+(?:\.\d+)?", seg).group())
                time_actions.append(("speed", val))
            else:
                return f"XO: I don't recognize '{seg}'. Type HELP for the available orders."
        if len(time_actions) == 2 and time_actions[0][0] == "bottom" and time_actions[1][0] == "wait":
            notices.append("ENGINEERING: Propulsion will be secured during the approved seabed hold.")
            time_actions = [time_actions[0]]
        if len(time_actions) == 2 and time_actions[0][0] == "depth" and time_actions[1][0] in {"silent", "advance"}:
            # Allow a realistic combined order: change to a cleared depth,
            # then continue the same leg. The depth change itself is assumed
            # to occur during this single game turn.
            goal = round(time_actions[0][1])
            max_authorized = self.water_depth() - 40
            if self.s.bottomed or goal < 25 or goal > max_authorized:
                return f"NAVIGATOR: Requested depth {goal} ft is not cleared in this sector."
            self.s.depth = goal
            notices.append(f"HELM: Requested operating depth {goal} ft confirmed; proceeding with the underway order.")
            time_actions = [time_actions[1]]
        if len(time_actions) > 1:
            return "XO: Send one main action per turn. Combine a cleared depth change with movement or a REPORT 30 standing order."
        if not time_actions:
            return "\n".join(notices) if notices else "No order issued."
        kind, arg = time_actions[0]
        outcome = self._action_with_clock(kind, arg)
        return "\n".join(notices + [outcome])

    def save(self, destination: Path) -> None:
        # The random state is stored as a JSON-compatible nested list structure;
        # no pickle or executable deserialization is involved.
        data = {
            "version": VERSION,
            "seed": self.seed,
            "state": asdict(self.state),
            "rng_state": self.rng.getstate(),
            "log": self.log[-80:],
        }
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, destination: Path) -> "Game":
        data = json.loads(destination.read_text(encoding="utf-8"))
        if data.get("version") != VERSION:
            raise ValueError("This save belongs to a different version of the game.")
        if not isinstance(data.get("state"), dict):
            raise ValueError("Save file does not contain game state.")
        game = cls(seed=int(data["seed"]))
        game.state = GameState(**data["state"])
        def convert_to_tuple(x):
            return tuple(convert_to_tuple(v) for v in x) if isinstance(x, list) else x
        game.rng.setstate(convert_to_tuple(data["rng_state"]))
        game.log = list(data.get("log", []))[-80:]
        return game


def play_console(seed: Optional[int] = None, difficulty: str = "normal") -> None:
    game = Game(seed, difficulty)
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
                game = Game(None, difficulty)
                print(game.opening())
                continue
            break
        try:
            response = input("\nCaptain's order (HELP for commands): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nMission paused.")
            return
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
        print("\n" + game.command(response))


def launch_gui(seed: Optional[int] = None, difficulty: str = "normal") -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext

    NAVY = "#071827"
    PANEL = "#10283b"
    PANEL_2 = "#0c2030"
    TEXT = "#e3f1f5"
    MUTED = "#a9c5cf"
    GREEN = "#76efbd"
    GOLD = "#f4c676"

    root = tk.Tk()
    root.title("Operation Rustbucket | Naval Command Simulation")
    root.geometry("1260x850")
    root.minsize(900, 680)
    root.configure(bg=NAVY)
    game = Game(seed, difficulty)

    header = tk.Frame(root, bg=NAVY, pady=10)
    header.pack(side="top", fill="x", padx=16)
    tk.Label(header, text="OPERATION RUSTBUCKET", fg=GREEN, bg=NAVY, font=("Consolas", 20, "bold")).pack(side="left")
    phase_var = tk.StringVar()
    tk.Label(header, textvariable=phase_var, fg=GOLD, bg=NAVY, font=("Consolas", 11)).pack(side="right")

    content = tk.PanedWindow(root, orient="horizontal", bg=NAVY, sashwidth=7, borderwidth=0, relief="flat")
    content.pack(fill="both", expand=True, padx=12, pady=(0, 10))
    sidebar = tk.Frame(content, bg=PANEL, width=280)
    center = tk.Frame(content, bg=NAVY)
    content.add(sidebar, minsize=240, stretch="never")
    content.add(center, minsize=460)

    tk.Label(sidebar, text="USS RAZORBACK  SS-394", bg=PANEL, fg=GREEN, font=("Consolas", 13, "bold"), pady=18).pack(fill="x")
    stat_vars = {}
    for label in ["Current time", "Phase", "Mission progress", "Time remaining", "Hull integrity", "Battery", "Depth / seabed", "Under-keel", "Speed", "Stealth", "Sonar confidence", "Morale", "Exercise torpedoes", "Depth reports"]:
        row = tk.Frame(sidebar, bg=PANEL, pady=5)
        row.pack(fill="x", padx=14)
        tk.Label(row, text=label, fg=MUTED, bg=PANEL, font=("Arial", 10)).pack(side="left")
        var = tk.StringVar()
        tk.Label(row, textvariable=var, fg=TEXT, bg=PANEL, font=("Consolas", 10, "bold")).pack(side="right")
        stat_vars[label] = var
    tk.Label(sidebar, text="SONAR / FICTITIOUS CONTACT PLOT", fg=MUTED, bg=PANEL, font=("Consolas", 9), pady=12).pack()
    sonar_canvas = tk.Canvas(sidebar, height=230, bg="#061c1c", highlightthickness=0)
    sonar_canvas.pack(fill="x", padx=12, pady=(0, 12))

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

    def redraw_sonar() -> None:
        sonar_canvas.delete("all")
        w = max(200, sonar_canvas.winfo_width())
        h = 230
        cx, cy = w / 2, h / 2
        for radius in [34, 67, 99]:
            sonar_canvas.create_oval(cx-radius, cy-radius, cx+radius, cy+radius, outline="#286150")
        sonar_canvas.create_line(cx, 12, cx, h-12, fill="#285a49")
        sonar_canvas.create_line(8, cy, w-8, cy, fill="#285a49")
        sonar_canvas.create_oval(cx-4, cy-4, cx+4, cy+4, fill=GREEN, outline="")
        sonar_canvas.create_text(cx+8, cy+13, text="RAZORBACK", fill=GREEN, anchor="w", font=("Consolas", 9))
        locations = [(cx+63,cy-54,"UNKNOWN"),(cx-72,cy+43,"CONTACT"),(cx+62,cy+60,"PATROL")]
        if game.s.phase == "extraction" and game.s.escape_progress > 70:
            locations = [(cx+62,cy-54,"FRIENDLY?"),(cx-72,cy+43,"SONAR")]
        for x,y,word in locations:
            sonar_canvas.create_line(cx,cy,x,y,fill="#a88446", dash=(4,5))
            sonar_canvas.create_oval(x-5,y-5,x+5,y+5,outline=GOLD)
            sonar_canvas.create_text(x, y-12, text=word, fill=GOLD, font=("Consolas",8))
        sonar_canvas.create_text(7,8,text="PASSIVE SONAR / NOT TO SCALE",fill=GREEN,anchor="nw",font=("Consolas",8))

    def refresh() -> None:
        s=game.s
        p=s.inbound_progress if s.phase=="infiltration" else s.escape_progress
        floor=game.water_depth()
        vals={
            "Current time":clock(s.elapsed), "Phase":s.phase.upper(),"Mission progress":f"{p:.0f}%",
            "Time remaining":f"{game.remaining()} min", "Hull integrity":f"{s.hull}%",
            "Battery":f"{s.battery:.0f}%", "Depth / seabed":f"{s.depth}/{floor} ft",
            "Under-keel":f"~{max(0,floor-s.depth-10)} ft" if not s.bottomed else "On seabed",
            "Speed":f"{s.speed:g} kt", "Stealth":s.detection.upper(),
            "Sonar confidence":f"{s.sonar_confidence}%", "Morale":f"{s.crew_morale}%",
            "Exercise torpedoes":f"{s.torpedoes}", "Depth reports":f"{s.report_interval} min" if s.report_interval else "OFF",
        }
        for label,var in stat_vars.items(): var.set(vals[label])
        phase_var.set(f"TURN {s.turn:02d}  |  {s.phase.upper()}  |  SEED {game.seed}")
        options=game.choices()
        for i,b in enumerate(choices_buttons):
            if i < len(options):
                c=options[i]
                b.configure(text=f"{c.key}. {c.title}  -  {c.summary}", command=lambda cmd=c.command: order(cmd), state="normal")
            else:
                b.configure(text="MISSION COMPLETE - Choose New Game",state="disabled")
        redraw_sonar()

    def order(value: Optional[str]=None) -> None:
        cmd=order_var.get().strip() if value is None else value
        if not cmd: return
        result=game.command(cmd)
        show_output(f"YOUR ORDER: {cmd.upper()}\n\n{result}")
        order_var.set("")
        refresh()
        order_entry.focus_set()

    tk.Button(bottom, text="ISSUE ORDER", command=order, bg="#16674e", fg="white", activebackground="#258963", relief="flat", bd=0, padx=14, pady=10, font=("Consolas",10,"bold")).pack(side="right", padx=(7,0))
    order_entry.bind("<Return>", lambda _: order())

    tools_frame = tk.Frame(center, bg=NAVY)
    tools_frame.pack(fill="x", padx=10, pady=(0, 8))
    def info(command: str) -> None: order(command)
    for label, cmd in [("Sonar","sonar"),("Depth","depth report"),("Chart","map"),("Fleet","fleet"),("Help","help")]:
        tk.Button(tools_frame,text=label,command=lambda c=cmd: info(c),bg=PANEL,fg=TEXT,activebackground="#23526b",relief="flat",padx=10,pady=6).pack(side="left",padx=(0,5))
    def do_save() -> None:
        path=filedialog.asksaveasfilename(title="Save Operation Rustbucket",initialfile="rustbucket_save.json",defaultextension=".json",filetypes=[("JSON save","*.json")])
        if path:
            try:
                game.save(Path(path))
                show_output("SAVE COMPLETE: " + path)
            except Exception as exc:
                messagebox.showerror("Save error",str(exc))
    def do_load() -> None:
        nonlocal game
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
        if not messagebox.askyesno("New game", "Start a new Operation Rustbucket mission?"):
            return
        game=Game(None, difficulty)
        narrative.configure(state="normal")
        narrative.delete("1.0","end")
        narrative.configure(state="disabled")
        show_output(game.opening())
        refresh()
    for label, action in [("Save",do_save),("Load",do_load),("New Game",new_game)]:
        tk.Button(tools_frame,text=label,command=action,bg="#21445a",fg=TEXT,relief="flat",padx=10,pady=6).pack(side="right",padx=(5,0))
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
    parser.add_argument("--demo",action="store_true",help="Run a noninteractive smoke-test mission")
    parser.add_argument("--seed",type=int,help="Set deterministic scenario seed")
    parser.add_argument("--difficulty",choices=["easy","normal","hard"],default="normal")
    args=parser.parse_args()
    if args.demo:
        demo()
        return
    if args.console:
        play_console(args.seed,args.difficulty)
        return
    try:
        launch_gui(args.seed,args.difficulty)
    except (ImportError, RuntimeError) as exc:
        print(f"Desktop UI unavailable ({exc}). Starting console mode.")
        play_console(args.seed,args.difficulty)
    except Exception as exc:
        # Only fall back when the display cannot be created; do not hide GUI bugs.
        if exc.__class__.__name__ == "TclError":
            print(f"No graphical desktop available ({exc}); starting console mode.")
            play_console(args.seed,args.difficulty)
        else:
            raise


if __name__ == "__main__":
    main()
