"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { submitEnrollment } from "@/lib/api";
import {
  BenefitSelection,
  BENEFIT_TYPES,
  PLAN_OPTIONS,
} from "@/lib/types";
import StatusBadge from "@/components/StatusBadge";
import StatusTimeline from "@/components/StatusTimeline";
import { EnrollmentSummary } from "@/lib/types";

export default function EnrollPage() {
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
      setError(err instanceof Error ? err.message : "Submission failed");
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
            onClick={() => router.push(`/status?id=${result.enrollmentId}`)}
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
      <div>
        <h1 className="text-2xl font-bold text-gray-100">
          New Benefits Enrollment
        </h1>
        <p className="mt-1 text-sm text-gray-400">
          Fill in employee details and select benefit plans.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Employee info */}
        <div className="rounded-xl border border-gray-800 bg-[#111118] p-6 space-y-4">
          <h2 className="font-semibold text-gray-100">Employee Information</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="block text-sm font-medium text-gray-300">
                Employee ID
              </label>
              <input
                type="text"
                required
                value={employeeId}
                onChange={(e) => setEmployeeId(e.target.value)}
                placeholder="E12345"
                className="mt-1 block w-full rounded-lg border border-gray-700 bg-[#0a0a0f] px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300">
                Full Name
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
                Email
              </label>
              <input
                type="email"
                required
                value={employeeEmail}
                onChange={(e) => setEmployeeEmail(e.target.value)}
                placeholder="jane@company.com"
                className="mt-1 block w-full rounded-lg border border-gray-700 bg-[#0a0a0f] px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
              />
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
          disabled={submitting || selections.length === 0}
          className="w-full rounded-lg bg-green-600 px-4 py-3 text-sm font-semibold text-white hover:bg-green-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "Submitting..." : "Submit Enrollment"}
        </button>
      </form>
    </div>
  );
}
