import tempfile
import unittest
from pathlib import Path
from captains_orders import parse_offline
from operation_rustbucket import Game
from submarine_catalog import SUBMARINES, groups, select_submarine


class NewFeatures(unittest.TestCase):
    def test_fleet_selection_and_unique_ids(self):
        self.assertGreaterEqual(len(SUBMARINES), 125)
        self.assertEqual(len(SUBMARINES), len({s.id for s in SUBMARINES.values()}))
        self.assertEqual(select_submarine("razorback").country, "United States")
        self.assertEqual(select_submarine("Type XXI").country, "Germany")
        self.assertIn("GUPPY conversions", groups())
        self.assertIn("Japanese WWII", groups())

    def test_different_boats_have_real_gameplay_stats(self):
        g = Game(seed=19, submarine="Type XXI")
        self.assertEqual(g.sub.name, "Type XXI")
        self.assertEqual(g.s.battery, 97)
        self.assertEqual(g.s.torpedoes, 12)
        self.assertIn("Type XXI", g.status_text())
        self.assertEqual(g.command("speed 13"), "HELM: Maximum exercise speed for Type XXI is 12 kt. No order executed.")
        self.assertEqual(g.s.turn, 0)

    def test_sonar_tracks_are_really_moving(self):
        g = Game(seed=28)
        start = [(c.key, c.east, c.north) for c in g.sonar_world.contacts]
        g.command("silent")
        self.assertGreater(g.s.pos_east, 0)
        moved = [(c.key, c.east, c.north) for c in g.sonar_world.contacts]
        self.assertNotEqual(start, moved)
        self.assertGreater(len(g.sonar_world.observed()), 0)
        self.assertIn(" nm", g.sonar_report())

    def test_active_ping_advances_and_alters_contacts(self):
        g = Game(seed=20)
        before = sum(c.confidence for c in g.sonar_world.contacts)
        before_suspicion = g.s.suspicion
        result = g.command("send an active ping")
        self.assertIn("ACTIVE PING", result)
        self.assertEqual(g.s.turn, 1)
        self.assertEqual(g.s.sonar_mode, "active")
        self.assertGreater(g.s.suspicion, before_suspicion)
        self.assertGreater(sum(c.confidence for c in g.sonar_world.contacts), before)
        g.command("continue present course")
        self.assertEqual(g.s.sonar_mode, "passive")

    def test_sonar_report_only_returns_observed(self):
        g = Game(seed=42)
        for c in g.sonar_world.contacts:
            c.confidence = 0
        self.assertIn("No usable tracks", g.sonar_report())
        for c in g.sonar_world.contacts:
            c.confidence = 80
            c.last_seen = -10000
        self.assertIn("No usable tracks", g.sonar_report())

    def test_torpedo_requires_valid_sonar_track(self):
        g = Game(seed=41)
        out = g.command("fire torpedo")
        self.assertIn("launch denied", out)
        self.assertEqual(g.s.turn,0)
        self.assertEqual(g.s.torpedoes,10)
        c=next(c for c in g.sonar_world.contacts if c.side == 'blue')
        c.confidence=90
        c.last_seen=g.s.elapsed
        c.measured_range=2
        out=g.command("fire torpedo")
        self.assertIn("inert exercise torpedo",out)
        self.assertEqual(g.s.torpedoes,9)

    def test_sonar_state_save_load_replay(self):
        g=Game(seed=44, submarine="HMAS Onslow")
        g.command("listen")
        g.command("ping")
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/"save.json"
            g.save(path)
            restored=Game.load(path)
        self.assertEqual(g.s,restored.s)
        self.assertEqual(g.sub,restored.sub)
        self.assertEqual(g.sonar_world.serialize(),restored.sonar_world.serialize())
        self.assertEqual(g.command("silent"),restored.command("silent"))
        self.assertEqual(g.sonar_world.serialize(),restored.sonar_world.serialize())

    def test_old_game_save_compat(self):
        g=Game(seed=11)
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/"old.json"
            g.save(path)
            import json
            raw=json.loads(path.read_text())
            raw["version"]="2.0"
            raw.pop("contacts")
            for k in ["submarine_id", "pos_east", "pos_north", "sonar_mode"]:
                raw['state'].pop(k,None)
            path.write_text(json.dumps(raw))
            restored=Game.load(path)
        self.assertEqual(restored.sub.id,"razorback")

    def test_offline_sonar_phrase(self):
        self.assertEqual(parse_offline("listen").action,"analyze")
        self.assertEqual(parse_offline("active ping").action,"ping")
        self.assertEqual(parse_offline("continue heading 090 at 2 knots").action,"cruise")


if __name__ == "__main__":
    unittest.main(verbosity=2)
