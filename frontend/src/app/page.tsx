import { BillUpload } from "@/components/bill-upload";
import { Badge } from "@/components/ui/badge";
import {
  ShieldAlert,
  ShieldCheck,
  Scale,
  Volume2,
  Send,
  EyeOff,
  CheckCircle2,
  FileSearch,
  ExternalLink,
  Sparkles,
  Award,
} from "lucide-react";

export default function Home() {
  return (
    <div className="space-y-16 pb-20">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 sm:pt-20 pb-12 px-4 sm:px-8 border-b border-slate-200/80 dark:border-slate-800/80 bg-gradient-to-b from-blue-50/60 via-white to-transparent dark:from-slate-900/60 dark:via-slate-950 dark:to-transparent">
        <div className="container mx-auto max-w-5xl text-center space-y-6">
          <div className="inline-flex items-center space-x-2 bg-blue-100/80 dark:bg-blue-950/60 text-blue-800 dark:text-blue-300 px-4 py-1.5 rounded-full text-xs font-semibold border border-blue-200 dark:border-blue-800 shadow-xs">
            <Award className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
            <span>Forge Gen AI Buildathon 2026 • Theme 1: Civic Pulse & Digital Governance</span>
          </div>

          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-[1.15]">
            Autonomous PM-JAY Hospital Bill Auditor &{" "}
            <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 bg-clip-text text-transparent">
              CGRMS Grievance Agent
            </span>
          </h1>

          <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 max-w-3xl mx-auto leading-relaxed">
            Zero-dummy-data civic digital governance agent that ingests hospital bills, scrubs sensitive PII locally, cross-audits charges against the official National Health Authority (NHA) Health Benefit Package Master (HBP 2022), generates vernacular voice summaries via Sarvam AI, and files grievances on CGRMS with live browser automation.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-2 text-xs">
            <span className="inline-flex items-center px-3 py-1 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 mr-1.5 text-emerald-500" /> 1,118 Packages & 1,962 Procedures
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 font-medium">
              <ShieldCheck className="w-3.5 h-3.5 mr-1.5 text-blue-500" /> Local Presidio PII Masking
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 font-medium">
              <Sparkles className="w-3.5 h-3.5 mr-1.5 text-indigo-500" /> 11 Regional Indian Languages
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 font-medium">
              <Send className="w-3.5 h-3.5 mr-1.5 text-amber-500" /> Live CGRMS HITL Filing
            </span>
          </div>
        </div>
      </section>

      {/* Main Interactive Audit Upload Section */}
      <section className="container mx-auto px-4 sm:px-8">
        <BillUpload />
      </section>

      {/* Architectural Pillars Grid */}
      <section className="container mx-auto px-4 sm:px-8 pt-6">
        <div className="max-w-4xl mx-auto text-center mb-10">
          <Badge variant="outline" className="text-xs uppercase tracking-wider mb-2 border-slate-300">
            System Architecture
          </Badge>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            How Ayushman-Shield Enforces PM-JAY Cashless Rights
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Built strictly adhering to the National Health Authority guidelines with zero hardcoded dummy data
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {/* Pillar 1 */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-xl bg-blue-100 dark:bg-blue-950/50 text-blue-600 flex items-center justify-center mb-4">
                <EyeOff className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100 mb-2">
                1. Local Privacy Sanitization
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Microsoft Presidio and OpenCV redact sensitive identifiers (12-digit Aadhaar, 10-digit mobile, ABHA ID, PAN, bank accounts) locally on the edge before transmitting images to multimodal LLMs.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 text-[11px] text-blue-600 font-medium">
              Presidio + OpenCV • DPDP Compliant
            </div>
          </div>

          {/* Pillar 2 */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-xl bg-indigo-100 dark:bg-indigo-950/50 text-indigo-600 flex items-center justify-center mb-4">
                <Scale className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100 mb-2">
                2. Hybrid RAG Tariff Cross-Audit
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Qdrant hybrid vector & BM25 sparse search indexes the official NHA HBP 2022 Master. Detects unbundled consumables, double-billed diagnostics, tier rate violations, and ICU cap infractions.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 text-[11px] text-indigo-600 font-medium">
              Qdrant Hybrid • NHA HBP 2022
            </div>
          </div>

          {/* Pillar 3 */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-xl bg-amber-100 dark:bg-amber-950/50 text-amber-600 flex items-center justify-center mb-4">
                <Send className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100 mb-2">
                3. Live CGRMS HITL Grievance Filing
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                LangGraph orchestrates Playwright to navigate the live Central Grievance portal (cgrms.pmjay.gov.in), stream viewport frames over WebSockets, and halt via <code className="text-[10px] bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">interrupt_before</code> for human OTP entry.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 text-[11px] text-amber-600 font-medium">
              LangGraph StateGraph • Playwright
            </div>
          </div>
        </div>
      </section>

      {/* Statutory PM-JAY Regulations Table */}
      <section className="container mx-auto px-4 sm:px-8 pt-4">
        <div className="max-w-5xl mx-auto bg-slate-900 text-white rounded-3xl p-6 sm:p-8 border border-slate-800 shadow-xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-6 border-b border-slate-800">
            <div>
              <h3 className="text-lg font-bold">PM-JAY Beneficiary Cashless Protection Mandate</h3>
              <p className="text-xs text-slate-400 mt-1">
                Statutory bundling rules enforced automatically by Ayushman-Shield
              </p>
            </div>
            <a
              href="https://nha.gov.in"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center space-x-1 text-xs text-blue-400 hover:text-blue-300 font-medium"
            >
              <span>NHA Policy Documents</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-700/50">
              <span className="font-bold text-emerald-400 block mb-1">Section 4.2: 100% Cashless Mandate</span>
              <p className="text-slate-300 leading-relaxed">
                Empanelled Healthcare Providers (EHCPs) are strictly prohibited from collecting out-of-pocket cash from PM-JAY beneficiaries for registration, nursing, surgeon consultation, or patient meals.
              </p>
            </div>

            <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-700/50">
              <span className="font-bold text-emerald-400 block mb-1">Bundled Consumables & Diagnostics</span>
              <p className="text-slate-300 leading-relaxed">
                Surgical gloves, syringes, IV cannulas, drape packs, and standard pre-op/post-op routine diagnostics are 100% bundled into procedural package rates and cannot be billed additionally.
              </p>
            </div>

            <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-700/50">
              <span className="font-bold text-emerald-400 block mb-1">NPPA & NHA Notified Implant Ceilings</span>
              <p className="text-slate-300 leading-relaxed">
                Coronary stents (DES ₹34,125 incl. GST), knee implants, and pacemakers must strictly adhere to NPPA national price ceilings without hospital margin additions.
              </p>
            </div>

            <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-700/50">
              <span className="font-bold text-emerald-400 block mb-1">15-Day Post-Discharge Medications</span>
              <p className="text-slate-300 leading-relaxed">
                Hospitals are legally required to dispense 15 days of essential take-home medications at discharge completely free of cost to the Ayushman Bharat cardholder.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
