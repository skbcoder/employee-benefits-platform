export interface PolicyDecision {
  allowed: boolean;
  effects: string[];
  matched_policies: Array<{
    policy_id: string;
    description: string;
    effect: string;
  }>;
  explanation: string;
}

export interface PiiDetection {
  pii_type: string;
  value: string;
}

export interface AuditEntry {
  id: string;
  timestamp: string;
  event_type: string;
  conversation_id: string;
  agent: string;
  action: string;
  request_summary: string;
  response_summary: string;
  risk_level: string;
  risk_score: number;
  policy_decisions: PolicyDecision[];
  pii_detected: PiiDetection[];
  client_ip: string;
  metadata: Record<string, unknown>;
}

export interface ApprovalRequest {
  id: string;
  conversation_id: string;
  agent: string;
  action: string;
  context: Record<string, unknown>;
  risk_level: string;
  risk_score: number;
  status: string;
  created_at: string;
  expires_at: string;
  reviewer: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
}

export type GovTab = "audit" | "approvals" | "compliance" | "policies";
