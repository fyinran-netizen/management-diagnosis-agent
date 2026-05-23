export type VerificationResult = {
  passed: boolean;
  issues: string[];
  needs_revision: boolean;
};

export type RetrievedSource = {
  source: string;
  title: string;
  content: string;
  score: number;
};

export type TraceEvent = {
  node: string;
  status: string;
  output_summary: Record<string, unknown>;
  decision?: string;
  next_node?: string;
};

export type DiagnosisDebugResponse = {
  model: string;
  diagnosis_report: string;
  retrieved_sources: RetrievedSource[];
  verification: VerificationResult;
  revision_count: number;
  project_id: string | null;
  trace: TraceEvent[];
};
