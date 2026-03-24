const POLICIES = [
  { id: "enrollment_submit_review", description: "Log all enrollment submissions for audit trail", trigger: "enrollment / submit_enrollment", effect: "log", priority: 1 },
  { id: "enrollment_bulk_review", description: "Require approval for bulk enrollments (>3 selections)", trigger: "enrollment / submit_enrollment (>3 selections)", effect: "require_approval", priority: 10 },
  { id: "enrollment_pii_redact", description: "Redact SSN patterns in agent responses", trigger: "* / respond (SSN pattern)", effect: "redact", priority: 20 },
  { id: "block_ssn_exposure", description: "Block responses containing Social Security Numbers", trigger: "* / respond (SSN pattern)", effect: "deny", priority: 100 },
  { id: "redact_email_in_response", description: "Redact email addresses in agent responses", trigger: "* / respond (email pattern)", effect: "redact", priority: 90 },
  { id: "redact_phone_in_response", description: "Redact phone numbers in agent responses", trigger: "* / respond (phone pattern)", effect: "redact", priority: 80 },
  { id: "block_credit_card_exposure", description: "Block responses containing credit card numbers", trigger: "* / respond (credit card)", effect: "deny", priority: 100 },
  { id: "escalate_high_risk", description: "Require approval for high-risk actions (score > 0.8)", trigger: "* (risk_score > 0.8)", effect: "require_approval", priority: 50 },
  { id: "escalate_multiple_failures", description: "Require approval after multiple tool failures (>2)", trigger: "* (failed_tool_count > 2)", effect: "require_approval", priority: 40 },
  { id: "escalate_compliance_violation", description: "Require approval for compliance-related violations", trigger: "* (compliance violation)", effect: "require_approval", priority: 60 },
];

function effectBadgeClass(effect: string) {
  const styles: Record<string, string> = {
    allow: "bg-green-500/15 text-green-400",
    deny: "bg-red-500/15 text-red-400",
    redact: "bg-amber-500/15 text-amber-400",
    log: "bg-gray-500/15 text-gray-400",
    require_approval: "bg-blue-500/15 text-blue-400",
  };
  return styles[effect] || "bg-gray-500/15 text-gray-400";
}

function IconDocument({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
  );
}

export function PoliciesTab() {
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-gray-800 bg-[#111118] p-5">
        <div className="flex items-center gap-2 mb-2">
          <IconDocument className="h-5 w-5 text-blue-400" />
          <h3 className="text-sm font-semibold text-gray-200">Active Governance Policies</h3>
        </div>
        <p className="text-xs text-gray-500">
          These rules are evaluated on every AI agent action. Policies are defined in YAML configuration files and enforced by the governance service in real time.
        </p>
      </div>

      <div className="rounded-xl border border-gray-800 bg-[#111118] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-left text-xs text-gray-500">
                <th className="px-4 py-3 font-medium">Policy ID</th>
                <th className="px-4 py-3 font-medium">Description</th>
                <th className="px-4 py-3 font-medium">Trigger</th>
                <th className="px-4 py-3 font-medium">Effect</th>
                <th className="px-4 py-3 font-medium text-right">Priority</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/50">
              {POLICIES.sort((a, b) => a.priority - b.priority).map((p) => (
                <tr key={p.id} className="text-gray-300 hover:bg-gray-800/30">
                  <td className="px-4 py-3 font-mono text-xs text-gray-300">{p.id}</td>
                  <td className="px-4 py-3 text-xs text-gray-400 max-w-[280px]">{p.description}</td>
                  <td className="px-4 py-3 text-xs text-gray-500 font-mono max-w-[200px]">{p.trigger}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${effectBadgeClass(p.effect)}`}>
                      {p.effect}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500 font-mono text-right">P{p.priority}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
