"""数据类：游戏实体与状态容器。L0 叶子模块。

CourtContext 的 state/db 注解用字符串前向引用，避免 import db.py。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from ming_sim.constants import ECONOMY_ACCOUNTS


@dataclass
class ChatResult:
    action: str
    next_minister: str = ""
    refresh_ministers: List[str] = field(default_factory=list)


@dataclass
class LLMConfig:
    api_key: str
    base_url: str
    model: str


@dataclass
class Character:
    name: str
    office: str
    office_type: str
    faction: str
    aliases: List[str]
    personal_skills: List[str]
    loyalty: int
    ability: int
    integrity: int
    courage: int
    style: str
    birth_year: int = 0  # 历史生年（公历，0=未填）
    historical_death_year: int = 0  # 历史卒年（公历，0=未填）
    historical_death_month: int = 0  # 1-12，0=未指定
    status: str = "active"  # active | dismissed | imprisoned | exiled | retired | dead


@dataclass
class Event:
    id: str
    title: str
    kind: str
    summary: str
    urgency: int
    severity: int
    credibility: int
    interests: List[str]
    audiences: List[str]
    resolve_condition: str = ""
    fail_condition: str = ""
    trigger_year: int = 0   # 历史锚定触发年（公历，0=非历史锚定，靠 trigger_gate）
    trigger_month: int = 0  # 1-12，0=年内任意月
    precondition: str = ""  # 简短人话描述（如"民变>=60 + 陕西 unrest>=80"），目前只展示不强校验
    event_type: str = "situation"  # situation=转 bar issue；node=只播报不转 issue；ending=交结局判定
    trigger_gate: Dict[str, str] = field(default_factory=dict)  # seed 候选门槛：{metric: 比较式}，全满足才进候选


@dataclass
class Faction:
    name: str
    satisfaction: int
    leverage: int
    agenda: str


@dataclass
class Region:
    id: str
    name: str
    kind: str
    population: int
    public_support: int
    unrest: int
    natural_disaster: str
    human_disaster: str
    registered_land: int
    hidden_land: int
    tax_per_turn: int
    grain_security: int
    gentry_resistance: int
    military_pressure: int
    status: str


@dataclass
class Army:
    id: str
    name: str
    station: str
    theater: str
    commander: str
    controller: str
    troop_type: str
    manpower: int
    maintenance_per_turn: int
    supply: int
    morale: int
    training: int
    equipment: int
    arrears: int
    mobility: int
    loyalty: int
    status: str


@dataclass
class ExternalPower:
    id: str
    name: str
    leader: str
    stance: str
    leverage: int
    satisfaction: int
    military_strength: int
    cohesion: int
    supply: int
    agenda: str
    status: str
    last_action: str = "尚无新动"


@dataclass
class GameState:
    year: int = 1627
    period: int = 12
    turn: int = 1
    turn_phase: str = "summoning"  # summoning | reviewing | issued —— 见 session.TurnPhase
    metrics: Dict[str, int] = field(
        default_factory=lambda: {
            "国库": 320,
            "内库": 440,
            "民心": 46,
            "皇威": 58,
            "边防": 68,
            "民变": 30,
            "党争": 64,
            "执行": 42,
            "瞒报": 50,
        }
    )
    log: List[str] = field(default_factory=list)

    def clamp(self) -> None:
        for key, value in list(self.metrics.items()):
            if key in ECONOMY_ACCOUNTS:
                self.metrics[key] = max(0, value)
            else:
                self.metrics[key] = max(0, min(100, value))

    def next_period(self) -> None:
        self.turn += 1
        self.period += 1
        if self.period > 12:
            self.period = 1
            self.year += 1


@dataclass
class CourtContext:
    state: "GameState"
    db: "object"  # GameDB；用 object 注解避免 import db.py 造成环
    previous_summary: str = ""


def period_label(year: int, month: int) -> str:
    return f"{year}年{month}月"


def monthly_amount(amount: int) -> int:
    return max(0, round(int(amount) / 3))
