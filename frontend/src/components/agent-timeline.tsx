"use client";

import { CheckCircle2, Clock, AlertCircle, Loader2, ShieldCheck, FileSearch, Building2, Scale, FileText, Globe } from "lucide-react";
import { cn } from "@/lib/utils";

interface AgentTimelineProps {
  currentNode: string;
  status: string;
  totalExcess?: number;
  auditScore?: number;
}

const STEPS = [
  { id: "upload", label: "Local PII Redaction", icon: ShieldCheck, desc: "Masks Aadhaar, ABHA, Phone & Card numbers locally" },
  { id: "extract", label: "Multimodal Bill Extraction", icon: FileSearch, desc: "Gemini 2.5 Pro vision extracts all itemized line items" },
  { id: "verify", label: "Hospital Verification", icon: Building2, desc: "Verifies empanelment status & hospital tier" },
  { id: "audit", label: "NHA HBP 2022 Hybrid RAG", icon: Scale, desc: "Audits rates, bundled items, daily caps & implant ceilings" },
  { id: "report", label: "Evidence PDF & Vernacular Voice", icon: FileText, desc: "Generates legal annexure & Sarvam AI voice summary" },
];

export function AgentTimeline({ currentNode, status, totalExcess, auditScore }: AgentTimelineProps) {
  const getStepStatus = (stepId: string, index: number) => {
    const nodeOrder = ["upload", "extract", "verify", "audit", "report", "completed"];
    const currentIndex = nodeOrder.indexOf(currentNode);

    if (status === "completed" || currentIndex > index) {
      return "completed";
    }
    if (currentNode === stepId || (currentIndex === index && status !== "error")) {
      return "active";
    }
    if (status === "error" && currentNode === stepId) {
      return "error";
    }
    return "pending";
  };

  return (
    <div className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-100 dark:border-slate-800">
        <div>
          <h3 className="font-semibold text-slate-900 dark:text-slate-100 text-sm sm:text-base flex items-center space-x-2">
            <span>Autonomous Multi-Agent Audit Pipeline</span>
            {status === "processing" && (
              <span className="flex items-center text-xs font-normal text-blue-600 bg-blue-50 dark:bg-blue-950/40 px-2 py-0.5 rounded-full">
                <Loader2 className="w-3 h-3 mr-1 animate-spin" /> In Progress
              </span>
            )}
            {status === "completed" && (
              <span className="flex items-center text-xs font-normal text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-full">
                <CheckCircle2 className="w-3 h-3 mr-1" /> Audit Concluded
              </span>
            )}
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time LangGraph multi-agent execution state
          </p>
        </div>

        {status === "completed" && totalExcess !== undefined && (
          <div className="text-right">
            <span className="text-xs text-slate-500">Overcharge Detected:</span>
            <div className="text-sm font-bold text-red-600">
              ₹{totalExcess.toLocaleString("en-IN")}
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {STEPS.map((step, idx) => {
          const stepStatus = getStepStatus(step.id, idx);
          const Icon = step.icon;

          return (
            <div
              key={step.id}
              className={cn(
                "relative rounded-xl border p-4 transition-all duration-300 flex flex-col justify-between",
                stepStatus === "completed" && "border-emerald-200 dark:border-emerald-900/60 bg-emerald-50/50 dark:bg-emerald-950/20",
                stepStatus === "active" && "border-blue-500 dark:border-blue-500 bg-blue-50/60 dark:bg-blue-950/30 ring-2 ring-blue-500/20",
                stepStatus === "error" && "border-red-300 bg-red-50/50 dark:bg-red-950/20",
                stepStatus === "pending" && "border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40 opacity-70"
              )}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div
                    className={cn(
                      "w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold",
                      stepStatus === "completed" && "bg-emerald-600 text-white",
                      stepStatus === "active" && "bg-blue-600 text-white animate-pulse",
                      stepStatus === "error" && "bg-red-600 text-white",
                      stepStatus === "pending" && "bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                    )}
                  >
                    {stepStatus === "completed" ? (
                      <CheckCircle2 className="w-5 h-5" />
                    ) : stepStatus === "active" ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Icon className="w-4 h-4" />
                    )}
                  </div>
                  <span className="text-[10px] uppercase font-bold text-slate-400">Step {idx + 1}</span>
                </div>

                <h4 className="font-semibold text-xs text-slate-900 dark:text-slate-100 leading-tight mb-1">
                  {step.label}
                </h4>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  {step.desc}
                </p>
              </div>

              <div className="mt-3 pt-2 border-t border-slate-200/50 dark:border-slate-700/50 flex items-center justify-between text-[10px]">
                <span className="font-medium">
                  {stepStatus === "completed" && <span className="text-emerald-700 dark:text-emerald-400">Complete</span>}
                  {stepStatus === "active" && <span className="text-blue-700 dark:text-blue-400">Running...</span>}
                  {stepStatus === "pending" && <span className="text-slate-400">Queued</span>}
                  {stepStatus === "error" && <span className="text-red-600">Failed</span>}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

