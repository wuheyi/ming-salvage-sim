"""chat_messages：召对对话存档（持久化，进程重启恢复内存缓存）。

_ChatMixin。原撤回机制（chat_turns / chat_turn_rollback_items + agno runs 裁剪）已废——
召对流式中途退出＝前端中断线程，整轮不落库（副作用循环在流式跑完后才执行，中断即无副作用），
故无需事后回滚。只保留对话消息存档。
"""

from __future__ import annotations

from typing import Dict, List


class _ChatMixin:
    def append_chat_message(self, minister_name: str, turn: int, role: str, content: str) -> int:
        """召对聊天单条消息落库（chat_messages）。"""
        cur = self.conn.execute(
            "INSERT INTO chat_messages (minister_name, turn, role, content) VALUES (?, ?, ?, ?)",
            (minister_name, turn, role, content),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def load_all_chat_history(self) -> Dict[str, List[Dict[str, str]]]:
        """读出全部召对记录，按大臣分组，供进程启动时恢复内存缓存。"""
        rows = self.conn.execute(
            "SELECT minister_name, role, content FROM chat_messages ORDER BY id"
        ).fetchall()
        history: Dict[str, List[Dict[str, str]]] = {}
        for row in rows:
            history.setdefault(row["minister_name"], []).append(
                {"role": row["role"], "content": row["content"]}
            )
        return history

    def count_chat_rounds_in_turn(self, minister_name: str, turn: int) -> int:
        """本回合该大臣已聊几轮（一轮=一条 minister 回复）。供跨月补足算 need。"""
        row = self.conn.execute(
            "SELECT COUNT(*) AS n FROM chat_messages "
            "WHERE minister_name = ? AND turn = ? AND role = 'minister'",
            (minister_name, int(turn)),
        ).fetchone()
        return int(row["n"]) if row else 0

    def load_prev_chat_rounds(
        self, minister_name: str, before_turn: int, max_rounds: int
    ) -> List[Dict[str, str]]:
        """取该大臣 turn < before_turn 的尾 max_rounds 轮纯文本对话（跨月连续，按 id）。
        一轮=user+minister 两行；按 id DESC 取尾 2*max_rounds 行再反转为时间正序。
        走 idx_chat_messages_minister(minister_name, id)，不全表扫。"""
        if max_rounds <= 0:
            return []
        rows = self.conn.execute(
            "SELECT turn, role, content FROM chat_messages "
            "WHERE minister_name = ? AND turn < ? ORDER BY id DESC LIMIT ?",
            (minister_name, int(before_turn), max_rounds * 2),
        ).fetchall()
        return [
            {"turn": row["turn"], "role": row["role"], "content": row["content"]}
            for row in reversed(rows)
        ]

    def append_court_chat_message(self, turn: int, role: str, speaker: str, content: str) -> int:
        """朝会聊天室单条消息落库（court_chat_messages）。"""
        cur = self.conn.execute(
            "INSERT INTO court_chat_messages (turn, role, speaker, content) VALUES (?, ?, ?, ?)",
            (int(turn), role, speaker, content),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def load_court_chat_history(self, turn: int) -> List[Dict[str, str]]:
        """读取某一回合（月）的朝会聊天室记录。"""
        rows = self.conn.execute(
            "SELECT role, speaker, content FROM court_chat_messages WHERE turn = ? ORDER BY id",
            (int(turn),),
        ).fetchall()
        return [
            {"role": row["role"], "speaker": row["speaker"], "content": row["content"]}
            for row in rows
        ]
