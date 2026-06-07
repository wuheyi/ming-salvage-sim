import unittest

from ming_sim.simulation import _clean_fiscal_changes


class FiscalChangeCleaningTests(unittest.TestCase):
    def setUp(self):
        self.cfg = {
            "宗室禄米_base": 120,
            "宗室禄米_rate": 55,
            "官俸_base": 25,
            "官俸_rate": 100,
        }

    def test_rejects_legacy_zongshi_delta_without_mode(self):
        cleaned = _clean_fiscal_changes([
            {"键": "宗室禄米_rate", "增量": -45, "原因": "旧式错误"}
        ], fiscal_config=self.cfg)

        self.assertEqual(cleaned, [])

    def test_keeps_set_amount_mode(self):
        cleaned = _clean_fiscal_changes([
            {"键": "宗室禄米_base", "口径": "月额设为", "数值": 30, "原因": "减至三十万"}
        ], fiscal_config=self.cfg)

        self.assertEqual(cleaned, [{
            "key": "宗室禄米_base",
            "reason": "减至三十万",
            "mode": "月额设为",
            "value": 30.0,
        }])

    def test_rejects_conflicting_target_and_actual_cut(self):
        cleaned = _clean_fiscal_changes([
            {
                "键": "宗室禄米_base",
                "口径": "月额设为",
                "数值": 30,
                "原因": "宗室禄米总额压至三十万两，但实减仅约二万两",
            }
        ], fiscal_config=self.cfg)

        self.assertEqual(cleaned, [])

    def test_keeps_consistent_target_and_actual_cut(self):
        cleaned = _clean_fiscal_changes([
            {
                "键": "宗室禄米_base",
                "口径": "月额设为",
                "数值": 30,
                "原因": "宗室禄米总额压至三十万两，实际减少三十六万两",
            }
        ], fiscal_config=self.cfg)

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned[0]["key"], "宗室禄米_base")
        self.assertEqual(cleaned[0]["mode"], "月额设为")
        self.assertEqual(cleaned[0]["value"], 30.0)


if __name__ == "__main__":
    unittest.main()
