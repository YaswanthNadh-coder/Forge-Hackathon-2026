"use client";

import { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Download,
  Volume2,
  Send,
  Building2,
  FileText,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  HelpCircle,
  TrendingDown,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AuditResult, AuditViolation } from "@/types";
import { getReportDownloadUrl } from "@/lib/api";

interface AuditDashboardProps {
  audit: AuditResult;
  onStartGrievance: () => void;
  isStartingGrievance: boolean;
  onOpenVoice: () => void;
}

export function AuditDashboard({
  audit,
  onStartGrievance,
  isStartingGrievance,
  onOpenVoice,
}: AuditDashboardProps) {
  const [expandedViolation, setExpandedViolation] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"violations" | "line_items">("violations");

  const totalBilled = Number(audit.total_billed || 0);
  const totalAllowed = Number(audit.total_allowed || 0);
  const totalExcess = Number(audit.total_excess || 0);
  const violations = audit.violations || [];
  const lineItems = audit.bill?.line_items || [];

  const getSeverityBadge = (sev: string) => {
    switch (sev.toLowerCase()) {
      case "critical":
        return <Badge variant="destructive" className="text-[10px] uppercase font-bold">Critical</Badge>;
      case "high":
        return <Badge className="bg-amber-600 text-white text-[10px] uppercase font-bold">High</Badge>;
      case "medium":
        return <Badge className="bg-yellow-500 text-slate-900 text-[10px] uppercase font-bold">Medium</Badge>;
      default:
        return <Badge variant="secondary" className="text-[10px] uppercase font-bold">Low</Badge>;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-emerald-600 bg-emerald-50 border-emerald-200";
    if (score >= 50) return "text-amber-600 bg-amber-50 border-amber-200";
    return "text-red-600 bg-red-50 border-red-200";
  };

  return (
    <div className="space-y-8">
      {/* Top Banner Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Total Hospital Charges */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Total Billed by Hospital
          </p>
          <div className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-2">
            ₹{totalBilled.toLocaleString("en-IN")}
          </div>
          <p className="text-[11px] text-slate-400 mt-1 flex items-center">
            <Building2 className="w-3.5 h-3.5 mr-1" />
            {audit.bill?.hospital_name || "EHCP Provider"}
          </p>
        </div>

        {/* Card 2: Permissible under PM-JAY */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Permissible (NHA HBP 2022)
          </p>
          <div className="text-2xl font-bold text-emerald-600 mt-2">
            ₹{totalAllowed.toLocaleString("en-IN")}
          </div>
          <p className="text-[11px] text-emerald-700/80 dark:text-emerald-400 mt-1 flex items-center">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
            Cashless Package Entitlement
          </p>
        </div>

        {/* Card 3: Illegal Overbilling */}
        <div className="bg-gradient-to-br from-red-500/10 via-red-500/5 to-transparent border border-red-200 dark:border-red-900/50 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-wider text-red-600 dark:text-red-400">
              Illegal Overbilling Detected
            </p>
            <ShieldAlert className="w-4 h-4 text-red-600" />
          </div>
          <div className="text-2xl font-bold text-red-600 dark:text-red-400 mt-2">
            ₹{totalExcess.toLocaleString("en-IN")}
          </div>
          <p className="text-[11px] text-red-600/80 dark:text-red-400 mt-1">
            Section 4.2 NHA Statutory Violation
          </p>
        </div>

        {/* Card 4: Compliance Score */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Hospital Compliance Score
            </p>
            <span className={`text-xs px-2 py-0.5 rounded-full font-bold border ${getScoreColor(audit.audit_score)}`}>
              {audit.audit_score} / 100
            </span>
          </div>
          <div className="w-full bg-slate-100 dark:bg-slate-800 h-2.5 rounded-full mt-4 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                audit.audit_score >= 80 ? "bg-emerald-500" : audit.audit_score >= 50 ? "bg-amber-500" : "bg-red-500"
              }`}
              style={{ width: `${Math.max(5, audit.audit_score)}%` }}
            />
          </div>
          <p className="text-[11px] text-slate-400 mt-2">
            {audit.audit_score < 60 ? "Severe statutory overcharges" : "Moderate rate alignment"}
          </p>
        </div>
      </div>

      {/* Action Toolbar */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center space-x-2 text-xs text-slate-600 dark:text-slate-400">
          <span className="font-semibold text-slate-900 dark:text-slate-100">Empanelment Status:</span>
          <Badge variant="outline" className="text-emerald-700 bg-emerald-50 border-emerald-200 text-xs py-0.5">
            Verified NHA Empanelled ({audit.hospital_tier.toUpperCase()})
          </Badge>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 w-full sm:w-auto">
          {/* Download Official Audit Annexure PDF */}
          <a
            href={getReportDownloadUrl(audit.id)}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 sm:flex-none"
          >
            <Button variant="outline" size="sm" className="w-full text-xs h-9">
              <Download className="w-4 h-4 mr-1.5" />
              Download Evidence PDF
            </Button>
          </a>

          {/* Vernacular Voice Explanation */}
          <Button
            variant="secondary"
            size="sm"
            onClick={onOpenVoice}
            className="flex-1 sm:flex-none text-xs h-9 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
          >
            <Volume2 className="w-4 h-4 mr-1.5 text-indigo-600" />
            Listen Voice Summary
          </Button>

          {/* File CGRMS Grievance */}
          <Button
            size="sm"
            onClick={onStartGrievance}
            disabled={isStartingGrievance || totalExcess <= 0}
            className="flex-1 sm:flex-none text-xs h-9 bg-blue-600 hover:bg-blue-700 text-white font-medium shadow-md shadow-blue-500/20"
          >
            <Send className="w-3.5 h-3.5 mr-1.5" />
            File CGRMS Grievance
          </Button>
        </div>
      </div>

      {/* Tabs: Violations List vs Full Itemized Line Items */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4 mb-6">
          <div className="flex space-x-2">
            <button
              onClick={() => setActiveTab("violations")}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition-colors cursor-pointer ${
                activeTab === "violations"
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
            >
              Statutory Violations ({violations.length})
            </button>
            <button
              onClick={() => setActiveTab("line_items")}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition-colors cursor-pointer ${
                activeTab === "line_items"
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
            >
              Extracted Line Items ({lineItems.length})
            </button>
          </div>

          <span className="text-xs text-slate-400 hidden sm:inline">
            Cross-Audited against NHA HBP 2022 Master
          </span>
        </div>

        {/* Tab 1: Violations */}
        {activeTab === "violations" && (
          <div className="space-y-3">
            {violations.length === 0 ? (
              <div className="text-center py-12 text-slate-500">
                <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
                <p className="font-semibold text-sm">No Statutory Violations Detected</p>
                <p className="text-xs mt-1">The charges conform to PM-JAY package tariff rates.</p>
              </div>
            ) : (
              violations.map((v, i) => {
                const isExpanded = expandedViolation === v.id;
                return (
                  <div
                    key={v.id || i}
                    className="border border-slate-200 dark:border-slate-800 rounded-2xl p-4 hover:border-slate-300 dark:hover:border-slate-700 transition-all bg-slate-50/50 dark:bg-slate-900/40"
                  >
                    <div
                      className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 cursor-pointer"
                      onClick={() => setExpandedViolation(isExpanded ? null : v.id)}
                    >
                      <div className="flex items-start space-x-3">
                        <div className="w-7 h-7 rounded-lg bg-red-100 dark:bg-red-950/40 text-red-600 flex items-center justify-center shrink-0 font-bold text-xs mt-0.5">
                          #{i + 1}
                        </div>
                        <div>
                          <div className="flex flex-wrap items-center gap-2 mb-1">
                            <span className="font-semibold text-sm text-slate-900 dark:text-slate-100">
                              {v.description}
                            </span>
                            {getSeverityBadge(v.severity)}
                            <Badge variant="outline" className="text-[10px] text-slate-500 border-slate-200">
                              {v.violation_type.replace(/_/g, " ")}
                            </Badge>
                          </div>
                          <p className="text-xs text-slate-500 font-mono">
                            HBP Reference: {v.hbp_reference}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center justify-between sm:justify-end space-x-6 border-t sm:border-t-0 pt-2 sm:pt-0 border-slate-200 dark:border-slate-800">
                        <div className="text-left sm:text-right">
                          <span className="text-[10px] uppercase tracking-wider text-slate-400 block">
                            Unauthorized Charge
                          </span>
                          <span className="font-bold text-sm text-red-600 dark:text-red-400">
                            +₹{Number(v.excess_amount).toLocaleString("en-IN")}
                          </span>
                        </div>
                        <div className="text-slate-400">
                          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </div>
                      </div>
                    </div>

                    {/* Expanded Evidence & Legal Rule Breakdown */}
                    {isExpanded && (
                      <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-800 text-xs space-y-3 animate-in fade-in-50 duration-200">
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-white dark:bg-slate-950 p-3 rounded-xl border border-slate-200/60 dark:border-slate-800">
                          <div>
                            <span className="text-[10px] text-slate-400 uppercase font-semibold">Billed Amount</span>
                            <p className="font-bold text-slate-800 dark:text-slate-200 mt-0.5">
                              ₹{Number(v.billed_amount).toLocaleString("en-IN")}
                            </p>
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-400 uppercase font-semibold">Allowed under PM-JAY</span>
                            <p className="font-bold text-emerald-600 mt-0.5">
                              ₹{Number(v.allowed_amount).toLocaleString("en-IN")}
                            </p>
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-400 uppercase font-semibold">Illegal Excess Out-of-Pocket</span>
                            <p className="font-bold text-red-600 mt-0.5">
                              ₹{Number(v.excess_amount).toLocaleString("en-IN")}
                            </p>
                          </div>
                        </div>

                        <div className="bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/30 p-3 rounded-xl">
                          <p className="font-semibold text-amber-900 dark:text-amber-200 mb-1 flex items-center">
                            <Info className="w-3.5 h-3.5 mr-1.5 text-amber-600" /> Statutory Evidence & Bundling Violation
                          </p>
                          <p className="text-amber-800/90 dark:text-amber-300/90 leading-relaxed">
                            {v.evidence}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        )}

        {/* Tab 2: Extracted Line Items */}
        {activeTab === "line_items" && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 dark:bg-slate-800/60 text-slate-700 dark:text-slate-300 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="p-3 rounded-l-lg">#</th>
                  <th className="p-3">Description</th>
                  <th className="p-3">Category</th>
                  <th className="p-3 text-right">Qty</th>
                  <th className="p-3 text-right">Unit Price</th>
                  <th className="p-3 text-right rounded-r-lg">Total Price</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {lineItems.map((item, idx) => (
                  <tr key={item.id || idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="p-3 text-slate-400 font-mono">{idx + 1}</td>
                    <td className="p-3 font-medium text-slate-900 dark:text-slate-100">{item.description}</td>
                    <td className="p-3">
                      <Badge variant="outline" className="text-[10px] uppercase font-semibold">
                        {item.category}
                      </Badge>
                    </td>
                    <td className="p-3 text-right font-mono">{item.quantity}</td>
                    <td className="p-3 text-right font-mono">₹{Number(item.unit_price).toLocaleString("en-IN")}</td>
                    <td className="p-3 text-right font-mono font-semibold text-slate-900 dark:text-slate-100">
                      ₹{Number(item.total_price).toLocaleString("en-IN")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

