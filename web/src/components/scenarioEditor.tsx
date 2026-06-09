import React from "react";
import { Plus, Trash2 } from "lucide-react";
import { updateScenarioFile } from "../api";
import type {
  ScenarioCharacter,
  ScenarioCharactersFile,
  ScenarioEvent,
  ScenarioFaction,
} from "../types";

type FileKey = "characters" | "events" | "seed_events";

// 中文字段标签
const CHAR_LABELS: Record<string, string> = {
  name: "姓名",
  office: "官职",
  office_type: "官职类型",
  faction: "派系",
  loyalty: "忠诚",
  ability: "能力",
  integrity: "清廉",
  courage: "胆略",
  style: "风格",
  power_id: "势力",
  rank: "品秩/位号",
  diplomacy: "外交",
  martial: "军事",
  stewardship: "治政",
  intrigue: "谋略",
  learning: "学识",
  location: "所在",
  birth_year: "生年",
  debut_year: "登场年",
  debut_month: "登场月",
  historical_death_year: "史实卒年",
  historical_death_month: "史实卒月",
  status: "状态",
  summary: "简介",
};
// 字段内联说明（告诉用户怎么填）。没列的字段不显示提示。
const CHAR_HELP: Record<string, string> = {
  office_type: "内阁/六部/督抚/镇守/言官/宗室/勋戚/司礼监/地方 等",
  faction: "须是上面已存在的派系名",
  power_id: "明朝臣子填 ming",
  rank: "后宫位号（皇后/贵妃/妃…），外朝官员留空",
  loyalty: "0–100", ability: "0–100", integrity: "0–100", courage: "0–100",
  diplomacy: "0–100，省略回落能力", martial: "0–100，武力值，省略回落能力",
  stewardship: "0–100，省略回落能力", intrigue: "0–100，省略回落能力", learning: "0–100，省略回落能力",
  location: "地区 id，如 liaodong/beizhili/guangxi",
  birth_year: "公历，0=不设",
  debut_year: "公历，0=开局即在场；填了到该年月才登场",
  debut_month: "1–12，配合登场年",
  historical_death_year: "公历，0=不自动离场；填了到该年月自动离场",
  historical_death_month: "1–12，配合卒年",
  status: "active/offstage/dismissed/imprisoned/exiled/retired/dead",
};
const CHAR_INT_FIELDS = new Set([
  "loyalty", "ability", "integrity", "courage",
  "diplomacy", "martial", "stewardship", "intrigue", "learning",
  "birth_year", "debut_year", "debut_month", "historical_death_year", "historical_death_month",
]);
const CHAR_STR_FIELDS = ["name", "office", "office_type", "faction", "style", "power_id", "rank", "location", "status", "summary"];
const CHAR_ARR_FIELDS = ["aliases", "personal_skills"];
const CHAR_ARR_LABELS: Record<string, string> = { aliases: "别名", personal_skills: "特长" };

const EVENT_LABELS: Record<string, string> = {
  id: "标识",
  title: "标题",
  kind: "类别",
  summary: "摘要",
  urgency: "紧急度",
  severity: "严重度",
  credibility: "可信度",
  event_type: "事项类型",
  precondition: "触发前提（叙事说明）",
  resolve_condition: "达成条件",
  fail_condition: "失败条件",
  trigger_year: "触发年",
  trigger_month: "触发月",
  trigger_end_year: "窗口结束年",
  trigger_end_month: "窗口结束月",
  region_hint: "地区提示",
  bar_value: "进度条初值",
  bar_good_meaning: "进度条满端含义",
  bar_bad_meaning: "进度条见底含义",
  stage_text: "阶段叙事文案",
  inertia: "每月惯性漂移",
  is_historical: "史实锚定情势",
  auto_trigger: "auto_trigger（硬触发）",
};
// 字段内联说明。
const EVENT_HELP: Record<string, string> = {
  id: "稳定唯一标识，改它=换一条事件",
  event_type: "situation=转进度条事项；node=只播报；ending=交结局判定",
  precondition: "触发前提的人话说明，喂推演由 LLM 判定（叙事背景+结果烈度走向，可列结果分档）；决定能否触发的程序闸看下面的门槛",
  urgency: "0–100", severity: "0–100", credibility: "0–100",
  trigger_year: "历史锚定触发年（公历），0=非历史锚定",
  trigger_month: "1–12，0=年内任意月",
  trigger_end_year: "候选窗口结束年，0=不设上限",
  trigger_end_month: "1–12，0=年内任意月",
  region_hint: "地区 id，如 guangxi",
  bar_value: "0–100，situation 转事项时进度条初值，0=自动推导",
  bar_good_meaning: "进度条满端（=100）的含义，不是当前状态",
  bar_bad_meaning: "进度条见底（=0）的含义，不是当前状态",
  stage_text: "立项后的阶段叙事，空=用摘要",
  inertia: "每月自动漂移量，0=不漂",
  is_historical: "省略=按触发年>0 自动推断",
  auto_trigger: "达标即由程序硬立项，绕过 LLM 因果判定",
};
const EVENT_INT_FIELDS = new Set(["urgency", "severity", "credibility", "trigger_year", "trigger_month", "trigger_end_year", "trigger_end_month", "bar_value", "inertia"]);
const EVENT_STR_FIELDS = ["id", "title", "kind", "summary", "precondition", "resolve_condition", "fail_condition", "region_hint"];
// 仅候选事项（seed）才有的字段，历史事项不显示。
const EVENT_SEED_ONLY_INT = new Set(["trigger_end_year", "trigger_end_month", "bar_value", "inertia"]);
const EVENT_SEED_ONLY_STR = ["bar_good_meaning", "bar_bad_meaning", "stage_text"];
const EVENT_ARR_FIELDS = ["interests", "audiences", "tags"];
const EVENT_ARR_LABELS: Record<string, string> = { interests: "相关方", audiences: "受众", tags: "标签" };
const EVENT_TYPES = ["situation", "node", "ending"];

const emptyFaction = (): ScenarioFaction => ({ name: "", satisfaction: 50, leverage: 50, agenda: "" });
const emptyCharacter = (): ScenarioCharacter => ({
  name: "", office: "", office_type: "", faction: "",
  loyalty: 50, ability: 50, integrity: 50, courage: 50, style: "", power_id: "ming",
  personal_skills: [], aliases: [],
});
const emptyEvent = (isSeed: boolean): ScenarioEvent => ({
  id: "", title: "", kind: "", summary: "",
  urgency: 50, severity: 50, credibility: 50,
  interests: [], audiences: [], event_type: "node",
  ...(isSeed ? { trigger_gate: {}, auto_trigger: false } : { trigger_year: 0, trigger_month: 0 }),
});

const arrToText = (v: unknown) => (Array.isArray(v) ? v.join("、") : "");
const textToArr = (s: string) =>
  s.split(/[、,，\n]/).map((x) => x.trim()).filter(Boolean);

// 字段标签 + 内联说明（help 非空才显示小字提示）。
function FieldHint({ text }: { text?: string }) {
  if (!text) return null;
  return <small className="menu-hint scenario-field-hint">{text}</small>;
}

function NumberInput({ value, onChange }: { value: number; onChange: (n: number) => void }) {
  return (
    <input
      type="number"
      value={Number.isFinite(value) ? value : 0}
      onChange={(e) => onChange(Number(e.target.value))}
    />
  );
}

export function ScenarioEditor({
  scenarioId,
  initial,
  initialTab,
  focusKey,
  onClose,
  onSaved,
}: {
  scenarioId: string;
  initial: {
    characters: ScenarioCharactersFile | null;
    events: ScenarioEvent[] | null;
    seed_events: ScenarioEvent[] | null;
  };
  initialTab?: FileKey;
  focusKey?: string; // 人物姓名 / 派系名 / 事件 id，用于定位高亮
  onClose: () => void;
  onSaved: () => void;
}) {
  const [tab, setTab] = React.useState<FileKey>(initialTab ?? "characters");
  const [chars, setChars] = React.useState<ScenarioCharactersFile>(
    initial.characters ?? { factions: [], characters: [] }
  );
  const [events, setEvents] = React.useState<ScenarioEvent[]>(initial.events ?? []);
  const [seedEvents, setSeedEvents] = React.useState<ScenarioEvent[]>(initial.seed_events ?? []);
  const [busy, setBusy] = React.useState(false);
  const [err, setErr] = React.useState("");
  const [ok, setOk] = React.useState("");
  const bodyRef = React.useRef<HTMLDivElement>(null);

  // 从预览点进来时，定位+高亮目标记录。
  React.useEffect(() => {
    if (!focusKey) return;
    const t = window.setTimeout(() => {
      const el = bodyRef.current?.querySelector(`[data-focuskey="${CSS.escape(focusKey)}"]`);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
        el.classList.add("scenario-record-flash");
        window.setTimeout(() => el.classList.remove("scenario-record-flash"), 1800);
      }
    }, 60);
    return () => window.clearTimeout(t);
  }, [focusKey, tab]);

  const saveFile = async (file: FileKey, content: unknown) => {
    setBusy(true);
    setErr("");
    setOk("");
    try {
      await updateScenarioFile(scenarioId, file, content);
      setOk(`已保存「${file === "characters" ? "人物" : file === "events" ? "事项" : "候选事项"}」`);
      onSaved();
    } catch (e: any) {
      setErr(e?.message || String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="menu-modal-bg" onClick={onClose}>
      <div className="menu-modal scenario-editor" onClick={(e) => e.stopPropagation()}>
        <h2>编辑剧本</h2>
        <div className="scenario-tabs">
          <button className={tab === "characters" ? "active" : ""} onClick={() => setTab("characters")}>
            人物（{chars.characters.length}）
          </button>
          <button className={tab === "events" ? "active" : ""} onClick={() => setTab("events")}>
            事项（{events.length}）
          </button>
          <button className={tab === "seed_events" ? "active" : ""} onClick={() => setTab("seed_events")}>
            候选事项（{seedEvents.length}）
          </button>
        </div>

        {err && <div className="menu-error">{err}</div>}
        {ok && <div className="menu-notice">{ok}</div>}

        <div className="scenario-editor-body" ref={bodyRef}>
          {tab === "characters" && (
            <CharactersTab value={chars} onChange={setChars} />
          )}
          {tab === "events" && (
            <EventsTab value={events} isSeed={false} onChange={setEvents} />
          )}
          {tab === "seed_events" && (
            <EventsTab value={seedEvents} isSeed onChange={setSeedEvents} />
          )}
        </div>

        <div className="menu-modal-actions">
          <button onClick={onClose} disabled={busy}>关闭</button>
          <button
            className="primary"
            disabled={busy}
            onClick={() =>
              saveFile(
                tab,
                tab === "characters" ? chars : tab === "events" ? events : seedEvents
              )
            }
          >
            {busy ? "保存中…" : `保存当前标签`}
          </button>
        </div>
      </div>
    </div>
  );
}

function CharactersTab({
  value,
  onChange,
}: {
  value: ScenarioCharactersFile;
  onChange: (v: ScenarioCharactersFile) => void;
}) {
  const setFaction = (i: number, patch: Partial<ScenarioFaction>) => {
    const factions = value.factions.slice();
    factions[i] = { ...factions[i], ...patch };
    onChange({ ...value, factions });
  };
  const setChar = (i: number, patch: Partial<ScenarioCharacter>) => {
    const characters = value.characters.slice();
    characters[i] = { ...characters[i], ...patch };
    onChange({ ...value, characters });
  };

  return (
    <div>
      <h3 className="scenario-section">派系</h3>
      {value.factions.map((f, i) => (
        <div key={i} className="scenario-record" data-focuskey={f.name || undefined}>
          <div className="scenario-record-head">
            <span>{f.name || "（未命名派系）"}</span>
            <button
              className="scenario-del"
              onClick={() => onChange({ ...value, factions: value.factions.filter((_, j) => j !== i) })}
            >
              <Trash2 size={14} />
            </button>
          </div>
          <div className="scenario-fields">
            <label>名称<input value={f.name} onChange={(e) => setFaction(i, { name: e.target.value })} /></label>
            <label>满意<NumberInput value={f.satisfaction} onChange={(n) => setFaction(i, { satisfaction: n })} /></label>
            <label>影响<NumberInput value={f.leverage} onChange={(n) => setFaction(i, { leverage: n })} /></label>
            <label className="wide">诉求<input value={f.agenda} onChange={(e) => setFaction(i, { agenda: e.target.value })} /></label>
          </div>
        </div>
      ))}
      <button className="scenario-add" onClick={() => onChange({ ...value, factions: [...value.factions, emptyFaction()] })}>
        <Plus size={14} /> 添加派系
      </button>

      <h3 className="scenario-section">人物</h3>
      {value.characters.map((c, i) => (
        <div key={i} className="scenario-record" data-focuskey={c.name || undefined}>
          <div className="scenario-record-head">
            <span>{c.name || "（未命名人物）"}</span>
            <button
              className="scenario-del"
              onClick={() => onChange({ ...value, characters: value.characters.filter((_, j) => j !== i) })}
            >
              <Trash2 size={14} />
            </button>
          </div>
          <div className="scenario-fields">
            {CHAR_STR_FIELDS.map((k) => (
              <label key={k} className={k === "summary" ? "wide" : ""}>
                {CHAR_LABELS[k] || k}
                <FieldHint text={CHAR_HELP[k]} />
                <input value={String(c[k] ?? "")} onChange={(e) => setChar(i, { [k]: e.target.value })} />
              </label>
            ))}
            {[...CHAR_INT_FIELDS].map((k) => (
              <label key={k}>
                {CHAR_LABELS[k] || k}
                <FieldHint text={CHAR_HELP[k]} />
                <NumberInput value={Number(c[k] ?? 0)} onChange={(n) => setChar(i, { [k]: n })} />
              </label>
            ))}
            {CHAR_ARR_FIELDS.map((k) => (
              <label key={k} className="wide">
                {CHAR_ARR_LABELS[k]}（顿号分隔）
                <input value={arrToText(c[k])} onChange={(e) => setChar(i, { [k]: textToArr(e.target.value) })} />
              </label>
            ))}
          </div>
        </div>
      ))}
      <button className="scenario-add" onClick={() => onChange({ ...value, characters: [...value.characters, emptyCharacter()] })}>
        <Plus size={14} /> 添加人物
      </button>
    </div>
  );
}

function EventsTab({
  value,
  isSeed,
  onChange,
}: {
  value: ScenarioEvent[];
  isSeed: boolean;
  onChange: (v: ScenarioEvent[]) => void;
}) {
  const setEvent = (i: number, patch: Partial<ScenarioEvent>) => {
    const next = value.slice();
    next[i] = { ...next[i], ...patch };
    onChange(next);
  };
  const gateKey = isSeed ? "trigger_gate" : "require";
  const gateLabel = isSeed ? "触发门槛 trigger_gate" : "前提门槛 require";

  return (
    <div>
      {value.map((ev, i) => (
        <div key={i} className="scenario-record" data-focuskey={ev.id || undefined}>
          <div className="scenario-record-head">
            <span>{ev.title || ev.id || "（未命名事项）"}</span>
            <button className="scenario-del" onClick={() => onChange(value.filter((_, j) => j !== i))}>
              <Trash2 size={14} />
            </button>
          </div>
          <div className="scenario-fields">
            {EVENT_STR_FIELDS.map((k) => (
              <label key={k} className={k === "summary" || k === "precondition" || k.endsWith("condition") ? "wide" : ""}>
                {EVENT_LABELS[k] || k}
                <FieldHint text={EVENT_HELP[k]} />
                <input value={String(ev[k] ?? "")} onChange={(e) => setEvent(i, { [k]: e.target.value })} />
              </label>
            ))}
            <label>
              {EVENT_LABELS.event_type}
              <FieldHint text={EVENT_HELP.event_type} />
              <select value={ev.event_type} onChange={(e) => setEvent(i, { event_type: e.target.value as ScenarioEvent["event_type"] })}>
                {EVENT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </label>
            {/* 史实锚定情势：三态（默认/是/否）。默认=按触发年自动推断。 */}
            <label>
              {EVENT_LABELS.is_historical}
              <FieldHint text={EVENT_HELP.is_historical} />
              <select
                value={ev.is_historical === true ? "1" : ev.is_historical === false ? "0" : ""}
                onChange={(e) => {
                  const v = e.target.value;
                  setEvent(i, { is_historical: v === "" ? undefined : v === "1" });
                }}
              >
                <option value="">默认（按触发年推断）</option>
                <option value="1">是</option>
                <option value="0">否</option>
              </select>
            </label>
            {[...EVENT_INT_FIELDS]
              .filter((k) => isSeed ? !k.startsWith("trigger_year") && k !== "trigger_month" : !EVENT_SEED_ONLY_INT.has(k))
              .map((k) => (
                <label key={k}>
                  {EVENT_LABELS[k] || k}
                  <FieldHint text={EVENT_HELP[k]} />
                  <NumberInput value={Number(ev[k] ?? 0)} onChange={(n) => setEvent(i, { [k]: n })} />
                </label>
              ))}
            {isSeed && EVENT_SEED_ONLY_STR.map((k) => (
              <label key={k} className={k === "stage_text" ? "wide" : ""}>
                {EVENT_LABELS[k] || k}
                <FieldHint text={EVENT_HELP[k]} />
                <input value={String(ev[k] ?? "")} onChange={(e) => setEvent(i, { [k]: e.target.value })} />
              </label>
            ))}
            {EVENT_ARR_FIELDS.map((k) => (
              <label key={k} className="wide">
                {EVENT_ARR_LABELS[k]}（顿号分隔）
                <input value={arrToText(ev[k])} onChange={(e) => setEvent(i, { [k]: textToArr(e.target.value) })} />
              </label>
            ))}
            {isSeed && (
              <label>
                {EVENT_LABELS.auto_trigger}
                <FieldHint text={EVENT_HELP.auto_trigger} />
                <select value={ev.auto_trigger ? "1" : "0"} onChange={(e) => setEvent(i, { auto_trigger: e.target.value === "1" })}>
                  <option value="0">否</option>
                  <option value="1">是</option>
                </select>
              </label>
            )}
            <GateField
              label={gateLabel}
              value={(ev as any)[gateKey]}
              onChange={(parsed) => setEvent(i, { [gateKey]: parsed })}
            />
            <div className="scenario-nested-note wide">
              <small className="menu-hint">
                结构化效果（过程 ongoing_effects / 达成 effect_on_resolve / 崩坏 effect_on_fail，含建筑创建等）
                结构较复杂，请用「AI 对话编辑」来增改——表格编辑器只管上面这些字段，保存时会原样保留这些嵌套字段。
              </small>
            </div>
          </div>
        </div>
      ))}
      <button className="scenario-add" onClick={() => onChange([...value, emptyEvent(isSeed)])}>
        <Plus size={14} /> 添加{isSeed ? "候选事项" : "事项"}
      </button>
    </div>
  );
}

// 门槛字段：校验过的 JSON 文本框。保存前 JSON.parse；后端再用 validate_gate_expr 兜底。
function GateField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: unknown;
  onChange: (parsed: unknown) => void;
}) {
  const [text, setText] = React.useState(() => JSON.stringify(value ?? {}, null, 0));
  const [localErr, setLocalErr] = React.useState("");
  return (
    <label className="wide">
      {label}
      <small className="menu-hint">
        布尔条件树 JSON，如 {"{"}"民心": "&lt;=44"{"}"} 或 {"{"}"and": [...]{"}"}。空对象 {"{}"} = 无条件。
      </small>
      <textarea
        rows={2}
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          try {
            const parsed = e.target.value.trim() ? JSON.parse(e.target.value) : {};
            setLocalErr("");
            onChange(parsed);
          } catch {
            setLocalErr("JSON 格式错误，请修正后再保存。");
          }
        }}
      />
      {localErr && <span className="menu-error">{localErr}</span>}
    </label>
  );
}
