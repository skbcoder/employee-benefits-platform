"use client";

import { Suspense, useState, useEffect, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  submitEnrollment,
  getEnrollmentById,
  getEnrollmentByEmployee,
  getEnrollmentByName,
  getEnrollmentsByStatus,
  getProcessedEnrollmentById,
} from "@/lib/api";
import {
  BenefitSelection,
  BENEFIT_TYPES,
  PLAN_OPTIONS,
  EnrollmentStatus,
  EnrollmentSummary,
  ProcessedEnrollment,
} from "@/lib/types";
import StatusBadge from "@/components/StatusBadge";
import StatusTimeline from "@/components/StatusTimeline";

export default function EnrollmentPage() {
  return (
    <Suspense
      fallback={
        <div className="text-center py-12 text-gray-500">Loading...</div>
      }
    >
      <EnrollmentPageContent />
    </Suspense>
  );
}

type LookupMode = "enrollmentId" | "employeeId" | "employeeName";

function EnrollmentPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialTab = searchParams.get("tab") === "status" ? "status" : "enroll";
  const [activeTab, setActiveTab] = useState<"enroll" | "status">(initialTab);

  // Keep tab in sync with URL
  useEffect(() => {
    const tab = searchParams.get("tab") === "status" ? "status" : "enroll";
    setActiveTab(tab);
  }, [searchParams]);

  function switchTab(tab: "enroll" | "status") {
    setActiveTab(tab);
    if (tab === "status") {
      router.push("/enrollment?tab=status");
    } else {
      router.push("/enrollment");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Benefits Enrollment</h1>
        <p className="mt-1 text-sm text-gray-400">
          Submit new enrollments or check the status of existing ones.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-6 border-b border-gray-800">
        <button
          onClick={() => switchTab("enroll")}
          className={`pb-3 text-sm font-medium transition-colors ${
            activeTab === "enroll"
              ? "border-b-2 border-green-500 text-green-400"
              : "text-gray-500 hover:text-gray-300"
          }`}
        >
          Enroll
        </button>
        <button
          onClick={() => switchTab("status")}
          className={`pb-3 text-sm font-medium transition-colors ${
            activeTab === "status"
              ? "border-b-2 border-green-500 text-green-400"
              : "text-gray-500 hover:text-gray-300"
          }`}
        >
          Status
        </button>
      </div>

      {activeTab === "enroll" && <EnrollTab />}
      {activeTab === "status" && <StatusTab />}
    </div>
  );
}

/* ================================================================== */
/*  ENROLL TAB                                                         */
/* ================================================================== */

function EnrollTab() {
  const router = useRouter();
  const [employeeId, setEmployeeId] = useState("");
  const [employeeName, setEmployeeName] = useState("");
  const [employeeEmail, setEmployeeEmail] = useState("");
  const [selections, setSelections] = useState<BenefitSelection[]>([
    { type: "medical", plan: "gold" },
  ]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EnrollmentSummary | null>(null);

  function addSelection() {
    const usedTypes = new Set(selections.map((s) => s.type));
    const nextType = BENEFIT_TYPES.find((t) => !usedTypes.has(t));
    if (!nextType) return;
    setSelections([
      ...selections,
      { type: nextType, plan: PLAN_OPTIONS[nextType][0] },
    ]);
  }

  function removeSelection(index: number) {
    setSelections(selections.filter((_, i) => i !== index));
  }

  function updateSelection(
    index: number,
    field: keyof BenefitSelection,
    value: string
  ) {
    const updated = [...selections];
    if (field === "type") {
      updated[index] = { type: value, plan: PLAN_OPTIONS[value][0] };
    } else {
      updated[index] = { ...updated[index], [field]: value };
    }
    setSelections(updated);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const summary = await submitEnrollment({
        employeeId,
        employeeName,
        employeeEmail,
        selections,
      });
      setResult(summary);
    } catch (err) {
      setError("Unable to process your request. Please check your input and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (result) {
    return (
      <div className="space-y-6">
        <div className="rounded-xl border border-green-500/30 bg-green-500/10 p-6">
          <h2 className="text-xl font-semibold text-green-400">
            Enrollment Submitted
          </h2>
          <p className="mt-1 text-sm text-green-300/80">{result.message}</p>
        </div>

        <div className="rounded-xl border border-gray-800 bg-[#111118] p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-100">Enrollment Details</h3>
            <StatusBadge status={result.status} />
          </div>

          <div className="flex justify-center py-4">
            <StatusTimeline status={result.status} />
          </div>

          <dl className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-gray-500">Enrollment ID</dt>
              <dd className="font-mono text-gray-200">{result.enrollmentId}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Employee ID</dt>
              <dd className="text-gray-200">{result.employeeId}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Employee Name</dt>
              <dd className="text-gray-200">{result.employeeName}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Last Updated</dt>
              <dd className="text-gray-200">
                {new Date(result.updatedAt).toLocaleString()}
              </dd>
            </div>
          </dl>
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => {
              setResult(null);
              setEmployeeId("");
              setEmployeeName("");
              setEmployeeEmail("");
              setSelections([{ type: "medical", plan: "gold" }]);
            }}
            className="rounded-lg border border-gray-700 bg-[#111118] px-4 py-2 text-sm font-medium text-gray-300 hover:bg-gray-800"
          >
            Submit Another
          </button>
          <button
            onClick={() => router.push(`/enrollment?tab=status&id=${result.enrollmentId}`)}
            className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-500"
          >
            Track Status
          </button>
        </div>
      </div>
    );
  }

  const usedTypes = new Set(selections.map((s) => s.type));

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Employee info */}
        <div className="rounded-xl border border-gray-800 bg-[#111118] p-6 space-y-4">
          <h2 className="font-semibold text-gray-100">Employee Information</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="block text-sm font-medium text-gray-300">
                Employee ID *
              </label>
              <input
                type="text"
                required
                value={employeeId}
                onChange={(e) => setEmployeeId(e.target.value)}
                placeholder="E12345"
                className="mt-1 block w-full rounded-lg border border-gray-700 bg-[#0a0a0f] px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
              />
              <p className="mt-1 text-xs text-gray-600">Format: E##### or T##### (e.g., E12345)</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300">
                Full Name *
              </label>
              <input
                type="text"
                required
                value={employeeName}
                onChange={(e) => setEmployeeName(e.target.value)}
                placeholder="Jane Doe"
                className="mt-1 block w-full rounded-lg border border-gray-700 bg-[#0a0a0f] px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300">
                Email *
              </label>
              <input
                type="email"
                required
                value={employeeEmail}
                onChange={(e) => setEmployeeEmail(e.target.value)}
                placeholder="jane@company.com"
                className={`mt-1 block w-full rounded-lg border bg-[#0a0a0f] px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:ring-1 ${
                  employeeEmail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(employeeEmail)
                    ? "border-red-500/50 focus:border-red-500 focus:ring-red-500"
                    : "border-gray-700 focus:border-green-500 focus:ring-green-500"
                }`}
              />
              {employeeEmail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(employeeEmail) && (
                <p className="mt-1 text-xs text-red-400">Please enter a valid email address</p>
              )}
            </div>
          </div>
        </div>

        {/* Benefit selections */}
        <div className="rounded-xl border border-gray-800 bg-[#111118] p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-100">Benefit Selections</h2>
            {selections.length < BENEFIT_TYPES.length && (
              <button
                type="button"
                onClick={addSelection}
                className="rounded-lg border border-green-500/30 bg-green-500/10 px-3 py-1.5 text-sm font-medium text-green-400 hover:bg-green-500/20"
              >
                + Add Benefit
              </button>
            )}
          </div>

          {selections.length === 0 && (
            <p className="text-sm text-gray-500">
              Add at least one benefit selection.
            </p>
          )}

          <div className="space-y-3">
            {selections.map((sel, i) => (
              <div
                key={i}
                className="flex items-center gap-3 rounded-lg border border-gray-700/50 bg-[#0a0a0f] p-3"
              >
                <select
                  value={sel.type}
                  onChange={(e) => updateSelection(i, "type", e.target.value)}
                  className="rounded-lg border border-gray-700 bg-[#111118] px-3 py-2 text-sm text-gray-200 focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
                >
                  {BENEFIT_TYPES.filter(
                    (t) => t === sel.type || !usedTypes.has(t)
                  ).map((t) => (
                    <option key={t} value={t}>
                      {t.charAt(0).toUpperCase() + t.slice(1)}
                    </option>
                  ))}
                </select>
                <select
                  value={sel.plan}
                  onChange={(e) => updateSelection(i, "plan", e.target.value)}
                  className="rounded-lg border border-gray-700 bg-[#111118] px-3 py-2 text-sm text-gray-200 focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
                >
                  {PLAN_OPTIONS[sel.type]?.map((p) => (
                    <option key={p} value={p}>
                      {p.charAt(0).toUpperCase() + p.slice(1)}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={() => removeSelection(i)}
                  className="ml-auto rounded-lg p-1.5 text-gray-500 hover:bg-red-500/10 hover:text-red-400"
                  title="Remove"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        </div>

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting || selections.length === 0 || !employeeId.trim() || !employeeName.trim() || !employeeEmail.trim()}
          className="w-full rounded-lg bg-green-600 px-4 py-3 text-sm font-semibold text-white hover:bg-green-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "Submitting..." : "Submit Enrollment"}
        </button>
      </form>
    </div>
  );
}

/* ================================================================== */
/*  STATUS TAB                                                         */
/* ================================================================== */

const STATUS_FILTER_INFO: Record<string, { label: string; desc: string; bg: string; text: string; border: string }> = {
  SUBMITTED: {
    label: "Submitted",
    desc: "Enrollments that have been submitted and are awaiting dispatch.",
    bg: "bg-blue-500/10",
    text: "text-blue-400",
    border: "border-blue-500/30",
  },
  PROCESSING: {
    label: "Processing",
    desc: "Enrollments that have been dispatched and are being processed.",
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    border: "border-amber-500/30",
  },
  COMPLETED: {
    label: "Completed",
    desc: "Enrollments that have been fully processed and completed.",
    bg: "bg-green-500/10",
    text: "text-green-400",
    border: "border-green-500/30",
  },
};

function StatusTab() {
  const searchParams = useSearchParams();
  const statusFilter = searchParams.get("filter");
  const filterInfo = statusFilter ? STATUS_FILTER_INFO[statusFilter] : null;

  // List view state (when filter is active)
  const [filteredList, setFilteredList] = useState<EnrollmentSummary[]>([]);
  const [listLoading, setListLoading] = useState(false);
  const [listError, setListError] = useState<string | null>(null);
  const [listLoaded, setListLoaded] = useState(false);

  // Single enrollment detail state
  const [mode, setMode] = useState<LookupMode>("enrollmentId");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [enrollment, setEnrollment] = useState<EnrollmentSummary | null>(null);
  const [processing, setProcessing] = useState<ProcessedEnrollment | null>(null);
  const [autoSearchDone, setAutoSearchDone] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);

  // Auto-load list when filter changes
  useEffect(() => {
    if (!statusFilter || !STATUS_FILTER_INFO[statusFilter]) {
      setFilteredList([]);
      setListLoaded(false);
      return;
    }
    setListLoading(true);
    setListError(null);
    setListLoaded(false);
    getEnrollmentsByStatus(statusFilter)
      .then((list) => {
        setFilteredList(list);
        setListLoaded(true);
      })
      .catch((err) => {
        setListError("Unable to process your request. Please check your input and try again.");
        setListLoaded(true);
      })
      .finally(() => setListLoading(false));
  }, [statusFilter]);

  const handleSearch = useCallback(async (searchQuery?: string, searchMode?: LookupMode) => {
    const q = searchQuery ?? query;
    const m = searchMode ?? mode;
    if (!q.trim()) return;

    setError(null);
    setLoading(true);
    setEnrollment(null);
    setProcessing(null);

    try {
      let result: EnrollmentSummary;
      switch (m) {
        case "enrollmentId":
          result = await getEnrollmentById(q.trim());
          break;
        case "employeeId":
          result = await getEnrollmentByEmployee(q.trim());
          break;
        case "employeeName":
          result = await getEnrollmentByName(q.trim());
          break;
      }
      setEnrollment(result);
      setLastRefreshed(new Date());

      try {
        const proc = await getProcessedEnrollmentById(result.enrollmentId);
        setProcessing(proc);
      } catch {
        // Processing record may not exist yet
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Enrollment not found"
      );
    } finally {
      setLoading(false);
    }
  }, [query, mode]);

  useEffect(() => {
    if (autoSearchDone) return;
    const id = searchParams.get("id");
    if (id) {
      setQuery(id);
      setMode("enrollmentId");
      setAutoSearchDone(true);
      handleSearch(id, "enrollmentId");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, autoSearchDone]);

  function selectEnrollment(item: EnrollmentSummary) {
    setEnrollment(item);
    setProcessing(null);
    getProcessedEnrollmentById(item.enrollmentId)
      .then(setProcessing)
      .catch(() => {});
  }

  return (
    <div className="space-y-6">
      {/* Status filter banner */}
      {filterInfo && (
        <div className={`flex items-center justify-between rounded-xl border ${filterInfo.border} ${filterInfo.bg} p-4`}>
          <div className="flex items-center gap-3">
            <StatusBadge status={statusFilter as EnrollmentStatus} />
            <span className="text-sm text-gray-300">
              Showing enrollments with status: {filterInfo.label}
            </span>
          </div>
          <a
            href="/enrollment?tab=status"
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            Clear filter
          </a>
        </div>
      )}

      {/* Filtered list view */}
      {filterInfo && (
        <div className="space-y-3">
          {listLoading && (
            <div className="text-center py-8 text-gray-500">
              <svg className="mx-auto h-6 w-6 animate-spin text-gray-400 mb-2" fill="none" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2.5" opacity="0.25" />
                <path d="M12 3a9 9 0 0 1 9 9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
              </svg>
              Loading enrollments...
            </div>
          )}

          {listError && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
              {listError}
            </div>
          )}

          {listLoaded && !listError && filteredList.length === 0 && (
            <div className="rounded-xl border border-gray-800 bg-[#111118] p-8 text-center">
              <p className="text-gray-400">No enrollments with status &quot;{filterInfo.label}&quot; found.</p>
              <p className="mt-1 text-xs text-gray-600">Submit a new enrollment or check another status.</p>
            </div>
          )}

          {filteredList.length > 0 && (
            <div className="rounded-xl border border-gray-800 bg-[#111118] overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-800">
                <span className="text-sm font-medium text-gray-300">
                  {filteredList.length} enrollment{filteredList.length !== 1 ? "s" : ""}
                </span>
              </div>
              <div className="divide-y divide-gray-800/50">
                {filteredList.map((item) => (
                  <button
                    key={item.enrollmentId}
                    onClick={() => selectEnrollment(item)}
                    className={`w-full flex items-center justify-between px-4 py-3 text-left transition-colors hover:bg-gray-800/50 ${
                      enrollment?.enrollmentId === item.enrollmentId
                        ? "bg-green-500/10 border-green-500/30"
                        : ""
                    }`}
                  >
                    <div className="flex items-center gap-4 min-w-0">
                      <StatusBadge status={item.status} />
                      <div className="min-w-0">
                        <div className="text-sm font-medium text-gray-200 truncate">
                          {item.employeeName}
                        </div>
                        <div className="text-xs text-gray-500 truncate">
                          {item.employeeId} &middot; {item.enrollmentId.slice(0, 8)}...
                        </div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 shrink-0 ml-4">
                      {new Date(item.updatedAt).toLocaleDateString()}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Search */}
      <div className="rounded-xl border border-gray-800 bg-[#111118] p-6 space-y-4">
        <div className="flex gap-2">
          {(
            [
              ["enrollmentId", "Enrollment ID"],
              ["employeeId", "Employee ID"],
              ["employeeName", "Employee Name"],
            ] as const
          ).map(([value, label]) => (
            <button
              key={value}
              onClick={() => setMode(value)}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                mode === value
                  ? "bg-green-500/15 text-green-400"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-300"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSearch();
          }}
          className="flex gap-3"
        >
          <input
            type="text"
            required
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={
              mode === "enrollmentId"
                ? "Enter enrollment ID..."
                : mode === "employeeId"
                  ? "Enter employee ID (e.g. E12345)..."
                  : "Enter employee name..."
            }
            className="flex-1 rounded-lg border border-gray-700 bg-[#0a0a0f] px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-green-600 px-6 py-2 text-sm font-medium text-white hover:bg-green-500 disabled:opacity-50"
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </form>
        {lastRefreshed && <span className="text-xs text-gray-600">Updated {lastRefreshed.toLocaleTimeString()}</span>}
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Single enrollment detail */}
      {enrollment && (() => {
        const STATUS_ORDER: Record<string, number> = {
          SUBMITTED: 0,
          DISPATCH_FAILED: 0,
          PROCESSING: 1,
          COMPLETED: 2,
        };
        const enrollOrder = STATUS_ORDER[enrollment.status] ?? 0;
        const procOrder = processing ? (STATUS_ORDER[processing.status] ?? 0) : -1;
        const effectiveStatus: EnrollmentStatus =
          procOrder > enrollOrder
            ? (processing!.status as EnrollmentStatus)
            : enrollment.status;

        return (
        <div className="space-y-4">
          <div className="rounded-xl border border-gray-800 bg-[#111118] p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-gray-100">
                Enrollment Details
              </h2>
              <StatusBadge status={effectiveStatus} />
            </div>

            <div className="flex justify-center py-4">
              <StatusTimeline status={effectiveStatus} />
            </div>

            <dl className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <dt className="text-gray-500">Enrollment ID</dt>
                <dd className="font-mono text-gray-200">
                  {enrollment.enrollmentId}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500">Employee ID</dt>
                <dd className="text-gray-200">{enrollment.employeeId}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Employee Name</dt>
                <dd className="text-gray-200">{enrollment.employeeName}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Last Updated</dt>
                <dd className="text-gray-200">
                  {new Date(enrollment.updatedAt).toLocaleString()}
                </dd>
              </div>
            </dl>

            {enrollment.message && (
              <p className="text-sm text-gray-400 border-t border-gray-800 pt-3">
                {enrollment.message}
              </p>
            )}
          </div>

          {processing && (
            <div className="rounded-xl border border-gray-800 bg-[#111118] p-6 space-y-4">
              <h2 className="font-semibold text-gray-100">
                Processing Details
              </h2>
              <dl className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <dt className="text-gray-500">Processing Status</dt>
                  <dd className="text-gray-200">{processing.status}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">Last Updated</dt>
                  <dd className="text-gray-200">
                    {new Date(processing.updatedAt).toLocaleString()}
                  </dd>
                </div>
              </dl>
            </div>
          )}

          <button
            onClick={() => handleSearch(enrollment.enrollmentId, "enrollmentId")}
            disabled={loading}
            className="rounded-lg border border-gray-700 bg-[#111118] px-4 py-2 text-sm font-medium text-gray-300 hover:bg-gray-800 disabled:opacity-50"
          >
            Refresh Status
          </button>
        </div>
        );
      })()}
    </div>
  );
}
