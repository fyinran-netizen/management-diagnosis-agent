import { useMemo, useState } from "react";
import { AlertCircle, CheckCircle2, ChevronDown, ChevronRight, Database, FileText, Loader2, Play, ShieldCheck } from "lucide-react";
import { runDiagnosis } from "./api";
import type { DiagnosisDebugResponse, RetrievedSource, TraceEvent } from "./types";

const sampleDescription =
  "我们公司最近增长放缓，团队每天都很忙，但新客户越来越少。管理层主要在抓成本和效率，员工只是完成KPI，请帮我判断主要管理问题，并给出下一步建议。";

function formatValue(value: unknown): string {
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(3);
  }
  if (typeof value === "boolean") {
    return value ? "yes" : "no";
  }
  if (value === null || value === undefined) {
    return "-";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

function DiagnosisForm({
  description,
  isLoading,
  onChange,
  onSubmit,
}: {
  description: string;
  isLoading: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
}) {
  return (
    <section className="panel input-panel">
      <div className="panel-header">
        <div>
          <h2>Case Input</h2>
          <p>Describe the management situation you want diagnosed.</p>
        </div>
      </div>
      <textarea
        value={description}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Describe growth, customers, team behavior, metrics, strategy, or organization symptoms..."
      />
      <button className="primary-button" disabled={isLoading || !description.trim()} onClick={onSubmit}>
        {isLoading ? <Loader2 className="spin" size={18} /> : <Play size={18} />}
        Run Diagnosis
      </button>
    </section>
  );
}

function ReportPanel({ result }: { result: DiagnosisDebugResponse | null }) {
  return (
    <section className="panel report-panel">
      <div className="panel-header">
        <div>
          <h2>Diagnosis Report</h2>
          <p>{result ? `Model: ${result.model}` : "The final answer will appear here."}</p>
        </div>
        {result?.project_id ? <span className="tag">Project {result.project_id}</span> : null}
      </div>
      <div className="report-content">
        {result?.diagnosis_report ? result.diagnosis_report : "No report yet."}
      </div>
    </section>
  );
}

function VerificationPanel({ result }: { result: DiagnosisDebugResponse | null }) {
  const verification = result?.verification;
  return (
    <section className="panel compact-panel">
      <div className="metric-title">
        <ShieldCheck size={18} />
        Verification
      </div>
      {!verification ? (
        <p className="muted">No verification result yet.</p>
      ) : (
        <>
          <div className={verification.passed ? "status-line pass" : "status-line fail"}>
            {verification.passed ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
            {verification.passed ? "Passed" : "Needs attention"}
          </div>
          <p className="muted">Revision count: {result.revision_count}</p>
          {verification.issues.length > 0 ? (
            <ul className="issue-list">
              {verification.issues.map((issue) => (
                <li key={issue}>{issue}</li>
              ))}
            </ul>
          ) : null}
        </>
      )}
    </section>
  );
}

function Timeline({ events }: { events: TraceEvent[] }) {
  return (
    <section className="panel timeline-panel">
      <div className="panel-header">
        <div>
          <h2>Agent Timeline</h2>
          <p>{events.length ? `${events.length} recorded steps` : "Trace events will appear after a run."}</p>
        </div>
      </div>
      <div className="timeline">
        {events.length === 0 ? (
          <div className="empty-state">No trace yet.</div>
        ) : (
          events.map((event, index) => <TimelineItem event={event} index={index} key={`${event.node}-${index}`} />)
        )}
      </div>
    </section>
  );
}

function TimelineItem({ event, index }: { event: TraceEvent; index: number }) {
  const [open, setOpen] = useState(index < 3);
  const summaryEntries = Object.entries(event.output_summary ?? {});
  return (
    <article className="timeline-item">
      <button className="timeline-title" onClick={() => setOpen((value) => !value)}>
        {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        <span className="step-number">{index + 1}</span>
        <span>{event.node}</span>
        {event.decision ? <span className="decision">decision: {event.decision}</span> : null}
      </button>
      {open ? (
        <div className="timeline-details">
          {summaryEntries.map(([key, value]) => (
            <div className="summary-row" key={key}>
              <span>{key}</span>
              <strong>{formatValue(value)}</strong>
            </div>
          ))}
          {event.next_node ? (
            <div className="summary-row">
              <span>next_node</span>
              <strong>{event.next_node}</strong>
            </div>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}

function SourcesPanel({ sources }: { sources: RetrievedSource[] }) {
  const [selectedSource, setSelectedSource] = useState<RetrievedSource | null>(null);
  return (
    <section className="panel sources-panel">
      <div className="panel-header">
        <div>
          <h2>Retrieved Sources</h2>
          <p>{sources.length ? `${sources.length} knowledge chunks used` : "No sources yet."}</p>
        </div>
        <Database size={20} />
      </div>
      {sources.length === 0 ? (
        <div className="empty-state">Run a diagnosis to see retrieved knowledge.</div>
      ) : (
        <div className="sources-grid">
          <div className="source-list">
            {sources.map((source) => (
              <button
                className={selectedSource?.source === source.source ? "source-row active" : "source-row"}
                key={`${source.source}-${source.title}`}
                onClick={() => setSelectedSource(source)}
              >
                <span>
                  <strong>{source.title}</strong>
                  <small>{source.source}</small>
                </span>
                <em>{formatValue(source.score)}</em>
              </button>
            ))}
          </div>
          <div className="source-preview">
            {selectedSource ? (
              <>
                <h3>{selectedSource.title}</h3>
                <p className="muted">{selectedSource.source}</p>
                <p>{selectedSource.content}</p>
              </>
            ) : (
              <p className="muted">Select a source to inspect its content.</p>
            )}
          </div>
        </div>
      )}
    </section>
  );
}

function DebugPanel({ result }: { result: DiagnosisDebugResponse | null }) {
  const [open, setOpen] = useState(false);
  const rawJson = useMemo(() => (result ? JSON.stringify(result, null, 2) : ""), [result]);
  return (
    <section className="panel debug-panel">
      <button className="debug-toggle" onClick={() => setOpen((value) => !value)} disabled={!result}>
        <FileText size={18} />
        {open ? "Hide raw response" : "Show raw response"}
      </button>
      {open && result ? <pre>{rawJson}</pre> : null}
    </section>
  );
}

export function App() {
  const [description, setDescription] = useState(sampleDescription);
  const [result, setResult] = useState<DiagnosisDebugResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit() {
    setIsLoading(true);
    setError(null);
    try {
      const data = await runDiagnosis(description);
      setResult(data);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <h1>Management Diagnosis Agent</h1>
          <p>Run the local Agent and inspect the report, retrieval sources, verification, and workflow trace.</p>
        </div>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      <div className="main-grid">
        <div className="left-column">
          <DiagnosisForm
            description={description}
            isLoading={isLoading}
            onChange={setDescription}
            onSubmit={handleSubmit}
          />
          <ReportPanel result={result} />
        </div>
        <div className="right-column">
          <VerificationPanel result={result} />
          <Timeline events={result?.trace ?? []} />
        </div>
      </div>

      <SourcesPanel sources={result?.retrieved_sources ?? []} />
      <DebugPanel result={result} />
    </main>
  );
}
