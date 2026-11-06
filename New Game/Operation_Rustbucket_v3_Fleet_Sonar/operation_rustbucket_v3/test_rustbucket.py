import tempfile
import unittest
from pathlib import Path
from operation_rustbucket import Game, GameState, DEADLINE_MINUTES


class RustbucketTests(unittest.TestCase):
    def test_start_and_choices(self):
        g = Game(seed=11)
        self.assertEqual(len(g.choices()), 3)
        self.assertEqual(g.s.battery, 94)
        self.assertEqual(g.s.depth, 90)
        self.assertEqual(g.s.phase, "infiltration")
        self.assertIn("273-vessel", g.opening())

    def test_silent_advances_and_uses_battery(self):
        g = Game(seed=22)
        t = g.s.elapsed
        g.command("A")
        self.assertGreater(g.s.elapsed, t)
        self.assertGreater(g.s.inbound_progress, 0)
        self.assertLess(g.s.battery, 94)
        self.assertEqual(g.s.speed, 2)
        self.assertTrue(g.s.silent_running)

    def test_reports_and_compound_thermal_order(self):
        g = Game(seed=33)
        report = g.command("go into the thermal layer and check depth every 30 mins and continue on present course")
        self.assertIn("depth", report.lower())
        self.assertEqual(g.s.depth, 132)
        self.assertEqual(g.s.report_interval, 30)
        self.assertEqual(g.s.turn, 1)
        self.assertGreater(g.s.inbound_progress, 0)
        for _ in range(3):
            g.command("silent")
        self.assertIn("SCHEDULED REPORT", "\n".join(g.log))

    def test_unsafe_depth_rejected_without_turn(self):
        g = Game(seed=44)
        response = g.command("depth 999")
        self.assertIn("not cleared", response)
        self.assertEqual(g.s.turn, 0)
        self.assertEqual(g.s.depth, 90)

    def test_bottom_and_depart(self):
        g = Game(seed=55)
        g.command("bottom")
        self.assertTrue(g.s.bottomed)
        self.assertEqual(g.s.speed, 0)
        self.assertEqual(len(g.choices()), 3)
        g.command("depart")
        self.assertFalse(g.s.bottomed)
        self.assertEqual(g.s.depth, 90)

    def test_vintage_marker_and_success(self):
        g = Game(seed=1944, difficulty="easy")
        for i in range(35):
            if g.s.inbound_progress >= 95:
                break
            g.command("silent")
        self.assertGreaterEqual(g.s.inbound_progress, 95)
        g.command("transmit 1944")
        self.assertTrue(g.s.vintage_radio)
        self.assertTrue(g.s.marker_sent)
        self.assertEqual(g.s.phase,"extraction")
        for i in range(35):
            if g.s.phase in ("success", "failure"):
                break
            if g.water_depth() - g.s.depth - 10 < 35:
                g.command("depth 70")
            else:
                g.command("silent")
        self.assertEqual(g.s.phase, "success")
        self.assertGreaterEqual(g.s.score, 60)

    def test_save_load_rng_replay(self):
        g = Game(seed=66)
        g.command("silent")
        g.command("report 30")
        with tempfile.TemporaryDirectory() as folder:
            savefile = Path(folder)/"state.json"
            g.save(savefile)
            restored = Game.load(savefile)
        self.assertEqual(g.s, restored.s)
        self.assertEqual(g.rng.getstate(),restored.rng.getstate())
        self.assertEqual(g.command("silent"),restored.command("silent"))
        self.assertEqual(g.s, restored.s)

    def test_no_win_after_deadline(self):
        g = Game(seed=99)
        g.s.phase = "extraction"
        g.s.marker_sent = True
        g.s.escape_progress = 99
        g.s.elapsed = DEADLINE_MINUTES - 1
        g.command("silent")
        self.assertEqual(g.s.phase,"failure")


if __name__ == "__main__":
    unittest.main(verbosity=2)
