"use client";

import { useState } from "react";
import { Monitor, KeyRound, CheckCircle2, AlertTriangle, ShieldAlert, Radio, Loader2, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { submitOtp, getBrowserStreamUrl } from "@/lib/api";
import { useWebSocket } from "@/hooks/use-websocket";

interface BrowserStreamProps {
  threadId: string;
  initialFrame?: string;
  initialStage?: string;
  onCompleted?: (grievanceId: string) => void;
}

export function BrowserStream({ threadId, initialFrame, initialStage, onCompleted }: BrowserStreamProps) {
  const [frame, setFrame] = useState<string | null>(initialFrame || null);
  const [stage, setStage] = useState<string>(initialStage || "navigating");
  const [stepMessage, setStepMessage] = useState<string>("Initializing browser agent...");
  const [otp, setOtp] = useState<string>("");
  const [isSubmittingOtp, setIsSubmittingOtp] = useState<boolean>(false);
  const [otpError, setOtpError] = useState<string | null>(null);
  const [grievanceId, setGrievanceId] = useState<string | null>(null);

  // Connect to live browser screenshot stream
  const isTerminalStage = stage === "completed" || stage === "error";
  const { isConnected } = useWebSocket({
    url: isTerminalStage ? null : getBrowserStreamUrl(threadId),
    autoReconnect: !isTerminalStage,
    onMessage: (data) => {
      if (data.type === "browser_frame") {
        if (data.frame) setFrame(data.frame);
        if (data.status) setStage(data.status);
        if (data.step) setStepMessage(data.step);
        if (data.grievance_id) {
          setGrievanceId(data.grievance_id);
          onCompleted?.(data.grievance_id);
        }
      }
    },
  });

  const handleOtpSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otp.trim()) return;

    setIsSubmittingOtp(true);
    setOtpError(null);

    try {
      await submitOtp(threadId, otp.trim());
      setStage("otp_submitted");
      setStepMessage("OTP verified. Executing final submission on CGRMS portal...");
    } catch (err: any) {
      setOtpError(err.message || "Failed to submit OTP. Please verify and try again.");
    } finally {
      setIsSubmittingOtp(false);
    }
  };

  return (
    <div className="bg-slate-950 text-white rounded-2xl overflow-hidden border border-slate-800 shadow-xl">
      {/* Top Bar */}
      <div className="bg-slate-900/90 px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="flex space-x-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
            <div className="w-3 h-3 rounded-full bg-amber-500/80"></div>
            <div className="w-3 h-3 rounded-full bg-emerald-500/80"></div>
          </div>
          <div className="h-4 w-[1px] bg-slate-700"></div>
          <div className="flex items-center space-x-2 text-xs font-mono text-slate-300">
            <Monitor className="w-3.5 h-3.5 text-blue-400" />
            <span className="truncate max-w-[200px] sm:max-w-xs">https://cgrms.pmjay.gov.in</span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Badge
            variant="outline"
            className={`text-[10px] ${
              isConnected
                ? "border-emerald-500/40 text-emerald-400 bg-emerald-950/30"
                : "border-amber-500/40 text-amber-400 bg-amber-950/30"
            }`}
          >
            <Radio className="w-2.5 h-2.5 mr-1 animate-pulse" />
            {isConnected ? "LIVE STREAM" : "CONNECTING"}
          </Badge>
          <span className="text-[11px] text-slate-400 font-mono hidden sm:inline">
            LangGraph HITL Gate
          </span>
        </div>
      </div>

      {/* Browser Viewport Frame */}
      <div className="relative aspect-[16/9] w-full bg-slate-900 flex items-center justify-center overflow-hidden">
        {frame ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={`data:image/png;base64,${frame}`}
            alt="Live CGRMS Browser Stream"
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="flex flex-col items-center justify-center text-slate-400 space-y-3 p-8 text-center">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            <p className="text-sm font-medium">Navigating to CGRMS PM-JAY Public Portal...</p>
            <p className="text-xs text-slate-500 max-w-sm">
              Playwright browser is running headfully and streaming live viewport buffers.
            </p>
          </div>
        )}

        {/* HITL OTP Intercept Modal Banner */}
        {stage === "awaiting_otp" && (
          <div className="absolute inset-0 bg-slate-950/85 backdrop-blur-md flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-amber-500/40 rounded-2xl p-6 max-w-md w-full shadow-2xl animate-in zoom-in-95 duration-200">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center">
                  <KeyRound className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white flex items-center space-x-1.5">
                    <span>Human-in-the-Loop OTP Gate</span>
                    <Badge variant="outline" className="text-[10px] border-amber-500 text-amber-400">
                      PAUSED
                    </Badge>
                  </h4>
                  <p className="text-xs text-slate-400">
                    The agent reached the statutory submission step on CGRMS.
                  </p>
                </div>
              </div>

              <p className="text-xs text-slate-300 mb-4 bg-slate-800/80 p-3 rounded-lg border border-slate-700/60 leading-relaxed">
                Enter the OTP sent to the beneficiary mobile number by the National Health Authority to authorize submission.
              </p>

              <form onSubmit={handleOtpSubmit} className="space-y-4">
                <div>
                  <label className="text-[11px] font-medium text-slate-300 block mb-1.5 uppercase tracking-wider">
                    Official Verification OTP
                  </label>
                  <Input
                    type="text"
                    maxLength={6}
                    placeholder="Enter 6-digit OTP"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
                    className="bg-slate-950 border-slate-700 text-white text-center text-lg font-mono tracking-widest h-12 focus:border-amber-500"
                    autoFocus
                  />
                  {otpError && (
                    <p className="text-xs text-red-400 mt-1.5">{otpError}</p>
                  )}
                </div>

                <div className="flex items-center space-x-3">
                  <Button
                    type="submit"
                    disabled={isSubmittingOtp || otp.length < 4}
                    className="w-full bg-amber-600 hover:bg-amber-700 text-white font-medium text-xs h-10"
                  >
                    {isSubmittingOtp ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Submitting...
                      </>
                    ) : (
                      <>
                        Authorize & Submit Grievance <ArrowRight className="w-4 h-4 ml-1.5" />
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Success Confirmation Overlay */}
        {stage === "completed" && (
          <div className="absolute top-4 right-4 bg-emerald-950/90 border border-emerald-500 text-white px-4 py-2.5 rounded-xl shadow-lg flex items-center space-x-2 text-xs">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>
              Grievance Registered: <b>{grievanceId || "CGRMS-VERIFIED"}</b>
            </span>
          </div>
        )}
      </div>

      {/* Status Bar */}
      <div className="bg-slate-900 px-4 py-2.5 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center space-x-2 truncate">
          <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
          <span className="font-mono text-slate-300 truncate">{stepMessage}</span>
        </div>
        <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">
          Stage: {stage}
        </span>
      </div>
    </div>
  );
}

