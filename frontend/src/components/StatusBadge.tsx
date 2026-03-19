"use client";

import { EnrollmentStatus } from "@/lib/types";

const STATUS_CONFIG: Record<
  EnrollmentStatus,
  { label: string; bg: string; text: string; dot: string }
> = {
  SUBMITTED: {
    label: "Submitted",
    bg: "bg-blue-500/15",
    text: "text-blue-400",
    dot: "bg-blue-400",
  },
  DISPATCH_FAILED: {
    label: "Dispatch Failed",
    bg: "bg-red-500/15",
    text: "text-red-400",
    dot: "bg-red-400",
  },
  PROCESSING: {
    label: "Processing",
    bg: "bg-amber-500/15",
    text: "text-amber-400",
    dot: "bg-amber-400",
  },
  COMPLETED: {
    label: "Completed",
    bg: "bg-green-500/15",
    text: "text-green-400",
    dot: "bg-green-400",
  },
};

export default function StatusBadge({ status }: { status: EnrollmentStatus }) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.SUBMITTED;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium ${config.bg} ${config.text}`}
    >
      <span className={`h-2 w-2 rounded-full ${config.dot}`} />
      {config.label}
    </span>
  );
}
