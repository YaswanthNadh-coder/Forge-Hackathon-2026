export interface ExtractedLineItem {
  id: string;
  description: string;
  category: "procedure" | "consumable" | "implant" | "bed_charge" | "diagnostic" | "medicine" | "other";
  quantity: number;
  unit_price: number;
  total_price: number;
  hbp_package_code?: string;
  hbp_package_name?: string;
}

export interface ExtractedBill {
  hospital_name: string;
  hospital_nabh?: string;
  patient_name: string;
  admission_date?: string;
  discharge_date?: string;
  total_billed: number;
  line_items: ExtractedLineItem[];
  raw_text?: string;
}

export interface AuditViolation {
  id: string;
  line_item_id: string;
  violation_type: "overbilling" | "double_billing" | "unbundling" | "rate_violation" | "package_inclusion" | "bed_cap_exceeded";
  severity: "critical" | "high" | "medium" | "low";
  description: string;
  billed_amount: number;
  allowed_amount: number;
  excess_amount: number;
  hbp_reference: string;
  evidence: string;
}

export interface AuditResult {
  id: string;
  status: "processing" | "extracting" | "verifying" | "auditing" | "generating_report" | "completed" | "error";
  bill?: ExtractedBill;
  violations: AuditViolation[];
  total_billed: number;
  total_allowed: number;
  total_excess: number;
  hospital_verified: boolean;
  hospital_tier: string;
  audit_score: number;
  pdf_report_url?: string;
  voice_explanation_url?: string;
  created_at?: string;
  error_message?: string;
}

export interface GrievanceStatus {
  stage: "idle" | "navigating" | "filling_form" | "awaiting_otp" | "otp_submitted" | "completed" | "error";
  message: string;
  screenshot_url?: string;
  grievance_id?: string;
  browser_frame?: string;
}

export interface GrievanceResponse {
  thread_id: string;
  status: GrievanceStatus;
}

export type Language = "en" | "hi" | "ta" | "te" | "kn" | "ml" | "bn" | "mr" | "gu" | "pa" | "or";

export const LANGUAGE_LABELS: Record<Language, string> = {
  en: "English",
  hi: "हिन्दी (Hindi)",
  ta: "தமிழ் (Tamil)",
  te: "తెలుగు (Telugu)",
  kn: "ಕನ್ನಡ (Kannada)",
  ml: "മലയാളം (Malayalam)",
  bn: "বাংলা (Bengali)",
  mr: "मराठी (Marathi)",
  gu: "ગુજરાતી (Gujarati)",
  pa: "ਪੰਜਾਬੀ (Punjabi)",
  or: "ଓଡ଼ିଆ (Odia)",
};

export const INDIAN_STATES = [
  "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
  "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
  "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
  "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
  "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
  "Uttar Pradesh", "Uttarakhand", "West Bengal",
  "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
  "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
];

