import json
import unittest

from ming_sim.content import GameContent
from ming_sim.db import GameDB
from ming_sim.flows import (
    apply_annual_grain_flows,
    apply_annual_population_flows,
    apply_fixed_period_flows,
    calc_province_fiscal,
    compute_budget_lines,
)
from ming_sim.issues import apply_score_extraction, bind_content
from ming_sim.models import Event


class EconomyFieldCoverageTests(unittest.TestCase):
    def setUp(self):
        self.content = GameContent.load()
        bind_content(self.content)
        self.db = GameDB(":memory:", self.content)
        self.db.seed_static_data()
        self.state = self.db.load_state()
        self.event = Event(
            id="economy_field_coverage",
            title="经济字段覆盖",
            kind="测试",
            summary="",
            urgency=0,
            severity=0,
            credibility=100,
            interests=[],
            audiences=[],
        )

    def _set_region_for_exact_tax_math(self, region_id="beizhili"):
        fiscal = {
            "guan_min_tian": 12000,
            "wang_tian": 0,
            "huang_tian": 12000,
            "tian_fu_li": 1000,
            "liao_xiang_li": 1000,
            "salt_tax": 120,
            "commerce_tax": 60,
            "corruption": 0,
            "grain_output": 1000,
            "grain_stock": 500,
        }
        for row in self.db.conn.execute("SELECT id, fiscal FROM regions").fetchall():
            other = json.loads(row["fiscal"] or "{}")
            other["huang_tian"] = 0
            self.db.conn.execute(
                "UPDATE regions SET fiscal = ? WHERE id = ?",
                (json.dumps(other, ensure_ascii=False), row["id"]),
            )
        self.db.conn.execute(
            """
            UPDATE regions
            SET fiscal = ?, gentry_resistance = 0, unrest = 0
            WHERE id = ?
            """,
            (json.dumps(fiscal, ensure_ascii=False), region_id),
        )
        self.db.conn.commit()
        self.state.metrics["皇威"] = 100
        self.db.set_fiscal_config("皇庄亩率_base", 1000)
        self.db.set_fiscal_config("皇庄_rate", 50)
        return fiscal

    def _province_detail(self, region_id="beizhili"):
        _, _, details = calc_province_fiscal(self.state, self.db)
        return next(row for row in details if row["region_id"] == region_id)

    def test_core_tax_formula_fields_are_all_live(self):
        fiscal = self._set_region_for_exact_tax_math()

        detail = self._province_detail()
        self.assertEqual(detail["田赋账面"], 100)
        self.assertEqual(detail["田赋"], 100)
        self.assertEqual(detail["辽饷"], 100)
        self.assertEqual(detail["盐税"], 120)
        self.assertEqual(detail["商税"], 60)
        self.assertEqual(detail["皇庄"], 100)

        budget = compute_budget_lines(self.db, self.state)
        huang = [item for item in budget["内库"]["income"] if item["name"] == "皇庄"][0]
        self.assertEqual(huang["amount"], 50)

        fiscal["guan_min_tian"] += 1200
        self.db.conn.execute(
            "UPDATE regions SET fiscal = ? WHERE id = 'beizhili'",
            (json.dumps(fiscal, ensure_ascii=False),),
        )
        self.db.conn.commit()
        detail = self._province_detail()
        self.assertEqual(detail["田赋账面"], 110)
        self.assertEqual(detail["田赋"], 110)
        self.assertEqual(detail["辽饷"], 110)

        fiscal["tian_fu_li"] = 0
        fiscal["liao_xiang_li"] = 0
        fiscal["salt_tax"] = 0
        fiscal["commerce_tax"] = 0
        fiscal["huang_tian"] = 0
        self.db.conn.execute(
            "UPDATE regions SET fiscal = ? WHERE id = 'beizhili'",
            (json.dumps(fiscal, ensure_ascii=False),),
        )
        self.db.conn.commit()
        detail = self._province_detail()
        self.assertEqual(detail["田赋"], 0)
        self.assertEqual(detail["辽饷"], 0)
        self.assertEqual(detail["盐税"], 0)
        self.assertEqual(detail["商税"], 0)
        self.assertEqual(detail["皇庄"], 0)

    def test_collection_pressure_fields_affect_tax_receipts(self):
        self._set_region_for_exact_tax_math()
        before = self._province_detail()
        self.assertEqual(before["efficiency"], 1.0)

        self.db.conn.execute(
            """
            UPDATE regions
            SET gentry_resistance = 100, unrest = 100
            WHERE id = 'beizhili'
            """
        )
        row = self.db.conn.execute("SELECT fiscal FROM regions WHERE id = 'beizhili'").fetchone()
        fiscal = json.loads(row["fiscal"])
        fiscal["corruption"] = 100
        self.db.conn.execute(
            "UPDATE regions SET fiscal = ? WHERE id = 'beizhili'",
            (json.dumps(fiscal, ensure_ascii=False),),
        )
        self.db.conn.commit()

        after = self._province_detail()
        self.assertEqual(after["efficiency"], 0.05)
        self.assertLess(after["田赋"], before["田赋"])
        self.assertLess(after["辽饷"], before["辽饷"])
        self.assertLess(after["盐税"], before["盐税"])
        self.assertLess(after["商税"], before["商税"])
        self.assertEqual(after["皇庄"], before["皇庄"])

    def test_region_delta_can_modify_every_player_facing_economy_field(self):
        row = self.db.conn.execute("SELECT * FROM regions WHERE id = 'nanzhili'").fetchone()
        before_fiscal = json.loads(row["fiscal"])
        before_direct = {key: int(row[key]) for key in ("population", "registered_land", "hidden_land", "tax_per_turn")}
        before_scores = {
            "gentry_resistance": int(row["gentry_resistance"]),
            "military_pressure": int(row["military_pressure"]),
        }

        applied = self.db.apply_region_deltas(
            self.state,
            self.event,
            None,
            "测试",
            {
                "nanzhili": {
                    "人口": 10,
                    "田亩": 20,
                    "隐田": -30,
                    "税收": 1,
                    "士绅阻力": -5,
                    "军事压力": 3,
                    "官民田": 40,
                    "藩王庄田": 2,
                    "皇庄": 3,
                    "田赋亩率": 4,
                    "辽饷亩率": 5,
                    "盐税基数": 6,
                    "商税基数": 7,
                    "腐败度": -8,
                    "粮食年产": 90,
                    "存粮": 80,
                    "原因": "覆盖经济字段",
                }
            },
        )

        self.assertGreaterEqual(len(applied), 16)
        row = self.db.conn.execute("SELECT * FROM regions WHERE id = 'nanzhili'").fetchone()
        fiscal = json.loads(row["fiscal"])

        self.assertEqual(int(row["population"]), before_direct["population"] + 10)
        self.assertEqual(int(row["registered_land"]), before_direct["registered_land"] + 20)
        self.assertEqual(int(row["hidden_land"]), before_direct["hidden_land"] - 30)
        self.assertEqual(int(row["tax_per_turn"]), before_direct["tax_per_turn"] + 1)
        self.assertEqual(int(row["gentry_resistance"]), before_scores["gentry_resistance"] - 5)
        self.assertEqual(int(row["military_pressure"]), before_scores["military_pressure"] + 3)
        self.assertEqual(int(fiscal["guan_min_tian"]), int(before_fiscal["guan_min_tian"]) + 40)
        self.assertEqual(int(fiscal["wang_tian"]), int(before_fiscal["wang_tian"]) + 2)
        self.assertEqual(int(fiscal["huang_tian"]), int(before_fiscal["huang_tian"]) + 3)
        self.assertEqual(int(fiscal["tian_fu_li"]), int(before_fiscal["tian_fu_li"]) + 4)
        self.assertEqual(int(fiscal["liao_xiang_li"]), int(before_fiscal["liao_xiang_li"]) + 5)
        self.assertEqual(int(fiscal["salt_tax"]), int(before_fiscal["salt_tax"]) + 6)
        self.assertEqual(int(fiscal["commerce_tax"]), int(before_fiscal["commerce_tax"]) + 7)
        self.assertEqual(int(fiscal["corruption"]), int(before_fiscal["corruption"]) - 8)
        self.assertEqual(int(fiscal["grain_output"]), int(before_fiscal["grain_output"]) + 90)
        self.assertEqual(int(fiscal["grain_stock"]), int(before_fiscal["grain_stock"]) + 80)

    def test_dynamic_tax_scalers_target_rates_and_monthly_bases_correctly(self):
        row = self.db.conn.execute("SELECT fiscal FROM regions WHERE id = 'nanzhili'").fetchone()
        before = json.loads(row["fiscal"])

        self.db.apply_dynamic_fiscal_scale("辽饷", 0.5, "nanzhili")
        self.db.apply_dynamic_fiscal_scale("盐税", 0.5, "nanzhili")
        self.db.apply_dynamic_fiscal_scale("商税", 0.5, "nanzhili")

        after = json.loads(self.db.conn.execute("SELECT fiscal FROM regions WHERE id = 'nanzhili'").fetchone()["fiscal"])
        self.assertEqual(int(after["liao_xiang_li"]), round(int(before["liao_xiang_li"]) * 0.5))
        self.assertEqual(int(after["salt_tax"]), round(int(before["salt_tax"]) * 0.5))
        self.assertEqual(int(after["commerce_tax"]), round(int(before["commerce_tax"]) * 0.5))

        self.db.scale_tian_fu(0.5, "nanzhili")
        after_tian = json.loads(self.db.conn.execute("SELECT fiscal FROM regions WHERE id = 'nanzhili'").fetchone()["fiscal"])
        self.assertEqual(int(after_tian["tian_fu_li"]), round(int(before["tian_fu_li"]) * 0.5))

    def test_old_liao_xiang_monthly_field_migrates_to_liao_xiang_li(self):
        row = self.db.conn.execute("SELECT fiscal FROM regions WHERE id = 'beizhili'").fetchone()
        fiscal = json.loads(row["fiscal"])
        fiscal.pop("liao_xiang_li", None)
        fiscal["guan_min_tian"] = 2400
        fiscal["liao_xiang"] = 3
        self.db.conn.execute(
            "UPDATE regions SET fiscal = ? WHERE id = 'beizhili'",
            (json.dumps(fiscal, ensure_ascii=False),),
        )
        self.db.conn.commit()

        self.db._migrate_region_liao_xiang_li()

        migrated = json.loads(self.db.conn.execute("SELECT fiscal FROM regions WHERE id = 'beizhili'").fetchone()["fiscal"])
        self.assertNotIn("liao_xiang", migrated)
        self.assertEqual(migrated["liao_xiang_li"], 150)

    def test_hidden_land_clearance_changes_tax_basis_and_receipts(self):
        self._set_region_for_exact_tax_math()
        before = self._province_detail()
        row = self.db.conn.execute("SELECT hidden_land, fiscal FROM regions WHERE id = 'beizhili'").fetchone()
        before_hidden = int(row["hidden_land"])
        before_fiscal = json.loads(row["fiscal"])

        self.db.apply_region_deltas(
            self.state,
            self.event,
            None,
            "测试",
            {
                "beizhili": {
                    "隐田": -1200,
                    "田亩": 1200,
                    "官民田": 1200,
                    "原因": "清丈隐田入册",
                }
            },
        )

        row = self.db.conn.execute("SELECT hidden_land, fiscal FROM regions WHERE id = 'beizhili'").fetchone()
        after_fiscal = json.loads(row["fiscal"])
        after = self._province_detail()
        self.assertEqual(int(row["hidden_land"]), before_hidden - 1200)
        self.assertEqual(int(after_fiscal["guan_min_tian"]), int(before_fiscal["guan_min_tian"]) + 1200)
        self.assertEqual(after["田赋"], before["田赋"] + 10)
        self.assertEqual(after["辽饷"], before["辽饷"] + 10)

    def test_annual_grain_and_population_settlement_use_stock_output_population(self):
        self.state.period = 12
        self.db.set_fiscal_config("人均年耗粮_base", 3)
        self.db.set_fiscal_config("人口基础增长率_base", 10)
        self.db.set_fiscal_config("人口民心增益_base", 5)
        self.db.set_fiscal_config("人口民心减损_base", 5)
        self.db.set_fiscal_config("人口动乱减损_base", 5)
        self.db.set_fiscal_config("人口饥荒减损_base", 10)

        fiscal = {
            "guan_min_tian": 0,
            "wang_tian": 0,
            "huang_tian": 0,
            "tian_fu_li": 0,
            "liao_xiang_li": 0,
            "salt_tax": 0,
            "commerce_tax": 0,
            "corruption": 0,
            "grain_output": 900,
            "grain_stock": 600,
        }
        self.db.conn.execute(
            """
            UPDATE regions
            SET population = 200, public_support = 70, unrest = 0,
                natural_disaster = '', human_disaster = '', fiscal = ?
            WHERE id = 'beizhili'
            """,
            (json.dumps(fiscal, ensure_ascii=False),),
        )
        self.db.conn.commit()

        grain_flows = apply_annual_grain_flows(self.db, self.state)
        beizhili_grain = next(flow for flow in grain_flows if flow["region"] == "beizhili")
        self.assertEqual(beizhili_grain["output"], 900)
        self.assertEqual(beizhili_grain["consumption"], 600)
        self.assertEqual(beizhili_grain["stock"], 900)
        self.assertEqual(beizhili_grain["shortfall"], 0)

        pop_flows = apply_annual_population_flows(self.db, self.state, grain_flows)
        beizhili_pop = next(flow for flow in pop_flows if flow["region"] == "北直隶 / 京师")
        self.assertEqual(beizhili_pop["rate"], 1.5)
        self.assertEqual(beizhili_pop["old"], 200)
        self.assertEqual(beizhili_pop["new"], 203)

        fiscal["grain_output"] = 0
        fiscal["grain_stock"] = 10
        self.db.conn.execute(
            """
            UPDATE regions
            SET population = 100, public_support = 30, unrest = 80,
                natural_disaster = '旱灾', human_disaster = '', fiscal = ?
            WHERE id = 'beizhili'
            """,
            (json.dumps(fiscal, ensure_ascii=False),),
        )
        self.db.conn.commit()
        grain_flows = apply_annual_grain_flows(self.db, self.state)
        beizhili_grain = next(flow for flow in grain_flows if flow["region"] == "beizhili")
        self.assertEqual(beizhili_grain["shortfall"], 290)
        pop_flows = apply_annual_population_flows(self.db, self.state, grain_flows)
        beizhili_pop = next(flow for flow in pop_flows if flow["region"] == "北直隶 / 京师")
        self.assertEqual(beizhili_pop["rate"], -1.0)
        self.assertEqual(beizhili_pop["new"], 99)

        fiscal["grain_output"] = 900
        fiscal["grain_stock"] = 600
        self.db.conn.execute(
            """
            UPDATE regions
            SET population = 200, public_support = 70, unrest = 0,
                natural_disaster = '旱灾', human_disaster = '兵燹', fiscal = ?
            WHERE id = 'beizhili'
            """,
            (json.dumps(fiscal, ensure_ascii=False),),
        )
        self.db.conn.commit()
        grain_flows = apply_annual_grain_flows(self.db, self.state)
        pop_flows = apply_annual_population_flows(self.db, self.state, grain_flows)
        beizhili_pop = next(flow for flow in pop_flows if flow["region"] == "北直隶 / 京师")
        self.assertEqual(beizhili_pop["rate"], 1.5)
        self.assertEqual(beizhili_pop["new"], 203)

    def test_new_fiscal_items_and_fixed_fiscal_changes_affect_budget(self):
        apply_score_extraction(
            self.db,
            self.state,
            {
                "fiscal_creates": [
                    {
                        "key": "覆盖人头税_base",
                        "account": "国库",
                        "direction": "income",
                        "display": "覆盖人头税",
                        "init_value": 1200,
                        "formula": "per_basis",
                        "basis": "population",
                        "rate_unit": "毫/人/年",
                        "reason": "覆盖测试",
                    }
                ],
                "fiscal_changes": [
                    {
                        "key": "宗室禄米_base",
                        "mode": "set_amount",
                        "value": 30,
                        "reason": "月额设为三十万",
                    },
                    {
                        "key": "官俸_base",
                        "mode": "scale_amount",
                        "value": -20,
                        "reason": "官俸削二成",
                    },
                ],
            },
            content=self.content,
        )

        budget = compute_budget_lines(self.db, self.state)
        poll_tax = next(item for item in budget["国库"]["income"] if item["name"] == "覆盖人头税")
        zongshi = next(item for item in budget["国库"]["expense"] if item["name"] == "宗室禄米")
        guanfeng = next(item for item in budget["国库"]["expense"] if item["name"] == "百官俸禄")
        self.assertGreater(poll_tax["amount"], 0)
        self.assertEqual(zongshi["amount"], 30)
        self.assertEqual(guanfeng["amount"], 20)

    def test_monthly_flow_settles_army_arrears_and_building_income_maintenance(self):
        self.state.metrics["国库"] = 5
        self.state.metrics["内库"] = 100
        for key in (
            "金花银_rate", "矿税_rate", "织造_rate",
            "宗室禄米_rate", "官俸_rate", "工程_rate", "赈灾_rate",
            "宫廷_rate", "内廷俸_rate", "妃嫔_rate",
        ):
            self.db.set_fiscal_config(key, 0)
        zero_fiscal = {
            "guan_min_tian": 0,
            "wang_tian": 0,
            "huang_tian": 0,
            "tian_fu_li": 0,
            "liao_xiang_li": 0,
            "salt_tax": 0,
            "commerce_tax": 0,
            "corruption": 0,
            "grain_output": 0,
            "grain_stock": 0,
        }
        self.db.conn.execute(
            "UPDATE regions SET fiscal = ?",
            (json.dumps(zero_fiscal, ensure_ascii=False),),
        )
        self.db.conn.execute("UPDATE armies SET maintenance_per_turn = 0")
        self.db.conn.execute(
            """
            UPDATE armies
            SET maintenance_per_turn = 10, arrears = 0, morale = 50
            WHERE id = 'guanning'
            """
        )
        self.db.conn.execute("DELETE FROM buildings")
        self.db.add_building(
            self.state,
            "beizhili",
            "覆盖税关",
            "财政",
            condition=50,
            maintenance=3,
            output_metric="国库",
            output_amount=10,
        )
        self.db.conn.commit()

        flows = apply_fixed_period_flows(self.db, self.state)

        army = self.db.conn.execute(
            "SELECT arrears, morale FROM armies WHERE id = 'guanning'"
        ).fetchone()
        self.assertEqual(int(army["arrears"]), 5)
        self.assertLess(int(army["morale"]), 50)
        self.assertTrue(any(flow.get("category") == "各军军饷" and flow.get("shortfall") == 5 for flow in flows))
        self.assertTrue(any(flow.get("category") == "建筑产出" and flow.get("building") == "覆盖税关" and flow.get("amount") == 5 for flow in flows))
        self.assertTrue(any(flow.get("category") == "建筑维护" and flow.get("building") == "覆盖税关" and flow.get("needed") == 3 for flow in flows))

        ledger = self.db.conn.execute(
            """
            SELECT category, delta
            FROM economy_ledger
            WHERE category IN ('建筑产出', '建筑维护')
            ORDER BY id
            """
        ).fetchall()
        self.assertIn(("建筑产出", 5.0), [(row["category"], float(row["delta"])) for row in ledger])
        self.assertIn(("建筑维护", -3.0), [(row["category"], float(row["delta"])) for row in ledger])


if __name__ == "__main__":
    unittest.main()
