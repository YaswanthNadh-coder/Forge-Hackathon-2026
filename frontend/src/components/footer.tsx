import Link from "next/link";
import { ShieldAlert, HeartHandshake } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 py-10 mt-auto">
      <div className="container mx-auto px-4 sm:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <div>
            <div className="flex items-center space-x-2 mb-3">
              <ShieldAlert className="h-5 w-5 text-blue-600" />
              <span className="font-bold text-slate-900 dark:text-slate-100">Ayushman-Shield</span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed mb-4">
              Autonomous, zero-dummy-data public governance AI agent built to protect 55+ crore Ayushman Bharat PM-JAY beneficiaries from illegal out-of-pocket hospital overbilling.
            </p>
            <p className="text-[11px] text-slate-500">
              Forge Gen AI Buildathon 2026 • Theme 1: Civic Pulse & Digital Governance
            </p>
          </div>

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900 dark:text-slate-200 mb-3">
              Official Regulatory Authorities
            </h4>
            <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-400">
              <li>
                <a href="https://nha.gov.in" target="_blank" rel="noreferrer" className="hover:text-blue-600 underline-offset-2 hover:underline">
                  National Health Authority (NHA)
                </a>
              </li>
              <li>
                <a href="https://cgrms.pmjay.gov.in" target="_blank" rel="noreferrer" className="hover:text-blue-600 underline-offset-2 hover:underline">
                  Central Grievance Redressal Management System (CGRMS)
                </a>
              </li>
              <li>
                <a href="https://hospitals.pmjay.gov.in" target="_blank" rel="noreferrer" className="hover:text-blue-600 underline-offset-2 hover:underline">
                  PM-JAY Hospital Empanelment Registry
                </a>
              </li>
              <li>
                <a href="https://nppaindia.nic.in" target="_blank" rel="noreferrer" className="hover:text-blue-600 underline-offset-2 hover:underline">
                  National Pharmaceutical Pricing Authority (NPPA Ceiling Rates)
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900 dark:text-slate-200 mb-3">
              Privacy & Legal Mandate
            </h4>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Patient PII (Aadhaar, Phone, Bank Account, ABHA) is redacted locally using Microsoft Presidio and OpenCV before multimodal LLM processing. Cross-audits enforce Section 4.2 of the NHA Empanelment Agreement against illegal cash collection.
            </p>
          </div>
        </div>

        <div className="pt-6 border-t border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500">
          <p>© 2026 Ayushman-Shield. MIT License.</p>
          <p className="flex items-center mt-2 sm:mt-0">
            Powered by LangGraph HITL • Gemini 2.5 Pro • Qdrant RAG • Sarvam AI • Playwright
          </p>
        </div>
      </div>
    </footer>
  );
}

