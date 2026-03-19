export interface BenefitSelection {
  type: string;
  plan: string;
}

export interface EnrollmentRequest {
  employeeId: string;
  employeeName: string;
  employeeEmail: string;
  selections: BenefitSelection[];
}

export interface EnrollmentSummary {
  enrollmentId: string;
  employeeId: string;
  employeeName: string;
  status: EnrollmentStatus;
  updatedAt: string;
  message: string;
}

export type EnrollmentStatus =
  | "SUBMITTED"
  | "DISPATCH_FAILED"
  | "PROCESSING"
  | "COMPLETED";

export interface ProcessedEnrollment {
  enrollmentId: string;
  employeeId: string;
  employeeName: string;
  status: string;
  updatedAt: string;
}

export const BENEFIT_TYPES = ["medical", "dental", "vision", "life"] as const;

export const PLAN_OPTIONS: Record<string, string[]> = {
  medical: ["bronze", "silver", "gold", "platinum"],
  dental: ["basic", "premium"],
  vision: ["basic", "premium"],
  life: ["basic", "supplemental"],
};
