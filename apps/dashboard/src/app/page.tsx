"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import { AlertTriangle, Bot, ChevronRight, Clock3, FileJson2, ShieldCheck, Zap } from "lucide-react";

import { analyzeDLQEvent, decideDLQEvent, getDLQEvent, getDLQEvents, reprocessDLQEvent, type DLQEventDetail, type DLQEventSummary } from "@/lib/api";

const reasonLabel: Record<string, string> = { schema_error: "스키마 오류", missing_required_value: "필수값 누락", unrecoverable: "복구 불가" };
const llmAnalysisEnabled = process.env.NEXT_PUBLIC_LLM_ANALYSIS_ENABLED === "true";
const statusStyle: Record<string, string> = {
  pending: "border-amber-400/30 bg-amber-400/10 text-amber-300",
  pending_analysis: "border-violet-400/30 bg-violet-400/10 text-violet-300",
  invalid: "border-rose-400/30 bg-rose-400/10 text-rose-300",
  failed: "border-rose-400/30 bg-rose-400/10 text-rose-300",
  approved: "border-cyan-400/30 bg-cyan-400/10 text-cyan-300",
  reprocessed: "border-emerald-400/30 bg-emerald-400/10 text-emerald-300",
  on_hold: "border-rose-400/30 bg-rose-400/10 text-rose-300",
  valid: "border-emerald-400/30 bg-emerald-400/10 text-emerald-300",
  not_applicable: "border-slate-500/30 bg-slate-500/10 text-slate-300",
};

function StatusBadge({ value }: { value: string }) {
  return <span className={`inline-flex rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide ${statusStyle[value] ?? statusStyle.on_hold}`}>{value.replaceAll("_", " ")}</span>;
}

export default function SignalFlowDashboard() {
  const [events, setEvents] = useState<DLQEventSummary[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<DLQEventDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const loadEvents = useCallback(async () => {
    const data = await getDLQEvents();
    setEvents(data);
    return data;
  }, []);

  const loadSelectedEvent = useCallback(async (eventId: string) => {
    setSelectedEvent(await getDLQEvent(eventId));
  }, []);

  useEffect(() => {
    async function initialize() {
      try {
        const data = await loadEvents();
        if (data[0]) await loadSelectedEvent(data[0].event_id);
      } catch {
        setError("DLQ 사건을 불러오지 못했습니다. 백엔드 연결을 확인해 주세요.");
      } finally {
        setLoading(false);
      }
    }
    void initialize();
  }, [loadEvents, loadSelectedEvent]);

  async function selectEvent(eventId: string) {
    setActionMessage("");
    try { await loadSelectedEvent(eventId); } catch { setError("사건 상세 정보를 불러오지 못했습니다."); }
  }

  async function decide(decision: "approve" | "hold") {
    if (!selectedEvent) return;
    setIsSaving(true);
    setActionMessage("");
    try {
      setSelectedEvent(await decideDLQEvent(selectedEvent.event_id, decision));
      await loadEvents();
      setActionMessage(decision === "approve" ? "승인 결정이 감사 로그에 기록되었습니다." : "보류 결정이 감사 로그에 기록되었습니다.");
    } catch (requestError) {
      setActionMessage(requestError instanceof Error ? requestError.message : "결정을 저장하지 못했습니다.");
    } finally { setIsSaving(false); }
  }

  async function reprocess() {
    if (!selectedEvent) return;
    setIsSaving(true);
    setActionMessage("");
    try {
      setSelectedEvent(await reprocessDLQEvent(selectedEvent.event_id));
      await loadEvents();
      setActionMessage("재처리 어댑터로 이벤트를 전송했습니다.");
    } catch (requestError) {
      setActionMessage(requestError instanceof Error ? requestError.message : "재처리를 실행하지 못했습니다.");
    } finally { setIsSaving(false); }
  }

  async function analyze() {
    if (!selectedEvent) return;
    setIsSaving(true);
    setActionMessage("");
    try {
      setSelectedEvent(await analyzeDLQEvent(selectedEvent.event_id));
      await loadEvents();
      setActionMessage("AI 분석 결과와 검증 상태를 갱신했습니다.");
    } catch (requestError) {
      setActionMessage(requestError instanceof Error ? requestError.message : "AI 분석을 실행하지 못했습니다.");
    } finally { setIsSaving(false); }
  }

  const pendingCount = events.filter((event) => event.approval_status === "pending").length;
  const holdCount = events.filter((event) => event.approval_status === "on_hold").length;
  const approvalBlockReason = !selectedEvent || selectedEvent.approval_status === "pending"
    ? ""
    : { on_hold: "보류된 사건이라 승인할 수 없습니다. 검증 결과와 위험 사유를 확인해 주세요.",
        pending_analysis: "아직 AI 분석 전이라 승인할 수 없습니다. 먼저 AI 분석을 실행해 주세요.",
        approved: "이미 승인된 사건입니다. 재처리 실행으로 진행할 수 있습니다.",
        reprocessed: "이미 재처리된 사건입니다." }[selectedEvent.approval_status] ?? "";

  return <main className="min-h-screen bg-slate-950 px-5 py-6 text-slate-100 sm:px-8"><div className="mx-auto max-w-7xl">
    <header className="mb-8 flex flex-col gap-4 border-b border-slate-800 pb-6 sm:flex-row sm:items-end sm:justify-between"><div><div className="mb-3 flex items-center gap-2 text-cyan-300"><Zap className="h-5 w-5" /><span className="text-xs font-bold tracking-[0.24em]">SIGNALFLOW</span></div><h1 className="text-3xl font-bold tracking-tight text-white">DLQ Recovery Copilot</h1><p className="mt-2 max-w-2xl text-sm text-slate-400">AI 복구 제안을 검증하고, 운영자가 승인 또는 보류를 결정하는 안전한 이벤트 복구 검토 화면입니다.</p></div><div className="flex items-center gap-2 text-sm text-emerald-300"><span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />Review workspace ready</div></header>
    <section className="mb-6 grid gap-4 sm:grid-cols-3"><MetricCard label="검토 대상" value={String(events.length)} icon={<FileJson2 className="h-5 w-5" />} /><MetricCard label="승인 대기" value={String(pendingCount)} icon={<Clock3 className="h-5 w-5" />} tone="amber" /><MetricCard label="보류 / 격리" value={String(holdCount)} icon={<ShieldCheck className="h-5 w-5" />} tone="rose" /></section>
    {error && <div className="mb-6 flex items-center gap-3 rounded-xl border border-rose-400/30 bg-rose-400/10 p-4 text-sm text-rose-200"><AlertTriangle className="h-5 w-5 shrink-0" />{error}</div>}
    <section className="grid gap-6 lg:grid-cols-[340px_minmax(0,1fr)]"><aside className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4"><div className="mb-4 flex items-center justify-between"><h2 className="text-sm font-semibold text-slate-200">DLQ 사건</h2><span className="text-xs text-slate-500">{events.length} events</span></div><div className="space-y-2">{loading && <p className="p-3 text-sm text-slate-400">사건을 불러오는 중입니다.</p>}{events.map((event) => <button className={`w-full rounded-xl border p-3 text-left transition ${selectedEvent?.event_id === event.event_id ? "border-cyan-400/60 bg-cyan-400/10" : "border-slate-800 bg-slate-950/40 hover:border-slate-600"}`} key={event.event_id} onClick={() => void selectEvent(event.event_id)} type="button"><div className="flex items-start justify-between gap-3"><div><p className="font-mono text-xs font-semibold text-cyan-300">{event.event_id}</p><p className="mt-1 text-sm font-medium text-slate-200">{reasonLabel[event.reason] ?? event.reason}</p></div><ChevronRight className="h-4 w-4 text-slate-500" /></div><p className="mt-2 line-clamp-2 text-xs leading-5 text-slate-500">{event.error_message}</p><div className="mt-3 flex items-center justify-between gap-2"><span className="text-xs text-slate-400">신뢰도 {Math.round(event.confidence * 100)}%</span><div className="flex items-center gap-1.5">{event.analysis_status !== "ready" && <StatusBadge value={event.analysis_status === "failed" ? "failed" : "pending_analysis"} />}<StatusBadge value={event.approval_status} /></div></div></button>)}</div></aside>
    <section className="min-w-0 rounded-2xl border border-slate-800 bg-slate-900/80 p-5 sm:p-6">{!loading && !selectedEvent && <p className="text-sm text-slate-400">검토할 사건을 선택해 주세요.</p>}{selectedEvent && <div><div className="flex flex-col gap-4 border-b border-slate-800 pb-5 sm:flex-row sm:items-start sm:justify-between"><div><div className="mb-2 flex flex-wrap items-center gap-2"><span className="font-mono text-sm font-semibold text-cyan-300">{selectedEvent.event_id}</span><StatusBadge value={selectedEvent.approval_status} /><StatusBadge value={selectedEvent.validation_result.status} /></div><h2 className="text-xl font-bold text-white">{reasonLabel[selectedEvent.reason] ?? selectedEvent.reason}</h2><p className="mt-2 text-sm text-slate-400">{selectedEvent.error_message}</p></div><div className="rounded-xl border border-violet-400/20 bg-violet-400/10 px-4 py-3 text-right"><div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-violet-300"><Bot className="h-4 w-4" />AI confidence</div><p className="mt-1 text-2xl font-bold text-white">{Math.round(selectedEvent.confidence * 100)}%</p></div></div>
    <div className="mt-6 grid gap-5 xl:grid-cols-2"><Panel title="AI 판단 근거"><ReasonText text={selectedEvent.rationale} fallback="AI 분석을 실행하면 판단 근거가 표시됩니다." /></Panel><Panel title="위험 사유"><ReasonText text={selectedEvent.risk_reason} fallback="AI 분석을 실행하면 위험 사유가 표시됩니다." tone="rose" /></Panel></div>
    <div className="mt-5 grid gap-5 xl:grid-cols-2"><Panel title="원본 payload"><JsonBlock value={selectedEvent.raw_payload} /></Panel><Panel title="제안된 payload">{selectedEvent.corrected_payload ? <JsonBlock value={selectedEvent.corrected_payload} /> : <EmptyValue text="안전하게 생성할 수 있는 수정 payload가 없습니다." />}</Panel></div>
    <div className="mt-5 grid gap-5 xl:grid-cols-2"><Panel title="변경 diff">{selectedEvent.changes.length > 0 ? <div className="space-y-3">{selectedEvent.changes.map((change) => <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-3" key={change.field}><div className="flex items-center justify-between gap-3"><span className="font-mono text-sm font-semibold text-cyan-300">{change.field}</span><span className="text-xs text-slate-500">{change.reason}</span></div><div className="mt-3 grid grid-cols-2 gap-3 text-xs"><ValueBlock label="BEFORE" value={change.before} tone="rose" /><ValueBlock label="AFTER" value={change.after} tone="emerald" /></div></div>)}</div> : <EmptyValue text="AI가 안전한 변경안을 제시하지 않았습니다." />}</Panel><Panel title="검증과 감사 로그"><div className="mb-4 rounded-xl border border-slate-800 bg-slate-950/50 p-3"><div className="flex items-center justify-between gap-3"><span className="text-xs font-semibold text-slate-400">PYDANTIC VALIDATOR</span><StatusBadge value={selectedEvent.validation_result.status} /></div>{selectedEvent.validation_result.errors.length > 0 && <ul className="mt-3 space-y-1 text-xs text-rose-300">{selectedEvent.validation_result.errors.map((validationError) => <li key={validationError}>{validationError}</li>)}</ul>}</div><ol className="space-y-2">{selectedEvent.audit_logs.map((log, index) => <li className="flex gap-3 text-sm text-slate-400" key={`${log}-${index}`}><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-600" />{log}</li>)}</ol></Panel></div>
    <div className="mt-6 flex flex-col gap-3 rounded-2xl border border-slate-800 bg-slate-950/50 p-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="text-sm font-semibold text-slate-200">운영자 결정</p><p className="mt-1 text-xs text-slate-500">검증을 통과해도 자동 재처리하지 않습니다.</p>{!llmAnalysisEnabled && <p className="mt-1 text-xs text-violet-300">AI 분석은 현재 연결 전입니다. 검증된 데모 사건을 검토할 수 있습니다.</p>}{selectedEvent.reprocess_result && <p className="mt-1 text-xs text-emerald-300">{selectedEvent.reprocess_result.target} 전송 결과: {selectedEvent.reprocess_result.status}</p>}{approvalBlockReason && <p className="mt-2 text-xs text-amber-300">{approvalBlockReason}</p>}{actionMessage && <p className="mt-2 text-xs text-cyan-300">{actionMessage}</p>}</div><div className="flex flex-wrap gap-2">{llmAnalysisEnabled && <button className="rounded-lg border border-violet-400/50 px-4 py-2 text-sm font-semibold text-violet-200 transition hover:border-violet-300 disabled:cursor-not-allowed disabled:opacity-40" disabled={isSaving} onClick={() => void analyze()} type="button">AI 분석 실행</button>}<button className="rounded-lg border border-slate-600 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:border-rose-300 hover:text-rose-200 disabled:cursor-not-allowed disabled:opacity-40" disabled={isSaving || selectedEvent.approval_status === "reprocessed"} onClick={() => void decide("hold")} type="button">보류</button>{selectedEvent.approval_status === "approved" ? <button className="rounded-lg bg-emerald-400 px-4 py-2 text-sm font-bold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-40" disabled={isSaving} onClick={() => void reprocess()} type="button">재처리 실행</button> : <button className="rounded-lg bg-cyan-400 px-4 py-2 text-sm font-bold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-40" disabled={isSaving || selectedEvent.approval_status !== "pending"} onClick={() => void decide("approve")} type="button">재처리 승인</button>}</div></div>
    </div>}</section></section>
  </div></main>;
}

function MetricCard({ label, value, icon, tone = "cyan" }: { label: string; value: string; icon: ReactNode; tone?: "cyan" | "amber" | "rose" }) {
  const toneClass = { cyan: "text-cyan-300", amber: "text-amber-300", rose: "text-rose-300" }[tone];
  return <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4"><div className={`flex items-center justify-between ${toneClass}`}><span className="text-xs font-semibold uppercase tracking-wide">{label}</span>{icon}</div><p className="mt-4 text-3xl font-bold text-white">{value}</p></div>;
}

function Panel({ title, children }: { title: string; children: ReactNode }) { return <div className="rounded-2xl border border-slate-800 bg-slate-950/30 p-4"><h3 className="mb-3 text-sm font-semibold text-slate-200">{title}</h3>{children}</div>; }
function JsonBlock({ value }: { value: unknown }) { return <pre className="max-h-64 overflow-auto rounded-xl bg-slate-950 p-3 text-xs leading-5 text-slate-300">{JSON.stringify(value, null, 2)}</pre>; }
function ReasonText({ text, fallback, tone = "slate" }: { text?: string; fallback: string; tone?: "slate" | "rose" }) { if (!text) return <EmptyValue text={fallback} />; const toneClass = tone === "rose" ? "border-rose-400/20 bg-rose-400/5 text-rose-100" : "border-slate-800 bg-slate-950/50 text-slate-300"; return <p className={`rounded-xl border p-3 text-sm leading-6 ${toneClass}`}>{text}</p>; }
function EmptyValue({ text }: { text: string }) { return <p className="rounded-xl border border-dashed border-slate-700 p-4 text-sm leading-6 text-slate-500">{text}</p>; }
function ValueBlock({ label, value, tone }: { label: string; value: unknown; tone: "rose" | "emerald" }) { const toneClass = tone === "rose" ? "border-rose-400/20 bg-rose-400/5 text-rose-200" : "border-emerald-400/20 bg-emerald-400/5 text-emerald-200"; return <div className={`rounded-lg border p-2 ${toneClass}`}><p className="text-[10px] font-semibold tracking-wide opacity-60">{label}</p><p className="mt-1 break-all font-mono">{String(value ?? "null")}</p></div>; }
