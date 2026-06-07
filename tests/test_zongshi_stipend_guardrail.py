import unittest

from ming_sim.content import GameContent
from ming_sim.db import GameDB
from ming_sim.issues import apply_score_extraction, bind_content
from ming_sim.models import GameState


class ZongshiStipendFiscalModeTests(unittest.TestCase):
    def setUp(self):
        self.content = GameContent.load()
        bind_content(self.content)
        self.db = GameDB(":memory:", self.content)
        self.db.seed_static_data()
        self.state = GameState()

    def test_set_amount_recomputes_rate_from_current_database_values(self):
        applied = apply_score_extraction(
            self.db,
            self.state,
            {
                "fiscal_changes": [
                    {
                        "key": "宗室禄米_base",
                        "mode": "set_amount",
                        "value": 30,
                        "reason": "宗室禄米总额减至每月三十万两",
                    }
                ]
            },
            content=self.content,
        )

        cfg = self.db.get_fiscal_config()
        self.assertEqual(cfg["宗室禄米_base"], 120)
        self.assertEqual(cfg["宗室禄米_rate"], 25)
        self.assertEqual(round(cfg["宗室禄米_base"] * cfg["宗室禄米_rate"] / 100), 30)
        self.assertEqual(applied["fiscal_changes"][0]["mode"], "set_amount")
        self.assertEqual(applied["fiscal_changes"][0]["old_amount"], 66)
        self.assertEqual(applied["fiscal_changes"][0]["new_amount"], 30)
        self.assertLess(self.db.faction_satisfaction("宗室"), 45)
        row = self.db.conn.execute(
            "SELECT satisfaction, leverage FROM classes WHERE name='宗藩' AND region_id=''"
        ).fetchone()
        self.assertLess(row["satisfaction"], 55)
        self.assertGreater(row["leverage"], 50)

    def test_scale_amount_applies_percentage_to_monthly_amount_not_raw_rate(self):
        applied = apply_score_extraction(
            self.db,
            self.state,
            {
                "fiscal_changes": [
                    {
                        "key": "宗室禄米_base",
                        "mode": "scale_amount",
                        "value": -30,
                        "reason": "削周王禄米三成",
                    }
                ]
            },
            content=self.content,
        )

        cfg = self.db.get_fiscal_config()
        self.assertEqual(cfg["宗室禄米_base"], 120)
        self.assertEqual(cfg["宗室禄米_rate"], 38)
        self.assertEqual(round(cfg["宗室禄米_base"] * cfg["宗室禄米_rate"] / 100), 46)
        self.assertEqual(applied["fiscal_changes"][0]["mode"], "scale_amount")
        self.assertEqual(applied["fiscal_changes"][0]["old_amount"], 66)
        self.assertEqual(applied["fiscal_changes"][0]["new_amount"], 46)
        self.assertLess(self.db.faction_satisfaction("宗室"), 45)


if __name__ == "__main__":
    unittest.main()
