"use client";

import Link from "next/link";
import { ShieldAlert, FileText, ExternalLink, HelpCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function Header() {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md">
      <div className="container mx-auto flex h-16 items-center justify-between px-4 sm:px-8">
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-700 to-indigo-500 text-white shadow-md shadow-blue-500/20 group-hover:scale-105 transition-transform">
            <ShieldAlert className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg tracking-tight text-slate-900 dark:text-white">
                Ayushman-Shield
              </span>
              <Badge variant="outline" className="border-blue-600/30 text-blue-600 dark:text-blue-400 text-[10px] py-0 px-1.5 uppercase font-semibold">
                NHA HBP 2022
              </Badge>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 hidden sm:block">
              Autonomous PM-JAY Hospital Bill Auditor & CGRMS Grievance Agent
            </p>
          </div>
        </Link>

        <div className="flex items-center space-x-3">
          <a
            href="https://cgrms.pmjay.gov.in"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden md:inline-flex items-center space-x-1.5 text-xs text-slate-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800"
          >
            <span>Live CGRMS Portal</span>
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
          <a
            href="https://nha.gov.in"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:inline-flex items-center space-x-1 text-xs text-slate-600 dark:text-slate-400 hover:text-blue-600 transition-colors"
          >
            <span>NHA Official</span>
          </a>
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300">
            <span className="w-1.5 h-1.5 mr-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            Zero Dummy Data
          </span>
        </div>
      </div>
    </header>
  );
}

