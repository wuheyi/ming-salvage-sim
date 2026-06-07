import unittest

from ming_sim.content import GameContent
from ming_sim.db import GameDB
from ming_sim.issues import apply_score_extraction, bind_content
from ming_sim.models import GameState


class CharacterLocationSettlementTests(unittest.TestCase):
    def test_office_change_can_update_current_location(self):
        content = GameContent.load()
        bind_content(content)
        db = GameDB(":memory:", content)
        db.seed_static_data()
        state = GameState()

        applied = apply_score_extraction(
            db,
            state,
            {
                "character_changes": [
                    {
                        "name": "袁崇焕",
                        "new_office": "陕西总督",
                        "new_office_type": "督抚",
                        "location": "陕西",
                        "reason": "奉旨赴陕西平乱",
                    }
                ]
            },
            content=content,
        )

        row = db.conn.execute(
            "SELECT office, location FROM characters WHERE name=?",
            ("袁崇焕",),
        ).fetchone()

        self.assertEqual(row["office"], "陕西总督")
        self.assertEqual(row["location"], "陕西")
        self.assertEqual(content.characters["袁崇焕"].location, "陕西")
        self.assertEqual(applied["office_changes"][0]["location"], "陕西")


if __name__ == "__main__":
    unittest.main()
