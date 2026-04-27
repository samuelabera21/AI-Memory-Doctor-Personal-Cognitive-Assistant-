"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import styles from "./page.module.css";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

type AppView = "home" | "add" | "search" | "memories" | "summaries" | "insights" | "agent" | "evaluation" | "health";

type MemoryRow = {
  id: number;
  content: string;
  type: string;
  date: string;
  time: string;
  duration?: string | null;
  tags?: string[];
  version?: number;
  importance_score?: number;
  importance_reasons?: string[];
};

type MemoryHistoryRow = {
  id: number;
  old_content: string;
  new_content: string;
  old_type: string;
  new_type: string;
  change_reason: string;
  changed_at: string;
};

type SearchResponse = {
  query: string;
  answer: string;
  results: Array<
    MemoryRow & {
      semantic_score?: number;
    }
  >;
  time_filters?: {
    start_date?: string | null;
    end_date?: string | null;
    start_time?: string | null;
    end_time?: string | null;
  };
  context_meta?: {
    query_context_applied?: boolean;
    temporal_context_applied?: boolean;
    gate?: {
      applied?: boolean;
      reason?: string;
      confidence?: number;
      is_followup?: boolean;
      is_fresh?: boolean;
      ttl_seconds?: number;
      min_confidence?: number;
    };
  };
};

type SummaryResponse = {
  query: string;
  summary: string;
  count: number;
  ai_used?: boolean;
  provider?: string;
  period: { start_date: string; end_date: string };
};

type InsightResponse = {
  count: number;
  status?: "ready" | "insufficient_data";
  insight: string;
  most_common_type: string | null;
  most_productive_time: string | null;
  repeated_mistakes: string[];
  trend: string;
  priority_count?: number;
  priority_ratio?: number;
  priority_focus?: string | null;
  priority_highlights?: string[];
};

type EvalMetrics = {
  classification_accuracy: number;
  retrieval_accuracy: number;
  response_correctness: number;
  context_followup_accuracy?: number;
  context_application_rate?: number;
  sample_count: number;
  notes?: string[];
  passed_cases?: number;
  total_cases?: number;
};

type ExportReportResponse = {
  message: string;
  metrics: EvalMetrics;
  json_report: string;
  csv_report: string;
};

type ContextScenarioResponse = {
  message: string;
  scenario: {
    seed_count: number;
    first_query: string;
    followup_query: string;
    first_result_count: number;
    followup_result_count: number;
    context_meta?: {
      query_context_applied?: boolean;
      temporal_context_applied?: boolean;
      gate?: {
        applied?: boolean;
        reason?: string;
        confidence?: number;
      };
    };
  };
  scores: {
    context_followup_correctness: number;
    context_application_rate: number;
  };
  metric_sample: {
    retrieval_precision: number;
    response_correctness: number;
    context_followup_correctness: number;
    context_application_rate: number;
  };
};

type ContextScenarioHistoryItem = {
  run_id: string;
  generated_at_utc?: string;
  user_id?: number;
  context_followup_correctness: number;
  context_application_rate?: number;
  gate_reason?: string;
  gate_confidence?: number;
  query_context_applied?: boolean;
  temporal_context_applied?: boolean;
};

type ContextScenarioHistoryResponse = {
  items: ContextScenarioHistoryItem[];
  count: number;
  limit: number;
  avg_context_followup_correctness?: number;
};

type HealthPayload = {
  status?: string;
  message?: string;
  version?: string;
  environment?: string;
  [key: string]: unknown;
};

type AgentBase = {
  intent?: string;
  message?: string;
  hint?: string;
};

type AgentStoreResponse = AgentBase & {
  status?: string;
  memory_id?: number;
  data?: {
    date?: string;
    time?: string;
    type?: string;
    content?: string;
    duration?: string | null;
    tags?: string[] | string;
  };
};

type AgentSearchResponse = AgentBase & SearchResponse;
type AgentSummaryResponse = AgentBase & SummaryResponse;
type AgentInsightResponse = AgentBase & InsightResponse;
type AgentGenericResponse = AgentBase & Record<string, unknown>;

type MemorySort = "newest" | "oldest" | "type";

const MEMORY_PAGE_SIZE = 20;

function readTokenFromStorage(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return localStorage.getItem("ai_memory_token");
}

function readEmailFromStorage(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return localStorage.getItem("ai_memory_email");
}

async function parseApiError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") return data.detail;
    if (typeof data?.message === "string") return data.message;
    return JSON.stringify(data);
  } catch {
    return `${response.status} ${response.statusText}`;
  }
}

async function apiRequest<T>(
  path: string,
  options: { method?: string; token?: string | null; body?: unknown; onUnauthorized?: () => void } = {},
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: options.method ?? "GET",
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    });
  } catch {
    throw new Error(`Cannot reach backend at ${API_BASE}. Start FastAPI server and try again.`);
  }

  if (response.status === 401) {
    options.onUnauthorized?.();
    throw new Error("Session expired. Please log in again.");
  }

  if (!response.ok) {
    throw new Error(await parseApiError(response));
  }

  const raw = await response.text();
  if (!raw) {
    return null as T;
  }

  return JSON.parse(raw) as T;
}

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeView, setActiveView] = useState<AppView>("home");

  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authHydrated, setAuthHydrated] = useState(false);

  const [globalError, setGlobalError] = useState<string | null>(null);
  const [globalSuccess, setGlobalSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [memories, setMemories] = useState<MemoryRow[]>([]);
  const [selectedMemoryId, setSelectedMemoryId] = useState<number | null>(null);
  const [memoryHistory, setMemoryHistory] = useState<MemoryHistoryRow[]>([]);
  const [memoryFilterQuery, setMemoryFilterQuery] = useState("");
  const [memoryFilterType, setMemoryFilterType] = useState("all");
  const [memoryExactDate, setMemoryExactDate] = useState("");
  const [memoryDateFrom, setMemoryDateFrom] = useState("");
  const [memoryDateTo, setMemoryDateTo] = useState("");
  const [memorySort, setMemorySort] = useState<MemorySort>("newest");
  const [memoryPage, setMemoryPage] = useState(1);
  const [memoryFindId, setMemoryFindId] = useState("");

  const [addContent, setAddContent] = useState("");
  const [addTime, setAddTime] = useState("");

  const [editContent, setEditContent] = useState("");
  const [editReason, setEditReason] = useState("manual_edit");
  const [selectedUpdateMode, setSelectedUpdateMode] = useState<"manual" | "natural">("manual");

  const [correctionText, setCorrectionText] = useState("");

  const [searchQuery, setSearchQuery] = useState("");
  const [searchData, setSearchData] = useState<SearchResponse | null>(null);

  const [summaryQuery, setSummaryQuery] = useState("summarize this week");
  const [summaryData, setSummaryData] = useState<SummaryResponse | null>(null);

  const [insightData, setInsightData] = useState<InsightResponse | null>(null);

  const [agentText, setAgentText] = useState("");
  const [agentData, setAgentData] = useState<AgentGenericResponse | null>(null);

  const [metricsData, setMetricsData] = useState<EvalMetrics | null>(null);
  const [reportName, setReportName] = useState("thesis_eval_ui");
  const [exportData, setExportData] = useState<ExportReportResponse | null>(null);
  const [contextScenarioData, setContextScenarioData] = useState<ContextScenarioResponse | null>(null);
  const [contextScenarioHistory, setContextScenarioHistory] = useState<ContextScenarioHistoryResponse | null>(null);

  const [rootData, setRootData] = useState<HealthPayload | null>(null);
  const [liveData, setLiveData] = useState<HealthPayload | null>(null);
  const [readyData, setReadyData] = useState<HealthPayload | null>(null);
  const [healthCheckedAt, setHealthCheckedAt] = useState<string | null>(null);

  const clearMemorySelection = () => {
    setSelectedMemoryId(null);
    setEditContent("");
    setEditReason("manual_edit");
    setSelectedUpdateMode("manual");
    setMemoryHistory([]);
  };

  const onUnauthorized = () => {
    setToken(null);
    setEmail(null);
    setMemories([]);
    setSearchData(null);
    if (typeof window !== "undefined") {
      localStorage.removeItem("ai_memory_token");
      localStorage.removeItem("ai_memory_email");
    }
  };

  const withGuard = async (fn: () => Promise<void>) => {
    setGlobalError(null);
    setGlobalSuccess(null);
    setLoading(true);
    try {
      await fn();
    } catch (error) {
      setGlobalError(error instanceof Error ? error.message : "Unexpected error");
    } finally {
      setLoading(false);
    }
  };

  const loadMemories = useCallback(async () => {
    if (!token) return;
    const rows = await apiRequest<MemoryRow[]>("/memories", { token, onUnauthorized });
    setMemories(rows);
  }, [token]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const timer = window.setTimeout(() => {
      setToken(readTokenFromStorage());
      setEmail(readEmailFromStorage());
      setAuthHydrated(true);
    }, 0);

    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!token) return;
    const timer = window.setTimeout(() => {
      void withGuard(async () => {
        await loadMemories();
        const insights = await apiRequest<InsightResponse>("/insights", { token, onUnauthorized });
        setInsightData(insights);
      });
    }, 0);

    return () => window.clearTimeout(timer);
  }, [token, loadMemories]);

  const signOut = () => {
    onUnauthorized();
    setGlobalSuccess("Logged out successfully.");
  };

  const submitAuth = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await withGuard(async () => {
      if (authMode === "register") {
        await apiRequest<{ message: string }>("/auth/register", {
          method: "POST",
          body: { email: authEmail, password: authPassword },
        });
        setAuthMode("login");
        setGlobalSuccess("Account created. Please login.");
        return;
      }

      const login = await apiRequest<{ access_token: string; token_type: string }>("/auth/login", {
        method: "POST",
        body: { email: authEmail, password: authPassword },
      });

      setToken(login.access_token);
      setEmail(authEmail);
      if (typeof window !== "undefined") {
        localStorage.setItem("ai_memory_token", login.access_token);
        localStorage.setItem("ai_memory_email", authEmail);
      }
      setGlobalSuccess("Login successful.");
    });
  };

  const submitAddMemory = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await withGuard(async () => {
      if (!token) throw new Error("Please login first.");
      await apiRequest<{ status: string; memory_id: number; data: MemoryRow }>("/add-memory", {
        method: "POST",
        token,
        body: { content: addContent, time: addTime || null },
        onUnauthorized,
      });
      setAddContent("");
      setAddTime("");
      setGlobalSuccess("Memory saved.");
      await loadMemories();
    });
  };

  const runQuickSearch = async () => {
    if (!searchQuery.trim()) return;
    setActiveView("search");
    await withGuard(async () => {
      if (!token) throw new Error("Please login first.");
      const response = await apiRequest<SearchResponse>("/search-memory", {
        method: "POST",
        token,
        body: { query: searchQuery },
        onUnauthorized,
      });
      setSearchData(response);
    });
  };

  const memoryTypes = useMemo(() => {
    return Array.from(new Set(memories.map((memory) => memory.type).filter(Boolean))).sort((a, b) =>
      a.localeCompare(b),
    );
  }, [memories]);

  const filteredMemories = useMemo(() => {
    const normalizedQuery = memoryFilterQuery.trim().toLowerCase();
    const rows = memories.filter((memory) => {
      const matchesQuery =
        normalizedQuery.length === 0 ||
        memory.content.toLowerCase().includes(normalizedQuery) ||
        memory.type.toLowerCase().includes(normalizedQuery) ||
        memory.date.toLowerCase().includes(normalizedQuery) ||
        memory.time.toLowerCase().includes(normalizedQuery) ||
        String(memory.id).includes(normalizedQuery);

      const matchesType = memoryFilterType === "all" || memory.type === memoryFilterType;
      const matchesExactDate = !memoryExactDate || memory.date === memoryExactDate;
      const matchesFrom = !memoryDateFrom || memory.date >= memoryDateFrom;
      const matchesTo = !memoryDateTo || memory.date <= memoryDateTo;
      return matchesQuery && matchesType && matchesExactDate && matchesFrom && matchesTo;
    });

    const sortable = [...rows];
    if (memorySort === "type") {
      sortable.sort((a, b) => {
        const byType = a.type.localeCompare(b.type);
        if (byType !== 0) return byType;
        const aKey = `${a.date} ${a.time}`;
        const bKey = `${b.date} ${b.time}`;
        return bKey.localeCompare(aKey);
      });
      return sortable;
    }

    sortable.sort((a, b) => {
      const aKey = `${a.date} ${a.time}`;
      const bKey = `${b.date} ${b.time}`;
      return memorySort === "newest" ? bKey.localeCompare(aKey) : aKey.localeCompare(bKey);
    });
    return sortable;
  }, [memories, memoryFilterQuery, memoryFilterType, memoryExactDate, memoryDateFrom, memoryDateTo, memorySort]);

  const totalMemoryPages = Math.max(1, Math.ceil(filteredMemories.length / MEMORY_PAGE_SIZE));
  const currentMemoryPage = Math.min(memoryPage, totalMemoryPages);
  const pagedMemories = useMemo(() => {
    const start = (currentMemoryPage - 1) * MEMORY_PAGE_SIZE;
    return filteredMemories.slice(start, start + MEMORY_PAGE_SIZE);
  }, [filteredMemories, currentMemoryPage]);

  const findMemoryById = () => {
    const id = Number(memoryFindId);
    if (!id || Number.isNaN(id)) {
      setGlobalError("Enter a valid numeric memory ID.");
      return;
    }
    const memory = memories.find((row) => row.id === id);
    if (!memory) {
      setGlobalError(`Memory ID ${id} not found.`);
      return;
    }

    setGlobalError(null);
    setSelectedMemoryId(memory.id);
    setEditContent(memory.content);
    setSelectedUpdateMode("manual");
    setMemoryFilterQuery(String(memory.id));
    setGlobalSuccess(`Memory ID ${memory.id} selected.`);
  };

  const submitMemoryUpdate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await withGuard(async () => {
      if (!token || !selectedMemoryId) throw new Error("Select a memory first.");
      await apiRequest<{ status: string }>(`/memories/${selectedMemoryId}`, {
        method: "PUT",
        token,
        body: { content: editContent, reason: editReason || "manual_edit" },
        onUnauthorized,
      });
      await loadMemories();
      clearMemorySelection();
      setGlobalSuccess("Memory updated. Returned to memory finder.");
    });
  };

  const deleteMemory = async (memoryId: number) => {
    await withGuard(async () => {
      if (!token) throw new Error("Please login first.");
      await apiRequest<{ status: string }>(`/memories/${memoryId}`, {
        method: "DELETE",
        token,
        body: { reason: "user_delete", hard_delete: false },
        onUnauthorized,
      });
      if (selectedMemoryId === memoryId) {
        clearMemorySelection();
      }
      setGlobalSuccess("Memory deleted (soft delete).");
      await loadMemories();
    });
  };

  const runCorrection = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await withGuard(async () => {
      if (!token) throw new Error("Please login first.");
      const response = await apiRequest<{ message: string }>("/update-memory", {
        method: "POST",
        token,
        body: { text: correctionText },
        onUnauthorized,
      });
      setGlobalSuccess(response.message || "Correction processed.");
      setCorrectionText("");
      await loadMemories();
      clearMemorySelection();
    });
  };

  const loadHistory = async (memoryId: number) => {
    await withGuard(async () => {
      if (!token) throw new Error("Please login first.");
      const rows = await apiRequest<MemoryHistoryRow[]>(`/memories/${memoryId}/history`, {
        token,
        onUnauthorized,
      });
      setSelectedMemoryId(memoryId);
      setMemoryHistory(rows);
    });
  };

  const runSummary = async (query: string) => {
    await withGuard(async () => {
      if (!token) throw new Error("Please login first.");
      const response = await apiRequest<SummaryResponse>("/summarize", {
        method: "POST",
        token,
        body: { query },
        onUnauthorized,
      });
      setSummaryData(response);
    });
  };

  const refreshInsights = async () => {
    await withGuard(async () => {
      if (!token) throw new Error("Please login first.");
      const response = await apiRequest<InsightResponse>("/insights", {
        token,
        onUnauthorized,
      });
      setInsightData(response);
    });
  };

  const runAgent = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await withGuard(async () => {
      if (!token) throw new Error("Please login first.");
      if (!agentText.trim()) throw new Error("Type a request for the agent.");
      const response = await apiRequest<unknown>("/agent", {
        method: "POST",
        token,
        body: { text: agentText },
        onUnauthorized,
      });
      setAgentData((response as AgentGenericResponse) ?? null);
    });
  };

  const renderAgentResponse = () => {
    if (!agentData) {
      return <p className={styles.smallLabel}>No response yet.</p>;
    }

    const intent = agentData.intent ? String(agentData.intent) : "unknown";
    const hasSearch = "query" in agentData && "answer" in agentData && Array.isArray((agentData as AgentSearchResponse).results);
    const hasSummary = "summary" in agentData && "period" in agentData;
    const hasInsight = "insight" in agentData && "most_common_type" in agentData;
    const hasStore = "status" in agentData && "memory_id" in agentData;

    return (
      <div className={styles.agentResponseWrap}>
        <div className={styles.filterChips}>
          <span className={styles.chip}>intent: {intent}</span>
        </div>

        {hasSearch && (() => {
          const data = agentData as AgentSearchResponse;
          return (
            <div className={styles.resultBox}>
              <p><strong>Answer:</strong> {data.answer}</p>
              <p className={styles.smallLabel}>Results: {data.results.length}</p>
              <ul className={styles.memoryList}>
                {data.results.slice(0, 5).map((row) => (
                  <li key={row.id}>
                    <strong>{row.date}</strong> {row.time} | {row.type} | {row.content}
                  </li>
                ))}
              </ul>
            </div>
          );
        })()}

        {hasSummary && (() => {
          const data = agentData as AgentSummaryResponse;
          return (
            <div className={styles.resultBox}>
              <p>{data.summary}</p>
              <p className={styles.smallLabel}>Count: {data.count}</p>
              <p className={styles.smallLabel}>Period: {data.period.start_date} to {data.period.end_date}</p>
            </div>
          );
        })()}

        {hasInsight && (() => {
          const data = agentData as AgentInsightResponse;
          return (
            <div className={styles.gridCards}>
              <div className={styles.statCard}><p className={styles.smallLabel}>Most common type</p><p>{data.most_common_type ?? "-"}</p></div>
              <div className={styles.statCard}><p className={styles.smallLabel}>Most productive time</p><p>{data.most_productive_time ?? "-"}</p></div>
              <div className={styles.statCard}><p className={styles.smallLabel}>Trend</p><p>{data.trend}</p></div>
              <div className={styles.statCard}><p className={styles.smallLabel}>Repeated mistakes</p><p>{data.repeated_mistakes.join(", ") || "None"}</p></div>
              <div className={`${styles.statCard} ${styles.statWide}`}><p className={styles.smallLabel}>Narrative</p><p>{data.insight}</p></div>
            </div>
          );
        })()}

        {hasStore && (() => {
          const data = agentData as AgentStoreResponse;
          return (
            <div className={styles.resultBox}>
              <p><strong>Memory saved</strong> (ID: {data.memory_id})</p>
              <p className={styles.smallLabel}>{data.data?.date} {data.data?.time} | {data.data?.type}</p>
              <p>{data.data?.content}</p>
            </div>
          );
        })()}

        {!hasSearch && !hasSummary && !hasInsight && !hasStore && (
          <div className={styles.resultBox}>
            <p>{agentData.message ?? "I didn't understand."}</p>
            {agentData.hint && <p className={styles.smallLabel}>{agentData.hint}</p>}
            <div className={styles.inlineButtons}>
              <button className={styles.secondaryBtn} type="button" onClick={() => setAgentText("What did I do today?")}>Try search</button>
              <button className={styles.secondaryBtn} type="button" onClick={() => setAgentText("Summarize this week")}>Try summary</button>
              <button className={styles.secondaryBtn} type="button" onClick={() => setAgentText("Show my insights")}>Try insights</button>
            </div>
          </div>
        )}
      </div>
    );
  };

  const loadMetrics = async () => {
    await withGuard(async () => {
      if (!token) throw new Error("Please login first.");
      const response = await apiRequest<EvalMetrics>("/evaluation/metrics", {
        token,
        onUnauthorized,
      });
      setMetricsData(response);
    });
  };

  const postSampleMetrics = async () => {
    await withGuard(async () => {
      if (!token) throw new Error("Please login first.");
      const response = await apiRequest<EvalMetrics>("/evaluation/metrics", {
        method: "POST",
        token,
        body: {
          samples: [
            { retrieval_precision: 0.8, response_correctness: 0.9, context_followup_correctness: 1.0, context_application_rate: 1.0 },
            { retrieval_precision: 0.7, response_correctness: 0.8, context_followup_correctness: 0.5, context_application_rate: 0.5 },
          ],
        },
        onUnauthorized,
      });
      setMetricsData(response);
      setGlobalSuccess("Sample evaluation posted.");
    });
  };

  const exportReport = async () => {
    await withGuard(async () => {
      if (!token) throw new Error("Please login first.");
      const response = await apiRequest<ExportReportResponse>("/evaluation/export-report", {
        method: "POST",
        token,
        body: { report_name: reportName },
        onUnauthorized,
      });
      setExportData(response);
      setGlobalSuccess("Evaluation report exported.");
    });
  };

  const runContextScenario = async () => {
    await withGuard(async () => {
      if (!token) throw new Error("Please login first.");
      const response = await apiRequest<ContextScenarioResponse>("/evaluation/run-context-scenario", {
        method: "POST",
        token,
        onUnauthorized,
      });
      setContextScenarioData(response);
      const history = await apiRequest<ContextScenarioHistoryResponse>("/evaluation/context-scenario-history?limit=8", {
        token,
        onUnauthorized,
      });
      setContextScenarioHistory(history);
      setGlobalSuccess("Context scenario completed.");
    });
  };

  const loadContextScenarioHistory = async () => {
    await withGuard(async () => {
      if (!token) throw new Error("Please login first.");
      const history = await apiRequest<ContextScenarioHistoryResponse>("/evaluation/context-scenario-history?limit=8", {
        token,
        onUnauthorized,
      });
      setContextScenarioHistory(history);
    });
  };

  const asPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

  const checkHealth = async () => {
    await withGuard(async () => {
      const [root, live, ready] = await Promise.all([
        apiRequest<HealthPayload>("/", { method: "GET" }),
        apiRequest<HealthPayload>("/health/live", { method: "GET" }),
        apiRequest<HealthPayload>("/health/ready", { method: "GET" }),
      ]);
      setRootData(root);
      setLiveData(live);
      setReadyData(ready);
      setHealthCheckedAt(new Date().toLocaleString());
    });
  };

  const healthSignal = (payload: HealthPayload | null) => {
    if (!payload) return "unknown";
    const value = String(payload.status ?? payload.environment ?? "unknown").toLowerCase();
    if (value.includes("ready") || value.includes("alive") || value.includes("running") || value.includes("prod")) {
      return "healthy";
    }
    return "warning";
  };

  const viewButtons: Array<{ id: AppView; label: string }> = [
    { id: "home", label: "Home" },
    { id: "add", label: "Add Memory" },
    { id: "search", label: "Search" },
    { id: "memories", label: "Memories" },
    { id: "summaries", label: "Summaries" },
    { id: "insights", label: "Insights" },
    { id: "agent", label: "Agent" },
    { id: "evaluation", label: "Evaluation" },
    { id: "health", label: "Health" },
  ];

  const showComposer = activeView === "home" || activeView === "search";
  const selectedMemory = selectedMemoryId ? memories.find((memory) => memory.id === selectedMemoryId) ?? null : null;
  const showContextDiagnostics = process.env.NODE_ENV !== "production";

  if (!authHydrated) {
    return (
      <div className={styles.authShell}>
        <div className={styles.authCard}>
          <h1>AI Memory Doctor</h1>
          <p className={styles.authSubtitle}>Loading your session...</p>
        </div>
      </div>
    );
  }

  if (!token) {
    return (
      <div className={styles.authShell}>
        <div className={styles.authCard}>
          <h1>AI Memory Doctor</h1>
          <p className={styles.authSubtitle}>Create account or login to use all memory assistant features.</p>

          <div className={styles.authTabs}>
            <button
              type="button"
              className={`${styles.authTab} ${authMode === "login" ? styles.activeTab : ""}`}
              onClick={() => setAuthMode("login")}
            >
              Login
            </button>
            <button
              type="button"
              className={`${styles.authTab} ${authMode === "register" ? styles.activeTab : ""}`}
              onClick={() => setAuthMode("register")}
            >
              Register
            </button>
          </div>

          <form className={styles.formGrid} onSubmit={submitAuth}>
            <label>
              Email
              <input
                className={styles.textInput}
                type="email"
                value={authEmail}
                onChange={(e) => setAuthEmail(e.target.value)}
                required
              />
            </label>

            <label>
              Password
              <input
                className={styles.textInput}
                type="password"
                value={authPassword}
                minLength={8}
                onChange={(e) => setAuthPassword(e.target.value)}
                required
              />
            </label>

            <button className={styles.primaryBtn} type="submit" disabled={loading}>
              {loading ? "Please wait..." : authMode === "login" ? "Login" : "Create Account"}
            </button>
          </form>

          {globalError && <p className={styles.errorText}>{globalError}</p>}
          {globalSuccess && <p className={styles.successText}>{globalSuccess}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className={`${styles.shell} ${!sidebarOpen ? styles.sidebarCollapsed : ""}`}>
      <aside className={`${styles.sidebar} ${!sidebarOpen ? styles.sidebarHidden : ""}`}>
        <button className={styles.newChatButton} type="button" onClick={() => setActiveView("home")}>
          + New chat
        </button>

        <div className={styles.sidebarSection}>
          <p className={styles.sectionTitle}>Views</p>
          <ul className={styles.recentList}>
            {viewButtons.map((view) => (
              <li key={view.id}>
                <button
                  className={`${styles.recentItem} ${activeView === view.id ? styles.navActive : ""}`}
                  type="button"
                  onClick={() => setActiveView(view.id)}
                >
                  {view.label}
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className={styles.sidebarSection}>
          <p className={styles.sectionTitle}>Quick prompts</p>
          <ul className={styles.recentList}>
            {[
              "What did I do yesterday?",
              "Summarize this week",
              "Show my insights",
              "Actually I studied Java not Python",
            ].map((item) => (
              <li key={item}>
                <button
                  className={styles.recentItem}
                  type="button"
                  onClick={() => {
                    setSearchQuery(item);
                    setAgentText(item);
                    setSummaryQuery(item);
                    setActiveView("search");
                  }}
                >
                  {item}
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className={styles.userPill}>
          <span>{email}</span>
          <button type="button" className={styles.logoutBtn} onClick={signOut}>
            Logout
          </button>
        </div>
      </aside>

      <main className={styles.mainPanel}>
        <header className={styles.topBar}>
          <div className={styles.topBarLeft}>
            <button
              className={styles.sidebarToggle}
              type="button"
              onClick={() => setSidebarOpen((prev) => !prev)}
              aria-label={sidebarOpen ? "Hide sidebar" : "Show sidebar"}
            >
              {sidebarOpen ? "Hide" : "Show"}
            </button>
            <h1>AI Memory Doctor</h1>
          </div>
          <span className={styles.modelTag}>API: {API_BASE}</span>
        </header>

        <section className={styles.messages}>
          {globalError && <p className={styles.errorText}>{globalError}</p>}
          {globalSuccess && <p className={styles.successText}>{globalSuccess}</p>}

          {activeView === "home" && (
            <>
              <article className={styles.assistantMessage}>
                <h3>Main Workspace</h3>
                <p>Choose one action from the left sidebar. This screen stays focused and uncluttered.</p>
                <div className={styles.inlineButtons}>
                  <button className={styles.secondaryBtn} type="button" onClick={() => setActiveView("add")}>
                    Open Add Memory
                  </button>
                  <button className={styles.secondaryBtn} type="button" onClick={() => setActiveView("search")}>
                    Open Search
                  </button>
                  <button className={styles.secondaryBtn} type="button" onClick={() => setActiveView("memories")}>
                    Open Memory List
                  </button>
                </div>
              </article>

              <article className={styles.assistantMessage}>
                <h4>Recent Memories</h4>
                {memories.length === 0 ? (
                  <p>No memories yet.</p>
                ) : (
                  <ul className={styles.memoryList}>
                    {memories.slice(0, 5).map((memory) => (
                      <li key={memory.id}>
                        <strong>{memory.date}</strong> {memory.time} | {memory.type} | {memory.content}
                      </li>
                    ))}
                  </ul>
                )}
              </article>
            </>
          )}

          {activeView === "add" && (
            <article className={styles.assistantMessage}>
              <h3>Add Memory</h3>
              <p className={styles.smallLabel}>Quick capture: write memory and save.</p>
              <form className={styles.simpleAddForm} onSubmit={submitAddMemory}>
                <input
                  className={styles.textInput}
                  value={addContent}
                  onChange={(e) => setAddContent(e.target.value)}
                  placeholder="e.g., I drank coffee at 8:00"
                  required
                />
                <button className={styles.primaryBtn} type="submit" disabled={loading}>
                  Save
                </button>
              </form>

              <details className={styles.advancedRow}>
                <summary>Add optional time</summary>
                <input
                  className={styles.textInput}
                  type="time"
                  value={addTime}
                  onChange={(e) => setAddTime(e.target.value)}
                />
              </details>
            </article>
          )}

          {activeView === "search" && (
            <article className={styles.assistantMessage}>
              <h3>Search and Q&A</h3>
              <p className={styles.smallLabel}>Use the bottom composer to ask naturally, like ChatGPT.</p>

              {searchData && (
                <>
                  <div className={styles.userMessage}>{searchData.query}</div>
                  <div className={styles.resultBox}>
                    <p>
                      <strong>Answer:</strong> {searchData.answer}
                    </p>
                    {searchData.time_filters && (
                      <div className={styles.filterChips}>
                        {Object.entries(searchData.time_filters)
                          .filter(([, value]) => value)
                          .map(([key, value]) => (
                            <span key={key} className={styles.chip}>
                              {key}: {String(value)}
                            </span>
                          ))}
                      </div>
                    )}
                    <p className={styles.smallLabel}>Results: {searchData.results.length}</p>
                    <ul className={styles.memoryList}>
                      {searchData.results.slice(0, 5).map((row) => (
                        <li key={row.id}>
                          <strong>{row.date}</strong> {row.time} | {row.type} | {row.content}
                          <div className={styles.filterChips}>
                            <span className={styles.chip}>importance: {(row.importance_score ?? 0).toFixed(2)}</span>
                            {row.importance_reasons?.slice(0, 3).map((reason) => (
                              <span key={reason} className={styles.chip}>{reason}</span>
                            ))}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {showContextDiagnostics && searchData.context_meta && (
                    <div className={styles.debugPanel}>
                      <p className={styles.debugTitle}>Dev diagnostics: context engine</p>
                      <div className={styles.filterChips}>
                        <span className={styles.chip}>query_context_applied: {String(Boolean(searchData.context_meta.query_context_applied))}</span>
                        <span className={styles.chip}>temporal_context_applied: {String(Boolean(searchData.context_meta.temporal_context_applied))}</span>
                        <span className={styles.chip}>gate.reason: {searchData.context_meta.gate?.reason ?? "n/a"}</span>
                        <span className={styles.chip}>gate.confidence: {searchData.context_meta.gate?.confidence?.toFixed(3) ?? "0.000"}</span>
                        <span className={styles.chip}>gate.applied: {String(Boolean(searchData.context_meta.gate?.applied))}</span>
                      </div>
                    </div>
                  )}
                </>
              )}
            </article>
          )}

          {activeView === "memories" && (
            <>
              {!selectedMemoryId ? (
                <>
                  <article className={styles.assistantMessage}>
                    <h3>Memory Finder and CRUD</h3>
                    <p className={styles.smallLabel}>Designed for large memory volumes with filter, sort, pagination, and direct ID selection.</p>
                    <div className={styles.memoryToolbar}>
                      <label>
                        Keyword
                        <input
                          className={styles.textInput}
                          value={memoryFilterQuery}
                          onChange={(e) => {
                            setMemoryFilterQuery(e.target.value);
                            setMemoryPage(1);
                          }}
                          placeholder="Search by content, type, date, time, or id"
                        />
                      </label>
                      <label>
                        Type
                        <select
                          className={styles.textInput}
                          value={memoryFilterType}
                          onChange={(e) => {
                            setMemoryFilterType(e.target.value);
                            setMemoryPage(1);
                          }}
                        >
                          <option value="all">All</option>
                          {memoryTypes.map((type) => (
                            <option key={type} value={type}>
                              {type}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label>
                        Exact date
                        <input
                          className={styles.textInput}
                          type="date"
                          value={memoryExactDate}
                          onChange={(e) => {
                            setMemoryExactDate(e.target.value);
                            setMemoryPage(1);
                          }}
                        />
                      </label>
                      <label>
                        From
                        <input
                          className={styles.textInput}
                          type="date"
                          value={memoryDateFrom}
                          onChange={(e) => {
                            setMemoryDateFrom(e.target.value);
                            setMemoryPage(1);
                          }}
                        />
                      </label>
                      <label>
                        To
                        <input
                          className={styles.textInput}
                          type="date"
                          value={memoryDateTo}
                          onChange={(e) => {
                            setMemoryDateTo(e.target.value);
                            setMemoryPage(1);
                          }}
                        />
                      </label>
                      <label>
                        Sort
                        <select
                          className={styles.textInput}
                          value={memorySort}
                          onChange={(e) => {
                            setMemorySort(e.target.value as MemorySort);
                            setMemoryPage(1);
                          }}
                        >
                          <option value="newest">Newest first</option>
                          <option value="oldest">Oldest first</option>
                          <option value="type">By type</option>
                        </select>
                      </label>
                    </div>

                    <div className={styles.inlineButtons}>
                      <button className={styles.secondaryBtn} type="button" onClick={() => void withGuard(loadMemories)}>
                        Refresh list
                      </button>
                      <button
                        className={styles.secondaryBtn}
                        type="button"
                        onClick={() => {
                          setMemoryFilterQuery("");
                          setMemoryFilterType("all");
                          setMemoryExactDate("");
                          setMemoryDateFrom("");
                          setMemoryDateTo("");
                          setMemorySort("newest");
                          setMemoryPage(1);
                        }}
                      >
                        Clear filters
                      </button>
                    </div>

                    <div className={styles.inlineForm}>
                      <input
                        className={styles.textInput}
                        value={memoryFindId}
                        onChange={(e) => setMemoryFindId(e.target.value)}
                        placeholder="Jump to memory ID"
                      />
                      <button className={styles.secondaryBtn} type="button" onClick={findMemoryById}>
                        Select by ID
                      </button>
                    </div>

                    <p className={styles.smallLabel}>
                      Showing {pagedMemories.length} of {filteredMemories.length} filtered memories (total: {memories.length}).
                    </p>
                  </article>

                  <article className={styles.assistantMessage}>
                    {filteredMemories.length === 0 ? (
                      <p>No memories found.</p>
                    ) : (
                      <div className={styles.memoryCards}>
                        {pagedMemories.map((memory) => (
                          <div
                            key={memory.id}
                            className={`${styles.memoryCard} ${selectedMemoryId === memory.id ? styles.memoryCardActive : ""}`}
                          >
                            <p>
                              <strong>{memory.content}</strong>
                            </p>
                            <p className={styles.smallLabel}>
                              {memory.type} | {memory.date} {memory.time} | version {memory.version ?? 1}
                            </p>
                            <div className={styles.filterChips}>
                              <span className={styles.chip}>importance: {(memory.importance_score ?? 0).toFixed(2)}</span>
                              {memory.importance_reasons?.slice(0, 3).map((reason) => (
                                <span key={`${memory.id}-${reason}`} className={styles.chip}>{reason}</span>
                              ))}
                            </div>
                            <div className={styles.inlineButtons}>
                              <button
                                className={styles.secondaryBtn}
                                type="button"
                                onClick={() => {
                                  setSelectedMemoryId(memory.id);
                                  setEditContent(memory.content);
                                    setSelectedUpdateMode("manual");
                                }}
                              >
                                Select
                              </button>
                              <button className={styles.secondaryBtn} type="button" onClick={() => void loadHistory(memory.id)}>
                                History
                              </button>
                              <button className={styles.dangerBtn} type="button" onClick={() => void deleteMemory(memory.id)}>
                                Delete
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {filteredMemories.length > 0 && (
                      <div className={styles.paginationRow}>
                        <button
                          className={styles.secondaryBtn}
                          type="button"
                          onClick={() => setMemoryPage((prev) => Math.max(1, prev - 1))}
                          disabled={currentMemoryPage <= 1}
                        >
                          Previous
                        </button>
                        <p className={styles.smallLabel}>
                          Page {currentMemoryPage} of {totalMemoryPages}
                        </p>
                        <button
                          className={styles.secondaryBtn}
                          type="button"
                          onClick={() => setMemoryPage((prev) => Math.min(totalMemoryPages, prev + 1))}
                          disabled={currentMemoryPage >= totalMemoryPages}
                        >
                          Next
                        </button>
                      </div>
                    )}
                  </article>
                </>
              ) : (
                <>
                  <article className={styles.assistantMessage}>
                    <div className={styles.selectedPanelHeader}>
                      <div>
                        <h3>Edit Memory Workspace</h3>
                        <p className={styles.smallLabel}>
                          {selectedMemory
                            ? `ID ${selectedMemory.id} | ${selectedMemory.type} | ${selectedMemory.date} ${selectedMemory.time}`
                            : `ID ${selectedMemoryId}`}
                        </p>
                      </div>
                      <button
                        type="button"
                        className={styles.closeSelectionBtn}
                        onClick={clearMemorySelection}
                        aria-label="Deselect memory"
                      >
                        X
                      </button>
                    </div>

                    <div className={styles.inlineButtons}>
                      <button
                        className={styles.secondaryBtn}
                        type="button"
                        onClick={() => {
                          if (selectedMemoryId) {
                            void loadHistory(selectedMemoryId);
                          }
                        }}
                      >
                        Load history
                      </button>
                      <button
                        className={styles.dangerBtn}
                        type="button"
                        onClick={() => {
                          if (selectedMemoryId) {
                            void deleteMemory(selectedMemoryId);
                          }
                        }}
                      >
                        Delete selected
                      </button>
                    </div>

                    <div className={styles.modeTabs}>
                      <button
                        type="button"
                        className={`${styles.modeTab} ${selectedUpdateMode === "manual" ? styles.modeTabActive : ""}`}
                        onClick={() => setSelectedUpdateMode("manual")}
                      >
                        Manual edit
                      </button>
                      <button
                        type="button"
                        className={`${styles.modeTab} ${selectedUpdateMode === "natural" ? styles.modeTabActive : ""}`}
                        onClick={() => setSelectedUpdateMode("natural")}
                      >
                        Natural correction
                      </button>
                    </div>

                    {selectedUpdateMode === "manual" ? (
                      <form className={styles.formGrid} onSubmit={submitMemoryUpdate}>
                        <label>
                          Updated content
                          <textarea
                            className={styles.textArea}
                            value={editContent}
                            onChange={(e) => setEditContent(e.target.value)}
                          />
                        </label>
                        <label>
                          Reason
                          <input className={styles.textInput} value={editReason} onChange={(e) => setEditReason(e.target.value)} />
                        </label>
                        <button className={styles.primaryBtn} type="submit" disabled={loading}>
                          Update memory
                        </button>
                      </form>
                    ) : (
                      <form className={styles.formGrid} onSubmit={runCorrection}>
                        <label>
                          Correction sentence
                          <input
                            className={styles.textInput}
                            value={correctionText}
                            onChange={(e) => setCorrectionText(e.target.value)}
                            placeholder="Example: Actually I watched a YouTube video for 2 hours not today i see video for 2 hours"
                          />
                        </label>
                        <button className={styles.primaryBtn} type="submit" disabled={loading}>
                          Apply correction
                        </button>
                      </form>
                    )}
                  </article>

                  <article className={styles.assistantMessage}>
                    <h4>Selected Memory History</h4>
                    {memoryHistory.length === 0 ? (
                      <p>No history loaded. Click Load history above.</p>
                    ) : (
                      <ul className={styles.historyList}>
                        {memoryHistory.map((row) => (
                          <li key={row.id}>
                            <p>
                              <strong>{row.change_reason}</strong> at {new Date(row.changed_at).toLocaleString()}
                            </p>
                            <p className={styles.smallLabel}>Old: {row.old_content}</p>
                            <p className={styles.smallLabel}>New: {row.new_content}</p>
                          </li>
                        ))}
                      </ul>
                    )}
                  </article>
                </>
              )}
            </>
          )}

          {activeView === "summaries" && (
            <article className={styles.assistantMessage}>
              <h3>AI Summarization</h3>
              <p className={styles.smallLabel}>Write your own prompt. The backend will use Gemini when configured, otherwise it falls back to the built-in summary engine.</p>

              <form
                className={styles.summaryComposer}
                onSubmit={(event) => {
                  event.preventDefault();
                  void runSummary(summaryQuery);
                }}
              >
                <label>
                  Prompt
                  <textarea
                    className={styles.textArea}
                    value={summaryQuery}
                    onChange={(e) => setSummaryQuery(e.target.value)}
                    placeholder="Example: Summarize my week in a friendly tone and highlight the biggest patterns"
                  />
                </label>
                <button className={styles.primaryBtn} type="submit" disabled={loading}>
                  Generate summary
                </button>
              </form>

              <div className={styles.inlineButtons}>
                {[
                  "Summarize today in 3 bullets",
                  "Summarize this week and mention key habits",
                  "Give me a short monthly review",
                ].map((preset) => (
                  <button
                    key={preset}
                    className={styles.secondaryBtn}
                    type="button"
                    onClick={() => {
                      setSummaryQuery(preset);
                    }}
                  >
                    {preset}
                  </button>
                ))}
              </div>

              {summaryData && (
                <div className={styles.resultBox}>
                  <p>{summaryData.summary}</p>
                  <p className={styles.smallLabel}>
                    Engine: {summaryData.ai_used ? `AI (${summaryData.provider ?? "gemini"})` : "Fallback (rule-based)"}
                  </p>
                  <p className={styles.smallLabel}>Count: {summaryData.count}</p>
                  <p className={styles.smallLabel}>
                    Period: {summaryData.period.start_date} to {summaryData.period.end_date}
                  </p>
                </div>
              )}
            </article>
          )}

          {activeView === "insights" && (
            <article className={styles.assistantMessage}>
              <h3>Insights Dashboard</h3>
              <button className={styles.primaryBtn} type="button" onClick={() => void refreshInsights()} disabled={loading}>
                Refresh insights
              </button>

              {insightData ? (
                insightData.status === "insufficient_data" ? (
                  <div className={styles.resultBox}>
                    <p>{insightData.insight}</p>
                    <p className={styles.smallLabel}>Current memory count: {insightData.count}</p>
                    <div className={styles.inlineButtons}>
                      <button className={styles.secondaryBtn} type="button" onClick={() => setActiveView("add")}>
                        Add memories
                      </button>
                      <button className={styles.secondaryBtn} type="button" onClick={() => setActiveView("memories")}>
                        Open memory list
                      </button>
                    </div>
                  </div>
                ) : (
                <div className={styles.gridCards}>
                  <div className={styles.statCard}>
                    <p className={styles.smallLabel}>Most common type</p>
                    <p>{insightData.most_common_type ?? "-"}</p>
                  </div>
                  <div className={styles.statCard}>
                    <p className={styles.smallLabel}>Most productive time</p>
                    <p>{insightData.most_productive_time ?? "-"}</p>
                  </div>
                  <div className={styles.statCard}>
                    <p className={styles.smallLabel}>Trend</p>
                    <p>{insightData.trend}</p>
                  </div>
                  <div className={styles.statCard}>
                    <p className={styles.smallLabel}>Repeated mistakes</p>
                    <p>{insightData.repeated_mistakes.join(", ") || "None"}</p>
                  </div>
                  <div className={styles.statCard}>
                    <p className={styles.smallLabel}>Priority memories</p>
                    <p>{insightData.priority_count ?? 0}</p>
                    <p className={styles.smallLabel}>
                      {typeof insightData.priority_ratio === "number"
                        ? `${Math.round(insightData.priority_ratio * 100)}% of log`
                        : "No ratio yet"}
                    </p>
                  </div>
                  <div className={styles.statCard}>
                    <p className={styles.smallLabel}>Priority focus</p>
                    <p>{insightData.priority_focus ?? "-"}</p>
                    <p className={styles.smallLabel}>
                      {insightData.priority_highlights?.slice(0, 2).join(" | ") || "No priority highlights"}
                    </p>
                  </div>
                  <div className={`${styles.statCard} ${styles.statWide}`}>
                    <p className={styles.smallLabel}>Narrative</p>
                    <p>{insightData.insight}</p>
                  </div>
                </div>
                )
              ) : (
                <p>No insight data yet.</p>
              )}
            </article>
          )}

          {activeView === "agent" && (
            <article className={styles.assistantMessage}>
              <h3>Agent Orchestration</h3>
              <p className={styles.smallLabel}>Optional unified interface: send one sentence and backend routes intent (store/search/summarize/insight/update).</p>
              <form className={styles.inlineForm} onSubmit={runAgent}>
                <input
                  className={styles.textInput}
                  value={agentText}
                  onChange={(e) => setAgentText(e.target.value)}
                  placeholder="Type a natural request"
                  required
                />
                <button className={styles.primaryBtn} type="submit" disabled={loading}>
                  Run agent
                </button>
              </form>

              {renderAgentResponse()}
            </article>
          )}

          {activeView === "evaluation" && (
            <article className={styles.assistantMessage}>
              <h3>Evaluation and Report Export</h3>
              <p className={styles.smallLabel}>Track quality signals and export thesis-ready JSON/CSV reports.</p>
              <div className={styles.inlineButtons}>
                <button className={styles.primaryBtn} type="button" onClick={() => void loadMetrics()} disabled={loading}>
                  Load metrics
                </button>
                <button className={styles.secondaryBtn} type="button" onClick={() => void postSampleMetrics()} disabled={loading}>
                  Post sample metrics
                </button>
                <button className={styles.secondaryBtn} type="button" onClick={() => void runContextScenario()} disabled={loading}>
                  Run context scenario
                </button>
                <button className={styles.secondaryBtn} type="button" onClick={() => void loadContextScenarioHistory()} disabled={loading}>
                  Load context trend
                </button>
              </div>

              <div className={styles.inlineForm}>
                <input
                  className={styles.textInput}
                  value={reportName}
                  onChange={(e) => setReportName(e.target.value)}
                  placeholder="report name"
                />
                <button className={styles.primaryBtn} type="button" onClick={() => void exportReport()} disabled={loading}>
                  Export JSON + CSV
                </button>
              </div>

              {metricsData ? (
                <div className={styles.gridCards}>
                  <div className={styles.statCard}>
                    <p className={styles.smallLabel}>Classification accuracy</p>
                    <p className={styles.metricValue}>{asPercent(metricsData.classification_accuracy)}</p>
                  </div>
                  <div className={styles.statCard}>
                    <p className={styles.smallLabel}>Retrieval accuracy</p>
                    <p className={styles.metricValue}>{asPercent(metricsData.retrieval_accuracy)}</p>
                  </div>
                  <div className={styles.statCard}>
                    <p className={styles.smallLabel}>Response correctness</p>
                    <p className={styles.metricValue}>{asPercent(metricsData.response_correctness)}</p>
                  </div>
                  <div className={styles.statCard}>
                    <p className={styles.smallLabel}>Sample count</p>
                    <p className={styles.metricValue}>{metricsData.sample_count}</p>
                  </div>

                  {typeof metricsData.context_followup_accuracy === "number" && (
                    <div className={styles.statCard}>
                      <p className={styles.smallLabel}>Context follow-up accuracy</p>
                      <p className={styles.metricValue}>{asPercent(metricsData.context_followup_accuracy)}</p>
                    </div>
                  )}

                  {typeof metricsData.context_application_rate === "number" && (
                    <div className={styles.statCard}>
                      <p className={styles.smallLabel}>Context application rate</p>
                      <p className={styles.metricValue}>{asPercent(metricsData.context_application_rate)}</p>
                    </div>
                  )}

                  {(typeof metricsData.passed_cases === "number" || typeof metricsData.total_cases === "number") && (
                    <div className={`${styles.statCard} ${styles.statWide}`}>
                      <p className={styles.smallLabel}>Test pass status</p>
                      <p className={styles.metricValue}>
                        {(metricsData.passed_cases ?? 0)} / {(metricsData.total_cases ?? 0)} cases passed
                      </p>
                    </div>
                  )}

                  <div className={`${styles.resultBox} ${styles.statWide}`}>
                    <p className={styles.smallLabel}>Notes</p>
                    {metricsData.notes && metricsData.notes.length > 0 ? (
                      <ul className={styles.historyList}>
                        {metricsData.notes.map((note) => (
                          <li key={note}>{note}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className={styles.smallLabel}>No notes provided.</p>
                    )}
                  </div>
                </div>
              ) : (
                <div className={styles.resultBox}>
                  <p>No metrics loaded yet.</p>
                  <p className={styles.smallLabel}>Click Load metrics or Post sample metrics to populate the dashboard.</p>
                </div>
              )}

              {exportData ? (
                <div className={styles.resultBox}>
                  <p><strong>{exportData.message}</strong></p>
                  <div className={styles.filterChips}>
                    <span className={styles.chip}>JSON: {exportData.json_report}</span>
                    <span className={styles.chip}>CSV: {exportData.csv_report}</span>
                  </div>
                  <p className={styles.smallLabel}>
                    Export snapshot: {asPercent(exportData.metrics.classification_accuracy)} classification,
                    {" "}{asPercent(exportData.metrics.retrieval_accuracy)} retrieval,
                    {" "}{asPercent(exportData.metrics.response_correctness)} correctness,
                    {" "}{asPercent(exportData.metrics.context_application_rate ?? 0)} context-use.
                  </p>
                  {typeof exportData.metrics.passed_cases === "number" && typeof exportData.metrics.total_cases === "number" && (
                    <p className={styles.smallLabel}>
                      Case pass rate: {exportData.metrics.passed_cases}/{exportData.metrics.total_cases}
                    </p>
                  )}
                </div>
              ) : (
                <div className={styles.resultBox}>
                  <p>No export run yet.</p>
                  <p className={styles.smallLabel}>Run Export JSON + CSV to generate report files.</p>
                </div>
              )}

              {contextScenarioData ? (
                <div className={styles.resultBox}>
                  <p><strong>{contextScenarioData.message}</strong></p>
                  <p className={styles.smallLabel}>Seeded memories (temporary): {contextScenarioData.scenario.seed_count}</p>
                  <p className={styles.smallLabel}>First query: {contextScenarioData.scenario.first_query}</p>
                  <p className={styles.smallLabel}>Follow-up query: {contextScenarioData.scenario.followup_query}</p>
                  <div className={styles.filterChips}>
                    <span className={styles.chip}>first_results: {contextScenarioData.scenario.first_result_count}</span>
                    <span className={styles.chip}>followup_results: {contextScenarioData.scenario.followup_result_count}</span>
                    <span className={styles.chip}>gate.reason: {contextScenarioData.scenario.context_meta?.gate?.reason ?? "n/a"}</span>
                    <span className={styles.chip}>gate.confidence: {contextScenarioData.scenario.context_meta?.gate?.confidence?.toFixed(3) ?? "0.000"}</span>
                  </div>
                  <p className={styles.smallLabel}>
                    Scenario scores: follow-up correctness {asPercent(contextScenarioData.scores.context_followup_correctness)},
                    {" "}context application {asPercent(contextScenarioData.scores.context_application_rate)}.
                  </p>
                </div>
              ) : (
                <div className={styles.resultBox}>
                  <p>No context scenario run yet.</p>
                  <p className={styles.smallLabel}>Use Run context scenario to execute a real multi-turn test flow.</p>
                </div>
              )}

              {contextScenarioHistory ? (
                <div className={styles.resultBox}>
                  <p><strong>Context scenario trend</strong></p>
                  <div className={styles.filterChips}>
                    <span className={styles.chip}>runs: {contextScenarioHistory.count}</span>
                    <span className={styles.chip}>avg follow-up correctness: {asPercent(contextScenarioHistory.avg_context_followup_correctness ?? 0)}</span>
                  </div>

                  {contextScenarioHistory.items.length > 0 ? (
                    <ul className={styles.historyList}>
                      {contextScenarioHistory.items.slice().reverse().map((item) => (
                        <li key={item.run_id}>
                          <p>
                            <strong>{item.run_id}</strong> | {item.generated_at_utc ? new Date(item.generated_at_utc).toLocaleString() : "n/a"}
                          </p>
                          <p className={styles.smallLabel}>
                            follow-up: {asPercent(item.context_followup_correctness)} | app-rate: {asPercent(item.context_application_rate ?? 0)} |
                            reason: {item.gate_reason ?? "n/a"} | confidence: {(item.gate_confidence ?? 0).toFixed(3)}
                          </p>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className={styles.smallLabel}>No history items yet.</p>
                  )}
                </div>
              ) : (
                <div className={styles.resultBox}>
                  <p>No context trend loaded yet.</p>
                  <p className={styles.smallLabel}>Use Load context trend to see longitudinal behavior quality.</p>
                </div>
              )}
            </article>
          )}

          {activeView === "health" && (
            <article className={styles.assistantMessage}>
              <h3>Health and Operational Endpoints</h3>
              <p className={styles.smallLabel}>Quick operational checks to confirm API reachability, liveness, and readiness.</p>
              <button className={styles.primaryBtn} type="button" onClick={() => void checkHealth()} disabled={loading}>
                Check health
              </button>

              {healthCheckedAt && <p className={styles.smallLabel}>Last checked: {healthCheckedAt}</p>}

              <div className={styles.gridCards}>
                <div className={styles.statCard}>
                  <div className={styles.healthHeaderRow}>
                    <p className={styles.smallLabel}>Root (/)</p>
                    <span className={`${styles.healthBadge} ${styles[healthSignal(rootData)]}`}>
                      {healthSignal(rootData)}
                    </span>
                  </div>
                  {rootData ? (
                    <>
                      <p><strong>{rootData.message ?? "Service reachable"}</strong></p>
                      <div className={styles.filterChips}>
                        {rootData.version && <span className={styles.chip}>version: {rootData.version}</span>}
                        {rootData.environment && <span className={styles.chip}>env: {rootData.environment}</span>}
                      </div>
                    </>
                  ) : (
                    <p className={styles.smallLabel}>No data yet.</p>
                  )}
                </div>
                <div className={styles.statCard}>
                  <div className={styles.healthHeaderRow}>
                    <p className={styles.smallLabel}>Live (/health/live)</p>
                    <span className={`${styles.healthBadge} ${styles[healthSignal(liveData)]}`}>
                      {healthSignal(liveData)}
                    </span>
                  </div>
                  {liveData ? (
                    <p>
                      <strong>Status:</strong> {String(liveData.status ?? "unknown")}
                    </p>
                  ) : (
                    <p className={styles.smallLabel}>No data yet.</p>
                  )}
                </div>
                <div className={styles.statCard}>
                  <div className={styles.healthHeaderRow}>
                    <p className={styles.smallLabel}>Ready (/health/ready)</p>
                    <span className={`${styles.healthBadge} ${styles[healthSignal(readyData)]}`}>
                      {healthSignal(readyData)}
                    </span>
                  </div>
                  {readyData ? (
                    <p>
                      <strong>Status:</strong> {String(readyData.status ?? "unknown")}
                    </p>
                  ) : (
                    <p className={styles.smallLabel}>No data yet.</p>
                  )}
                </div>

                <div className={`${styles.resultBox} ${styles.statWide}`}>
                  <p className={styles.smallLabel}>How to read these checks</p>
                  <ul className={styles.historyList}>
                    <li><strong>Root</strong> confirms API is reachable and shows service metadata.</li>
                    <li><strong>Live</strong> confirms process is running (basic heartbeat).</li>
                    <li><strong>Ready</strong> confirms service is ready to accept traffic and dependencies are available.</li>
                  </ul>
                </div>
              </div>
            </article>
          )}
        </section>

        {showComposer && (
          <footer className={styles.composerWrap}>
            <div className={styles.composer}>
              <input
                className={styles.input}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Message AI Memory Doctor..."
                aria-label="Quick search"
              />
              <button
                className={styles.sendButton}
                type="button"
                onClick={() => void runQuickSearch()}
              >
                Search
              </button>
            </div>
            <p className={styles.helperText}>All modules are wired to backend endpoints with auth and 401 handling.</p>
          </footer>
        )}
      </main>
    </div>
  );
}
