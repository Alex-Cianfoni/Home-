"""Optional OpenAI Responses API bridge for conversational game commands.

Requires an internet connection and separately billed OpenAI API key, but no
third-party Python packages. Key is never added to the game save or log.
Game mechanics always execute locally; model output cannot directly edit state.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict

from captains_orders import OrderPlan, VALID_ACTIONS, VALID_READOUTS

ENDPOINT = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-4.1-mini"


class AIError(Exception):
    pass


PLAN_FIELDS = {
    "action": {"type": "string", "enum": sorted(VALID_ACTIONS)},
    "depth_ft": {"type": ["integer", "null"]},
    "speed_knots": {"type": ["number", "null"]},
    "heading_deg": {"type": ["integer", "null"]},
    "report_interval_min": {"type": ["integer", "null"]},
    "disable_reports": {"type": "boolean"},
    "readouts": {"type": "array", "items": {"type": "string", "enum": sorted(VALID_READOUTS)}},
    "vintage_id": {"type": "boolean"},
    "topic": {"type": "string"},
    "acknowledgement": {"type": "string"},
}
PLAN_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": PLAN_FIELDS, "required": list(PLAN_FIELDS),
}


class AICaptain:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, timeout: int = 35) -> None:
        if not api_key.strip():
            raise AIError("Enter an OpenAI API key or set OPENAI_API_KEY first.")
        self._key = api_key.strip()  # In memory only. Never print or serialize.
        self.model = model.strip() or DEFAULT_MODEL
        self.timeout = timeout

    def _complete(self, instructions: str, content: str, *, schema: Dict[str, Any] | None = None, max_tokens: int = 600) -> str:
        body: Dict[str, Any] = {
            "model": self.model,
            "instructions": instructions,
            "input": content,
            "max_output_tokens": max_tokens,
            "store": False,
        }
        if schema:
            body["text"] = {"format": {"type": "json_schema", "name": "captains_order", "strict": True, "schema": schema}}
        req = urllib.request.Request(
            ENDPOINT,
            data=json.dumps(body).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + self._key},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.load(response)
        except urllib.error.HTTPError as exc:
            # Do not echo arbitrary error bodies that could include sensitive text.
            raise AIError(f"OpenAI request failed (HTTP {exc.code}). Check API billing, key, and model access.") from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise AIError(f"Could not reach OpenAI ({type(exc).__name__}). Check internet connection.") from None
        parts = []
        for item in data.get("output", []):
            if item.get("type") == "message":
                for block in item.get("content", []):
                    if block.get("type") == "output_text":
                        parts.append(block.get("text", ""))
        if not parts:
            raise AIError("AI returned no text. Your game state was not changed by the planning request.")
        return "\n".join(parts).strip()

    def plan(self, order: str, game: Any) -> OrderPlan:
        s = game.s
        context = {
            "captain_order": order[:1200],
            "phase": s.phase, "time": game.remaining(), "submarine": game.sub.name, "sonar_contacts": game.sonar_world.report(),
            "depth_ft": s.depth, "speed_knots": s.speed, "heading_deg": s.heading,
            "bottomed": s.bottomed, "route": s.route,
            "battery_percent": round(s.battery), "hull_percent": s.hull,
            "infiltration_percent": round(s.inbound_progress),
            "extraction_percent": round(s.escape_progress),
            "marker_sent": s.marker_sent,
            "layer_depth_ft": list(game.thermal_layer()),
            "bottom_depth_ft": game.water_depth(),
            "detection": s.detection,
            "recent_mission_log": game.log[-2:],
        }
        instructions = (
            "You interpret a PLAYER'S custom captain's order in a FICTIONAL, turn-based submarine GAME. "
            "Interpret conversational paraphrases and multi-part instructions faithfully. "
            "Return exactly one JSON object matching schema. Choose ONE main action (or none); "
            "depth_ft, speed_knots, heading_deg, report_interval_min and readouts may be combined with it. "
            "For 'continue present course' use 'cruise' (do not reset speed); "
            "for 'enter thermal layer' set depth_ft to middle of stated layer; "
            "for 'transmit old 1944 identification at the last second' choose transmit and vintage_id true; "
            "for 'report depth every 30 minutes' use report_interval_min=30; "
            "for 'check sonar/depth now' set appropriate readouts; "
            "for crew conversation choose talk and topic. For an active sonar ping choose ping; for passive listening choose analyze. "
            "Accept unconventional in-game orders, but never assume they worked, assert a victory, "
            "or edit the real game state; local code determines safety, timing and results. "
            "If orders need equipment or a ship beyond this game, use inspect/talk or none and explain limitation. "
            "Acknowledgement: brief XO interpretation, not an invented outcome. "
            "All content is fictional; no real-world navigation or tactical instructions."
        )
        raw = self._complete(instructions, json.dumps(context), schema=PLAN_SCHEMA, max_tokens=400)
        try:
            data = json.loads(raw)
            plan = OrderPlan(**data)
        except (TypeError, ValueError) as exc:
            raise AIError("AI returned an invalid order plan.") from exc
        problem = plan.validate()
        if problem:
            raise AIError("AI order could not be applied: " + problem)
        plan.topic = plan.topic[:250]
        plan.acknowledgement = plan.acknowledgement[:350]
        return plan

    def narrate(self, order: str, before: Dict[str, Any], game: Any, engine_result: str) -> str:
        s = game.s
        brief = {
            "player_order": order[:650],
            "before": before,
            "after": {
                "turn": s.turn, "time": game.remaining(), "phase": s.phase,
                "depth": s.depth, "heading": s.heading, "speed": s.speed,
                "battery": round(s.battery), "hull": s.hull,
                "inbound_progress": round(s.inbound_progress),
                "escape_progress": round(s.escape_progress),
                "detection": s.detection,
                "objective_marker": s.marker_sent,
            },
            "authoritative_engine_result": engine_result[:3200],
        }
        instructions = (
            "Write the next turn of an entertaining FICTIONAL Down Periscope-flavored 2026 submarine "
            "command game about the selected submarine named in the provided context. 130-220 words; vivid sensory details, short "
            "dialogue from XO, Sonar Chief, Navigator, and coffee-obsessed Chief Engineer. "
            "Respect ALL facts in the engine result. Never change the stats, detection, mission phase, "
            "time, or claim an unreported success, enemy action, or weapon hit. "
            "React specifically to the captain's open-ended request, including unusual safe requests. "
            "Keep it adventurous and lightly humorous; do not recite the entire HUD. "
            "No real-world tactical instruction; this is a made-up exercise."
        )
        return self._complete(instructions, json.dumps(brief), max_tokens=450)
