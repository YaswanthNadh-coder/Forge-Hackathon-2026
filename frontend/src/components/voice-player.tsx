"use client";

import { useState, useRef, useEffect } from "react";
import { Volume2, Play, Pause, Download, Globe2, Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Language, LANGUAGE_LABELS } from "@/types";
import { getVoiceUrl } from "@/lib/api";

interface VoicePlayerProps {
  auditId: string;
  defaultLanguage?: Language;
}

export function VoicePlayer({ auditId, defaultLanguage = "hi" }: VoicePlayerProps) {
  const [selectedLang, setSelectedLang] = useState<Language>(defaultLanguage);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handleFetchAudio = async (lang: Language) => {
    setIsLoading(true);
    setIsPlaying(false);
    try {
      const url = getVoiceUrl(auditId, lang);
      setAudioUrl(url);
    } catch (err) {
      console.error("Audio retrieval error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    handleFetchAudio(selectedLang);
  }, [selectedLang, auditId]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play().then(() => setIsPlaying(true)).catch((e) => {
        console.warn("Playback error:", e);
        setIsPlaying(false);
      });
    }
  };

  return (
    <div className="bg-gradient-to-r from-blue-900/10 via-indigo-900/10 to-purple-900/10 border border-blue-200 dark:border-blue-900/50 rounded-2xl p-5 shadow-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-md shadow-blue-500/20">
            <Volume2 className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h4 className="font-semibold text-sm text-slate-900 dark:text-slate-100">
                Vernacular Voice Explanation
              </h4>
              <Badge variant="outline" className="text-[10px] bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 border-indigo-200 dark:border-indigo-800">
                <Sparkles className="w-3 h-3 mr-1 text-indigo-500" /> Sarvam AI
              </Badge>
            </div>
            <p className="text-xs text-slate-500">
              Listen to the audit breakdown in your preferred regional language
            </p>
          </div>
        </div>

        {/* Language Selector */}
        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <Globe2 className="w-4 h-4 text-slate-400 shrink-0" />
          <select
            value={selectedLang}
            onChange={(e) => setSelectedLang(e.target.value as Language)}
            className="text-xs font-medium bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 w-full sm:w-44 cursor-pointer"
          >
            {Object.entries(LANGUAGE_LABELS).map(([code, name]) => (
              <option key={code} value={code} className="bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100">
                {name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Audio Controls */}
      <div className="bg-white/90 dark:bg-slate-900/90 rounded-xl p-3 border border-slate-200/60 dark:border-slate-800 flex items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <Button
            size="sm"
            variant="default"
            onClick={togglePlay}
            disabled={isLoading || !audioUrl}
            className="h-9 px-4 rounded-lg bg-blue-600 hover:bg-blue-700 text-xs font-medium"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
            ) : isPlaying ? (
              <Pause className="w-4 h-4 mr-1.5" />
            ) : (
              <Play className="w-4 h-4 mr-1.5 fill-white" />
            )}
            {isPlaying ? "Pause" : "Listen Explanation"}
          </Button>

          {/* Audio Waveform visualization */}
          <div className="hidden sm:flex items-center space-x-1 h-6 px-2">
            {[40, 70, 30, 90, 60, 45, 80, 50, 75, 35, 65, 85].map((h, i) => (
              <div
                key={i}
                className={`w-1 rounded-full bg-blue-500 transition-all duration-300 ${
                  isPlaying ? "animate-pulse" : "opacity-40"
                }`}
                style={{
                  height: isPlaying ? `${Math.max(20, (h * (i % 2 === 0 ? 1 : 0.7)))}%` : "30%",
                  animationDelay: `${i * 0.1}s`,
                }}
              />
            ))}
          </div>
        </div>

        {audioUrl && (
          <div className="flex items-center space-x-2">
            <audio
              ref={audioRef}
              src={audioUrl}
              onEnded={() => setIsPlaying(false)}
              onError={() => setIsPlaying(false)}
              className="hidden"
            />
            <a
              href={audioUrl}
              download={`ayushman_audit_${selectedLang}.wav`}
              className="inline-flex items-center space-x-1 text-xs text-slate-500 hover:text-blue-600 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Download Audio</span>
            </a>
          </div>
        )}
      </div>
    </div>
  );
}

