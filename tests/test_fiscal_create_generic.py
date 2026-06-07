import unittest

from ming_sim.content import GameContent
from ming_sim.db import GameDB
from ming_sim.flows import compute_budget_lines
from ming_sim.issues import apply_score_extraction, bind_content
from ming_sim.models import GameState
from ming_sim.simulation import _clean_fiscal_creates


class FiscalCreateGenericTests(unittest.TestCase):
    def setUp(self):
        self.content = GameContent.load()
        bind_content(self.content)
        self.db = GameDB(":memory:", self.content)
        self.db.seed_static_data()
        self.state = GameState()

    def test_clean_accepts_chinese_income_direction(self):
        cleaned = _clean_fiscal_creates([
            {
                "键": "新设税目_base",
                "账户": "国库",
                "方向": "收",
                "显示名": "新设税目",
                "初值": 20,
                "原因": "新设月度税入",
            }
        ])

        self.assertEqual(cleaned, [{
            "key": "新设税目_base",
            "account": "国库",
            "direction": "income",
            "display": "新设税目",
            "init_value": 20,
            "reason": "新设月度税入",
        }])

    def test_created_fiscal_item_enters_fixed_budget_income(self):
        applied = apply_score_extraction(
            self.db,
            self.state,
            {
                "fiscal_creates": [
                    {
                        "key": "新设税目_base",
                        "account": "国库",
                        "direction": "income",
                        "display": "新设税目",
                        "init_value": 20,
                        "reason": "新设月度税入",
                    }
                ]
            },
            content=self.content,
        )

        cfg = self.db.get_fiscal_config()
        self.assertEqual(applied["fiscal_creates"][0]["key"], "新设税目_base")
        self.assertEqual(cfg["新设税目_base"], 20)
        self.assertEqual(cfg["新设税目_rate"], 100)

        budget = compute_budget_lines(self.db, self.state)
        created = [
            item for item in budget["国库"]["income"]
            if item["name"] == "新设税目"
        ]
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0]["amount"], 20)
        self.assertEqual(created[0]["base"], 20)
        self.assertEqual(created[0]["rate"], 100)

    def test_created_poll_tax_follows_population_basis(self):
        apply_score_extraction(
            self.db,
            self.state,
            {
                "fiscal_creates": [
                    {
                        "key": "人头新税_base",
                        "account": "国库",
                        "direction": "income",
                        "display": "人头新税",
                        "init_value": 1200,
                        "formula": "per_basis",
                        "basis": "population",
                        "rate_unit": "毫/人/年",
                        "reason": "按人丁岁征",
                    }
                ]
            },
            content=self.content,
        )

        def amount() -> int:
            budget = compute_budget_lines(self.db, self.state)
            return [
                item for item in budget["国库"]["income"]
                if item["name"] == "人头新税"
            ][0]["amount"]

        before = amount()
        self.db.conn.execute("UPDATE regions SET population = population + 100 WHERE id = 'beizhili'")
        self.db.conn.commit()
        self.assertEqual(amount(), before + 1)

    def test_created_land_tax_follows_guan_min_tian_basis(self):
        apply_score_extraction(
            self.db,
            self.state,
            {
                "fiscal_creates": [
                    {
                        "key": "田亩新税_base",
                        "account": "国库",
                        "direction": "income",
                        "display": "田亩新税",
                        "init_value": 1200,
                        "formula": "per_basis",
                        "basis": "guan_min_tian",
                        "rate_unit": "毫/亩/年",
                        "reason": "按官民田亩岁征",
                    }
                ]
            },
            content=self.content,
        )

        def amount() -> int:
            budget = compute_budget_lines(self.db, self.state)
            return [
                item for item in budget["国库"]["income"]
                if item["name"] == "田亩新税"
            ][0]["amount"]

        before = amount()
        row = self.db.conn.execute("SELECT fiscal FROM regions WHERE id = 'beizhili'").fetchone()
        import json
        fiscal = json.loads(row["fiscal"])
        fiscal["guan_min_tian"] = int(fiscal.get("guan_min_tian", 0)) + 100
        self.db.conn.execute(
            "UPDATE regions SET fiscal = ? WHERE id = 'beizhili'",
            (json.dumps(fiscal, ensure_ascii=False),),
        )
        self.db.conn.commit()
        self.assertEqual(amount(), before + 1)


if __name__ == "__main__":
    unittest.main()
