function IconWarning({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
    </svg>
  );
}

interface ServiceErrorProps {
  onRetry: () => void;
  context: string;
}

export function ServiceError({ onRetry, context }: ServiceErrorProps) {
  return (
    <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-6">
      <div className="flex items-center justify-center gap-3">
        <IconWarning className="h-6 w-6 text-amber-400" />
        <div className="text-center">
          <p className="text-amber-400 font-semibold">Governance Service Not Connected</p>
          <p className="mt-1 text-sm text-gray-500">
            The governance service at <span className="font-mono text-gray-400">localhost:8500</span> is not responding.
            {context && <span className="ml-1">Unable to load {context}.</span>}
          </p>
        </div>
      </div>
      <div className="mt-4 text-center">
        <button
          onClick={onRetry}
          className="rounded-lg bg-amber-500/10 px-5 py-2 text-sm font-medium text-amber-400 hover:bg-amber-500/20 transition-colors"
        >
          Retry Connection
        </button>
      </div>
    </div>
  );
}
