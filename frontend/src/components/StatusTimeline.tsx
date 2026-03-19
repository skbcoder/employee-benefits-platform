"use client";

import { EnrollmentStatus } from "@/lib/types";

const STEPS: { key: EnrollmentStatus; label: string }[] = [
  { key: "SUBMITTED", label: "Submitted" },
  { key: "PROCESSING", label: "Processing" },
  { key: "COMPLETED", label: "Completed" },
];

const ORDER: Record<EnrollmentStatus, number> = {
  SUBMITTED: 0,
  DISPATCH_FAILED: 0,
  PROCESSING: 1,
  COMPLETED: 2,
};

export default function StatusTimeline({
  status,
}: {
  status: EnrollmentStatus;
}) {
  const current = ORDER[status] ?? 0;
  const isFailed = status === "DISPATCH_FAILED";

  return (
    <div className="flex items-center gap-0">
      {STEPS.map((step, i) => {
        const done = i < current && !isFailed;
        const active = i === current && !isFailed;
        const isProcessing = active && status === "PROCESSING";
        const isCompleted = done || (active && status === "COMPLETED");
        const upcoming = i > current || isFailed;

        const delay = i * 150;

        return (
          <div key={step.key} className="flex items-center">
            {/* Connector line */}
            {i > 0 && (
              <div className="relative h-0.5 w-12 bg-gray-700/50">
                {(done || active) && !isFailed && (
                  <div
                    className="absolute inset-0 bg-green-500 animate-connector-fill"
                    style={{ animationDelay: `${delay - 100}ms` }}
                  />
                )}
              </div>
            )}

            {/* Step circle + label */}
            <div
              className="flex flex-col items-center gap-1.5 animate-step-enter"
              style={{ animationDelay: `${delay}ms` }}
            >
              <div
                className={`relative flex h-9 w-9 items-center justify-center rounded-full text-sm font-semibold transition-all duration-500 ${
                  isCompleted
                    ? "bg-green-500 text-white"
                    : isProcessing
                      ? "border-2 border-amber-400 text-amber-400 animate-step-pulse-amber"
                      : active
                        ? "border-2 border-green-500 text-green-400 animate-step-pulse"
                        : "border-2 border-gray-700 text-gray-500"
                }`}
              >
                {isCompleted ? (
                  <svg
                    className="h-4 w-4 animate-check-draw"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={3}
                    style={{ animationDelay: `${delay + 200}ms` }}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                ) : isProcessing ? (
                  <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2.5" opacity="0.25" />
                    <path d="M12 3a9 9 0 0 1 9 9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
                  </svg>
                ) : (
                  i + 1
                )}
              </div>
              <span
                className={`text-xs animate-fade-in-up ${
                  isCompleted
                    ? "font-medium text-green-400"
                    : isProcessing
                      ? "font-medium text-amber-400"
                      : active
                        ? "font-medium text-gray-200"
                        : "text-gray-500"
                }`}
                style={{ animationDelay: `${delay + 100}ms` }}
              >
                {step.label}
              </span>
            </div>
          </div>
        );
      })}

      {/* Failed indicator */}
      {isFailed && (
        <div className="flex items-center">
          <div className="relative h-0.5 w-12 bg-gray-700/50">
            <div className="absolute inset-0 bg-red-500/60 animate-connector-fill" />
          </div>
          <div
            className="flex flex-col items-center gap-1.5 animate-step-enter"
            style={{ animationDelay: "200ms" }}
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-red-500 text-white text-sm font-semibold animate-step-pulse-red">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <span className="text-xs font-medium text-red-400 animate-fade-in-up" style={{ animationDelay: "300ms" }}>
              Failed
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
