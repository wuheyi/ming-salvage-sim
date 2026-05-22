"""月末推演与打分提取：跑 simulator/extractor agent。L7。"""

from __future__ import annotations

import json
import sqlite3
from typing import Dict, List, Optional

from agno.agent import Agent

from ming_sim.agents import parse_agent_json, run_agent_stream_text, run_agent_text
from ming_sim.context import historical_anchor_for_month, victory_status
from ming_sim.db import GameDB
from ming_sim.issues import gather_candidate_events, issue_to_payload
from ming_sim.models import GameState
from ming_sim.token_stats import tlog


def simulate_season_with_agno(
    agent: Agent,
    state: GameState,
    db: GameDB,
    decree_text: str,
    directives_brief: List[Dict[str, object]],
    previous_narrative: str,
    fixed_flows: Optional[List[Dict[str, object]]] = None,
    deaths_this_turn: Optional[List[Dict[str, str]]] = None,
) -> str:
    """推演 agent: 输入一坨,输出一篇邸报纯文字。"""
    active = db.list_active_issues()
    issues_payload = [
        issue_to_payload(row, db.list_recent_issue_advances(int(row["id"]), 1))
        for row in active
    ]
    # 程序已按 trigger 时间 / trigger_gate 阈值筛过的候选事件，交推演 agent 因果判定是否触发。
    candidate_events = [
        {
            "id": ev.id,
            "title": ev.title,
            "kind": ev.kind,
            "summary": ev.summary,
            "interests": ev.interests,
            "is_historical": ev.trigger_year > 0,
            "resolve_condition": ev.resolve_condition,
            "fail_condition": ev.fail_condition,
        }
        for ev in gather_candidate_events(state, db)
    ]
    payload = {
        "year": state.year,
        "period": state.period,
        "decree_text": decree_text,
        "directives": directives_brief,
        "current_state": dict(state.metrics),
        "treasury": db.treasury_report(state),
        "factions": db.faction_report(),
        "active_issues": issues_payload,
        "candidate_events": candidate_events,
        "previous_narrative_tail": previous_narrative[-1500:] if previous_narrative else "",
        "external_powers": db.external_power_payload(),
        "historical_anchor": historical_anchor_for_month(state.year, state.period),
        "victory_status": victory_status(db, state),
        "regions": db.region_payload(limit=8, danger_order=True),
        "armies": db.army_payload(limit=8, danger_order=True),
        "fixed_flows": fixed_flows or [],
        "deaths_this_turn": deaths_this_turn or [],
    }
    raw = run_agent_stream_text(
        agent,
        json.dumps(payload, ensure_ascii=False, sort_keys=False),
        tag="simulator",
    )
    return raw.strip()


def extract_scores_with_agno(
    agent: Agent,
    db: GameDB,
    state: GameState,
    narrative: str,
    decree_text: str = "",
    sanitizer: Optional[Agent] = None,
) -> tuple[Dict[str, object], str, str]:
    """结算 agent: 读邸报抽 JSON。

    返回 (解析后的 dict, extractor 原始输出串, extractor 输入 payload 串)，
    后两项供调用方留痕到 turn_extractions。
    """
    active = db.list_active_issues()

    def _cond(r: sqlite3.Row, key: str) -> str:
        keys = r.keys() if hasattr(r, "keys") else []
        return r[key] if key in keys else ""

    issues_brief = [
        {
            "issue_id": int(r["id"]),
            "title": r["title"],
            "bar_value": int(r["bar_value"]),
            "inertia": int(r["inertia"]),
            "stage_text": r["stage_text"],
            "cancellable": r["cancellable"],
            "resolve_condition": _cond(r, "resolve_condition") or "(未填)",
            "fail_condition": _cond(r, "fail_condition") or "(未填)",
        }
        for r in active
    ]
    region_ids = [r["id"] for r in db.conn.execute("SELECT id FROM regions").fetchall()]
    army_ids = [r["id"] for r in db.conn.execute("SELECT id FROM armies").fetchall()]
    candidate_events = [
        {"id": ev.id, "title": ev.title}
        for ev in gather_candidate_events(state, db)
    ]
    payload = {
        "narrative": narrative,
        "decree_text": decree_text,
        "active_issues": issues_brief,
        "candidate_events": candidate_events,
        "current_state": dict(state.metrics),
        "factions": db.faction_report(),
        "external_powers": db.external_power_payload(),
        "region_ids": region_ids,
        "army_ids": army_ids,
        "external_power_ids": [str(r["id"]) for r in db.conn.execute("SELECT id FROM external_powers").fetchall()],
        "fiscal_config": db.get_fiscal_config(),
    }
    payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=False)
    raw = run_agent_text(agent, payload_json, tag="extractor")
    try:
        return parse_agent_json(raw, "结算抽取"), raw, payload_json
    except Exception as parse_err:
        if sanitizer is None:
            raise
        tlog(f"[extractor] 主输出解析失败：{parse_err}；调 sanitizer 重整")
        cleaned = run_agent_text(sanitizer, raw, tag="sanitizer")
        # 留痕用原始 raw（sanitizer 前），追查时能看到 extractor 真实吐了什么。
        return parse_agent_json(cleaned, "结算抽取（sanitizer）"), raw, payload_json
