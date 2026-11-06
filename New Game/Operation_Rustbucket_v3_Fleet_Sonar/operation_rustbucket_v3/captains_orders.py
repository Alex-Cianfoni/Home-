"""Interpret natural-language captain's orders into bounded simulation actions.

Offline interpretation is deterministic and intentionally imperfect. Optional
cloud AI can produce the same OrderPlan schema for more open-ended phrasing.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

VALID_ACTIONS = {
    "none", "cruise", "silent", "advance", "speed", "wait", "analyze",
    "bottom", "depart", "depth", "alternate", "radio", "transmit",
    "fire", "inspect", "repair", "periscope", "talk", "ping",
}
VALID_READOUTS = {"sonar", "environment", "status", "fleet", "map"}


@dataclass
class OrderPlan:
    action: str = "none"
    argument: Optional[float] = None
    depth_ft: Optional[int] = None
    speed_knots: Optional[float] = None
    heading_deg: Optional[int] = None
    report_interval_min: Optional[int] = None
    disable_reports: bool = False
    readouts: List[str] = field(default_factory=list)
    vintage_id: bool = False
    topic: str = ""
    acknowledgement: str = ""

    def validate(self) -> str:
        if self.action not in VALID_ACTIONS:
            return "Unsupported action."
        if self.depth_ft is not None and not 0 <= self.depth_ft <= 2000:
            return "Depth must be in feet and within the simulation's valid range."
        if self.speed_knots is not None and not 0 <= self.speed_knots <= 15:
            return "Speed must be between 0 and 15 knots for the supported roster."
        if self.heading_deg is not None and not 0 <= self.heading_deg <= 359:
            return "Heading must be between 000 and 359 degrees true."
        if self.report_interval_min is not None and not 5 <= self.report_interval_min <= 120:
            return "Scheduled reports must be between 5 and 120 minutes."
        if not set(self.readouts).issubset(VALID_READOUTS):
            return "Unknown requested report."
        return ""


def parse_offline(raw: str, *, layer_low: int = 120, layer_high: int = 145) -> OrderPlan:
    """Best-effort interpretation of unstructured English without networking.

    Patterns search the *whole* order rather than splitting on 'and', so a
    multi-part sentence can combine a depth, heading, speed, report schedule,
    and one time-advancing activity in a single turn.
    """
    original = raw.strip()
    s = re.sub(r"\s+", " ", original.lower().replace("’", "'")).strip()
    p = OrderPlan(topic=original[:250])
    if not s:
        return p

    # Read-only requests: distinguish observing a layer from entering it.
    if re.search(r"\b(?:sonar|contacts?|acoustic|bearing)\b", s) and re.search(
        r"\b(?:check|report|show|display|identify|tell|scan|monitor|listen|review|analy[sz]e|track)\b", s):
        p.readouts.append("sonar")
    if re.search(r"\b(?:depth|bottom clearance|seabed|water depth|thermal|thermocline|temperature profile|layer)\b", s) and re.search(
        r"\b(?:check|report|show|display|what|how|read|review|tell|monitor)\b", s):
        p.readouts.append("environment")
    if re.search(r"\b(?:status|battery|hull|readiness|how much fuel|time left|mission progress)\b", s):
        if re.search(r"\b(?:check|report|show|display|what|how|read|tell|give|status)\b", s):
            p.readouts.append("status")
    if re.search(r"\b(?:map|chart|position|location)\b", s) and re.search(r"\b(?:check|show|display|open|view|where|review)\b", s):
        p.readouts.append("map")
    if re.search(r"\b(?:fleet|allies|alliance ships)\b", s) and re.search(r"\b(?:check|show|report|display|list|what)\b", s):
        p.readouts.append("fleet")
    if re.fullmatch(r"\s*(?:sonar|contacts|passive sonar)\s*", s):
        p.readouts = ["sonar"]
    elif re.fullmatch(r"\s*(?:depth report|environment|thermal report|check depth|check thermal layer)\s*", s):
        p.readouts = ["environment"]
    elif re.fullmatch(r"\s*(?:status|st)\s*", s):
        p.readouts = ["status"]
    elif re.fullmatch(r"\s*(?:map|chart)\s*", s):
        p.readouts = ["map"]
    elif re.fullmatch(r"\s*(?:fleet|allies)\s*", s):
        p.readouts = ["fleet"]

    if re.search(r"\b(?:cancel|disable|stop|turn off|no more)\b.{0,32}\b(?:reports?|checks?|interval)\b", s) or "report off" in s:
        p.disable_reports = True
    interval = re.search(r"\b(?:report|reports|reporting|check|checks|checking|monitor|depth readings?)\b.{0,32}?\b(?:every|each|at intervals of|interval(?: of)?)\s*(\d+)\s*(?:min(?:ute)?s?|m)\b", s)
    if not interval:
        interval = re.search(r"\b(?:every|each)\s*(\d+)\s*(?:min(?:ute)?s?|m)\b.{0,35}\b(?:check|report|depth|environment|reading)", s)
    if not interval:
        interval = re.search(r"\b(?:report|reports|check depth)\s+(\d+)\s*(?:min(?:ute)?s?|m)?\b", s)
    if interval:
        p.report_interval_min = int(interval.group(1))
        p.disable_reports = False
        # 'check depth every 30 minutes' schedules checks, not an immediate readout.
        if "now" not in s and "immediately" not in s:
            p.readouts = [r for r in p.readouts if r != "environment"]

    heading = re.search(r"\b(?:heading|course|steer|turn to|come to|set course(?: to)?|make your heading)\s*(?:of|to|is|at|true)?\s*(\d{1,3})(?:\s*(?:degrees?|°|t|true))?\b", s)
    if heading:
        p.heading_deg = int(heading.group(1))

    speed = re.search(r"\b(?:speed|make|set speed(?: to)?|at|to|maintain|hold)\s*(?:of|to|is)?\s*(\d+(?:\.\d+)?)\s*(?:knots?|kts?|kt)\b", s)
    if not speed:
        speed = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:knots?|kts?|kt)\b", s)
    if not speed:
        speed = re.fullmatch(r"(?:speed|set speed|make speed)\s+(?:to\s+)?(\d+(?:\.\d+)?)", s)
    if speed:
        p.speed_knots = float(speed.group(1))
    elif "two knots" in s:
        p.speed_knots = 2.0
    elif "three knots" in s:
        p.speed_knots = 3.0

    explicit_depth = re.search(r"\b(?:depth|dive|descend|ascend|rise|surface|come up|take (?:her|us)|bring (?:her|us)|level off)\s*(?:to|at|of|down to|up to|the boat to)?\s*(\d{2,3})\s*(?:ft|feet|foot)?\b", s)
    if explicit_depth:
        p.depth_ft = int(explicit_depth.group(1))
    elif s in {"thermal", "thermocline"} or re.search(r"\b(?:enter|go into|dive into|descend into|move into|take .* into|hide .* in)\b.{0,20}\b(?:thermal|thermocline|temperature)\b", s):
        p.depth_ft = round((layer_low + layer_high) / 2)
    elif re.search(r"\b(?:go|move|rise|come|stay)\s+above\s+(?:the\s+)?(?:thermal|layer)\b", s):
        p.depth_ft = max(25, layer_low - 20)
    elif re.search(r"\b(?:go|move|dive|descend|stay)\s+below\s+(?:the\s+)?(?:thermal|layer)\b", s):
        p.depth_ft = layer_high + 15

    if "1944" in s or "morse" in s or "vintage" in s or "world war ii identification" in s:
        p.vintage_id = True

    # Priority matters: 'go silent and then transmit' should transmit, whereas
    # 'transmit readiness to XO' is *not* the objective marker.
    marker_context = bool(re.search(r"\b(?:marker|objective|identification|id(?:ent)?|mission accomplished|challenge|1944|morse|transmission)\b", s))
    if re.search(r"\b(?:active sonar|active ping|ping sonar|ping now|send (?:a )?ping)\b", s) or s in {"ping", "active"}:
        p.action = "ping"
    elif (re.search(r"\b(?:transmit|send|broadcast|signal|radio out)\b", s) and marker_context) or re.fullmatch(r"(?:transmit(?:\s+1944)?|marker|send marker|1944|morse|vintage)", s):
        p.action = "transmit"
    elif re.search(r"\b(?:settle|lay|lie|land|rest)\b.{0,28}\b(?:bottom|seabed|sea floor|ocean floor)\b", s) or re.fullmatch(r"bottom|seabed", s):
        p.action = "bottom"
    elif re.search(r"\b(?:depart|leave|lift off|rise off|push off|get off)\b.{0,28}\b(?:bottom|seabed|sea floor)\b", s) or s == "depart":
        p.action = "depart"
    elif re.search(r"\b(?:fire|launch|shoot)\b.{0,24}\b(?:torpedo|weapon|exercise)\b", s) or s == "fire":
        p.action = "fire"
    elif re.search(r"\b(?:alternate|reroute|different extraction|deeper.water route)\b", s):
        p.action = "alternate"
    elif re.search(r"\b(?:periscope|raise scope|look outside|look through scope)\b", s) and not re.search(r"\b(?:check depth|report|show status)\b", s):
        p.action = "periscope"
    elif re.search(r"\b(?:repair|fix|diagnos|maintenance|inspect engine|check (?:the )?engine|check (?:the )?battery|inspect damage)\b", s):
        p.action = "repair"
    elif re.search(r"\b(?:ask|contact|call|message|request|communicate|coordinate|hail)\b.{0,45}\b(?:midway|becuna|exercise control|controller|fleet command|new jersey|clearance|permission|traffic|safety)\b", s) or s == "radio":
        p.action = "radio"
    elif s in {"listen", "passive", "passive sonar", "listen for contacts"} or re.search(r"\b(?:listen|analy[sz]e|classify|identify|track)\b.{0,40}\b(?:contact|sonar|noise|submarine|patrol|signal)\b", s) and not re.search(r"\b(?:proceed|continue|withdraw|move|advance|head|steer|cruise)\b", s):
        p.action = "analyze"
    elif re.search(r"\b(?:hold(?: position| station)?|wait|stop|remain stationary|stay still|all stop|engines off|shut down propulsion|turn off engines)\b", s) and p.speed_knots is None and not re.search(r"\b(?:continue|proceed|withdraw|move|advance|keep going)\b", s):
        p.action = "wait"
    elif re.search(r"\b(?:silent|silent running|run silent|go silent|quiet running|rig for silent|silent withdrawal|silently)\b", s):
        p.action = "silent" if p.speed_knots is None else "cruise"
    elif s == "advance":
        p.action = "advance"
    elif re.search(r"\b(?:full ahead|increase speed|make best speed|rush|faster|accelerate)\b", s):
        p.action = "speed"
        p.speed_knots = p.speed_knots if p.speed_knots is not None else 5.0
    elif re.search(r"\b(?:proceed|continue|maintain course|present course|keep going|keep moving|advance|withdraw|exit|head|move|cruise|sail|navigate)\b", s):
        p.action = "cruise"
    elif p.speed_knots is not None:
        p.action = "speed" if s.startswith(("speed", "set speed", "make speed")) else "cruise"
    elif p.depth_ft is not None:
        p.action = "depth"
    elif p.heading_deg is not None:
        p.action = "cruise" if re.search(r"\b(?:turn|steer|proceed)\b", s) else "none"
    elif re.search(r"\b(?:ask|tell|discuss|speak|talk|question|brief|explain)\b", s):
        p.action = "talk"
    elif re.search(r"\b(?:inspect|investigate|review|search|evaluate|assess)\b", s):
        p.action = "inspect"

    # Mere questions and status checks should be free, unlike an underway order.
    if re.match(r"^(?:what|where|when|who|how|why|is|are|do|does|tell me|show me|give me)\b", s) and p.readouts and p.action not in {"transmit", "radio"}:
        p.action = "none"
    if p.action == "none" and not (p.readouts or p.report_interval_min or p.disable_reports or p.heading_deg is not None):
        p.action = "talk" if re.search(r"\b(?:crew|xo|chief|captain|sonar|navigator|officer|coffee|plan|opinion)\b", s) else "inspect"

    return p
