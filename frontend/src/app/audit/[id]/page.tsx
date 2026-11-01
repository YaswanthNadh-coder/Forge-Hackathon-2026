"use client";

import { useEffect, useState, use, Suspense, useRef, useCallback } from "react";
import Link from "next/link";
import { ArrowLeft, Loader2, AlertCircle, RefreshCw, Radio } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { AuditResult, GrievanceResponse } from "@/types";
import { getAuditResult, startGrievance, getWebSocketUrl } from "@/lib/api";
import { useWebSocket } from "@/hooks/use-websocket";
import { AgentTimeline } from "@/components/agent-timeline";
import { AuditDashboard } from "@/components/audit-dashboard";
import { VoicePlayer } from "@/components/voice-player";
import { BrowserStream } from "@/components/browser-stream";

interface AuditPageProps {
  params: Promise<{ id: string }>;
}

function AuditPageInner({ params }: AuditPageProps) {
  const resolvedParams = use(params);
  const auditId = resolvedParams.id;

  const [audit, setAudit] = useState<AuditResult | null>(null);
  const [currentNode, setCurrentNode] = useState<string>("extract");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const [showVoicePlayer, setShowVoicePlayer] = useState<boolean>(false);

  const [grievanceThreadId, setGrievanceThreadId] = useState<string | null>(null);
  const [isStartingGrievance, setIsStartingGrievance] = useState<boolean>(false);
  const [grievanceError, setGrievanceError] = useState<string | null>(null);

  const statusRef = useRef<string>("processing");

  const fetchAuditData = useCallback(async () => {
    try {
      const data = await getAuditResult(auditId);
      setAudit(data);
      statusRef.current = data.status;
      if (data.status === "completed") {
        setCurrentNode("completed");
      }
      setFetchError(null);
    } catch (err: any) {
      setFetchError(err.message || "Failed to load audit results.");
    } finally {
      setIsLoading(false);
    }
  }, [auditId]);

  useEffect(() => {
    fetchAuditData();
    const interval = setInterval(() => {
      if (
        statusRef.current === "processing" ||
        statusRef.current === "extracting" ||
        statusRef.current === "verifying" ||
        statusRef.current === "auditing" ||
        statusRef.current === "generating_report"
      ) {
        fetchAuditData();
      }
    }, 2500);
    return () => clearInterval(interval);
  }, [fetchAuditData]);

  const isTerminalStatus =
    audit?.status === "completed" || audit?.status === "error";

  const { isConnected } = useWebSocket({
    url: isTerminalStatus ? null : getWebSocketUrl(auditId),
    autoReconnect: !isTerminalStatus,
    onMessage: (msg) => {
      if (msg.type === "node_complete") {
        setCurrentNode(msg.node || msg.current_node);
        fetchAuditData();
      } else if (msg.type === "audit_complete") {
        setCurrentNode("completed");
        fetchAuditData();
      } else if (msg.type === "error") {
        fetchAuditData();
      }
    },
  });

  const handleStartGrievance = async () => {
    setIsStartingGrievance(true);
    setGrievanceError(null);
    try {
      const res: GrievanceResponse = await startGrievance(auditId);
      setGrievanceThreadId(res.thread_id);
    } catch (err: any) {
      setGrievanceError(err.message || "Could not launch CGRMS browser agent.");
    } finally {
      setIsStartingGrievance(false);
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-20 flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
        <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
          Loading Ayushman-Shield Audit Workspace...
        </p>
        <p className="text-xs text-slate-500 font-mono">Session ID: {auditId}</p>
      </div>
    );
  }

  if (fetchError && !audit) {
    return (
      <div className="container mx-auto px-4 py-20 max-w-xl">
        <Alert variant="destructive" className="rounded-2xl">
          <AlertCircle className="w-5 h-5" />
          <AlertTitle className="text-sm font-bold">Audit Session Not Found</AlertTitle>
          <AlertDescription className="text-xs mt-1">
            {fetchError}
          </AlertDescription>
        </Alert>
        <div className="mt-6 flex justify-center">
          <Link href="/">
            <Button variant="outline" size="sm" className="text-xs">
              <ArrowLeft className="w-4 h-4 mr-1.5" /> Return to Upload
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 sm:px-8 py-8 space-y-8 max-w-6xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center space-x-3">
          <Link href="/">
            <Button variant="outline" size="icon" className="w-9 h-9 rounded-xl">
              <ArrowLeft className="w-4 h-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                Audit Workspace
              </h1>
              <span className="font-mono text-xs text-slate-500">#{auditId.slice(0, 8).toUpperCase()}</span>
            </div>
            <p className="text-xs text-slate-500">
              {audit?.bill?.hospital_name || "Hospital Bill Audit"} • PM-JAY Compliance Evaluation
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Badge
            variant="outline"
            className={`text-[10px] ${
              isConnected
                ? "border-emerald-500/40 text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/20"
                : "border-slate-300 text-slate-500"
            }`}
          >
            <Radio className="w-2.5 h-2.5 mr-1" />
            {isConnected ? "WS Live Stream" : "Polling"}
          </Badge>
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchAuditData}
            className="text-xs h-8 px-2 text-slate-600 hover:text-slate-900"
          >
            <RefreshCw className="w-3.5 h-3.5 mr-1" /> Refresh
          </Button>
        </div>
      </div>

      <AgentTimeline
        currentNode={currentNode}
        status={audit?.status || "processing"}
        totalExcess={audit ? Number(audit.total_excess) : undefined}
        auditScore={audit?.audit_score}
      />

      {(showVoicePlayer || (audit && audit.status === "completed")) && (
        <VoicePlayer auditId={auditId} defaultLanguage="hi" />
      )}

      {audit && (
        <AuditDashboard
          audit={audit}
          onStartGrievance={handleStartGrievance}
          isStartingGrievance={isStartingGrievance}
          onOpenVoice={() => setShowVoicePlayer(true)}
        />
      )}

      {grievanceError && (
        <Alert variant="destructive" className="rounded-2xl">
          <AlertCircle className="w-4 h-4" />
          <AlertDescription className="text-xs">{grievanceError}</AlertDescription>
        </Alert>
      )}

      {grievanceThreadId && (
        <div className="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-base text-slate-900 dark:text-slate-100 flex items-center space-x-2">
                <span>Central Grievance Redressal (CGRMS) Portal Session</span>
                <Badge className="bg-blue-600 text-[10px] uppercase">Active Session</Badge>
              </h3>
              <p className="text-xs text-slate-500">
                Playwright browser is automating form entry against https://cgrms.pmjay.gov.in
              </p>
            </div>
            <span className="font-mono text-xs text-slate-400">Thread: {grievanceThreadId.slice(0, 8)}</span>
          </div>

          <BrowserStream
            threadId={grievanceThreadId}
            onCompleted={(id) => {
              console.log("Grievance registered successfully:", id);
            }}
          />
        </div>
      )}
    </div>
  );
}

export default function AuditPage({ params }: AuditPageProps) {
  return (
    <Suspense
      fallback={
        <div className="container mx-auto px-4 py-20 flex flex-col items-center justify-center space-y-4">
          <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
          <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
            Initializing Audit Workspace...
          </p>
        </div>
      }
    >
      <AuditPageInner params={params} />
    </Suspense>
  );
}
