"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Upload, FileText, Image as ImageIcon, ShieldCheck, CheckCircle2, AlertCircle, Loader2, Hospital, MapPin, CreditCard } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { INDIAN_STATES } from "@/types";
import { uploadBill } from "@/lib/api";

export function BillUpload() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [file, setFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Form Fields
  const [stateName, setStateName] = useState("Delhi");
  const [city, setCity] = useState("");
  const [district, setDistrict] = useState("");
  const [hospitalName, setHospitalName] = useState("");
  const [cardStatus, setCardStatus] = useState<"active" | "inactive" | "pending">("active");
  const [pmjayId, setPmjayId] = useState("");
  const [admissionDate, setAdmissionDate] = useState("");
  const [dischargeDate, setDischargeDate] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleFileChange = (selectedFile: File) => {
    setFile(selectedFile);
    setErrorMessage(null);

    if (selectedFile.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = (e) => setFilePreview(e.target?.result as string);
      reader.readAsDataURL(selectedFile);
    } else {
      setFilePreview(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setErrorMessage("Please select or drop a hospital bill photo or PDF.");
      return;
    }
    if (!hospitalName.trim()) {
      setErrorMessage("Please enter the hospital name.");
      return;
    }
    if (!city.trim()) {
      setErrorMessage("Please enter the patient city.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("state", stateName);
      formData.append("city", city.trim());
      formData.append("district", district.trim() || city.trim());
      formData.append("hospital_name", hospitalName.trim());
      formData.append("pmjay_card_status", cardStatus);
      if (pmjayId) formData.append("pmjay_id", pmjayId.trim());
      if (admissionDate) formData.append("admission_date", admissionDate);
      if (dischargeDate) formData.append("discharge_date", dischargeDate);

      const res = await uploadBill(formData);
      router.push(`/audit/${res.audit_id}`);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to upload and initiate audit.");
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Upload Zone Card */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-6 border-b border-slate-100 dark:border-slate-800">
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                  Step 1: Upload Hospital Bill
                </h3>
                <Badge variant="outline" className="text-blue-600 dark:text-blue-400 border-blue-200 text-xs">
                  Photo / PDF
                </Badge>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Upload clear camera photos, scanned copies, or discharge summary bills (up to 20MB)
              </p>
            </div>

            {/* PII Privacy Shield Callout */}
            <div className="flex items-center space-x-2 bg-emerald-50 dark:bg-emerald-950/30 text-emerald-800 dark:text-emerald-300 px-3.5 py-2 rounded-xl border border-emerald-200 dark:border-emerald-800/60 text-xs shrink-0">
              <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
              <div>
                <p className="font-semibold text-[11px] leading-tight">Local PII Privacy Shield Active</p>
                <p className="text-[10px] text-emerald-700/80 dark:text-emerald-400">
                  Aadhaar, ABHA & Phone masked locally via Presidio
                </p>
              </div>
            </div>
          </div>

          {/* Drag & Drop Area */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-200 flex flex-col items-center justify-center min-h-[220px] ${
              isDragging
                ? "border-blue-500 bg-blue-50/50 dark:bg-blue-950/20 scale-[0.99]"
                : file
                ? "border-emerald-400 bg-emerald-50/20 dark:bg-emerald-950/10"
                : "border-slate-300 dark:border-slate-700 hover:border-blue-400 hover:bg-slate-50/50 dark:hover:bg-slate-800/50"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,application/pdf"
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileChange(e.target.files[0]);
                }
              }}
            />

            {file ? (
              <div className="flex flex-col items-center space-y-3">
                {filePreview ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={filePreview}
                    alt="Bill Preview"
                    className="w-32 h-32 object-cover rounded-xl shadow-md border border-slate-200 dark:border-slate-700"
                  />
                ) : (
                  <div className="w-16 h-16 rounded-2xl bg-emerald-100 dark:bg-emerald-950/40 text-emerald-600 flex items-center justify-center">
                    <FileText className="w-8 h-8" />
                  </div>
                )}
                <div>
                  <p className="font-semibold text-sm text-slate-800 dark:text-slate-200">{file.name}</p>
                  <p className="text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB • Ready for audit</p>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    fileInputRef.current?.click();
                  }}
                  className="text-xs h-8"
                >
                  Change File
                </Button>
              </div>
            ) : (
              <div className="flex flex-col items-center space-y-3">
                <div className="w-14 h-14 rounded-2xl bg-blue-50 dark:bg-blue-950/40 text-blue-600 flex items-center justify-center">
                  <Upload className="w-7 h-7" />
                </div>
                <div>
                  <p className="font-semibold text-sm text-slate-800 dark:text-slate-200">
                    Click to browse or drag & drop hospital bill
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    Accepts JPEG, PNG, WebP photos or itemized PDF invoices
                  </p>
                </div>
                <span className="text-[11px] font-medium text-blue-600 bg-blue-50 dark:bg-blue-950/60 px-3 py-1 rounded-full">
                  Supports Multi-page & Smartphone Photos
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Patient Admission Details */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-sm">
          <div className="mb-6 pb-4 border-b border-slate-100 dark:border-slate-800">
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              Step 2: Admission & PM-JAY Details
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Used to query NHA empanelment directories, verify hospital tier, and cross-reference state package rates.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <Label className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Hospital Name *
              </Label>
              <div className="relative mt-1.5">
                <Hospital className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
                <Input
                  required
                  placeholder="e.g. Max Super Speciality Hospital, Saket"
                  value={hospitalName}
                  onChange={(e) => setHospitalName(e.target.value)}
                  className="pl-9 text-xs sm:text-sm"
                />
              </div>
              <p className="text-[11px] text-slate-500 mt-1">Cross-checked against official PM-JAY Empanelment registry</p>
            </div>

            <div>
              <Label className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                State / UT *
              </Label>
              <select
                value={stateName}
                onChange={(e) => setStateName(e.target.value)}
                className="w-full mt-1.5 h-10 px-3 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs sm:text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {INDIAN_STATES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
              <p className="text-[11px] text-slate-500 mt-1">Determines state-specific HBP 2022 tier multipliers</p>
            </div>

            <div>
              <Label className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                City / District *
              </Label>
              <div className="relative mt-1.5">
                <MapPin className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
                <Input
                  required
                  placeholder="e.g. New Delhi"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  className="pl-9 text-xs sm:text-sm"
                />
              </div>
            </div>

            <div>
              <Label className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                PM-JAY Card Status *
              </Label>
              <div className="relative mt-1.5">
                <CreditCard className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
                <select
                  value={cardStatus}
                  onChange={(e) => setCardStatus(e.target.value as any)}
                  className="w-full h-10 pl-9 pr-3 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs sm:text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="active">Active PM-JAY Cardholder (₹5 Lakh Entitlement)</option>
                  <option value="pending">Golden Card Approved / Pending Generation</option>
                  <option value="inactive">ABHA Registered / Scheme Eligible</option>
                </select>
              </div>
            </div>

            <div>
              <Label className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                PM-JAY ID or ABHA Number (Optional)
              </Label>
              <Input
                placeholder="e.g. PMJAY-1234-5678 or 14-digit ABHA"
                value={pmjayId}
                onChange={(e) => setPmjayId(e.target.value)}
                className="mt-1.5 text-xs sm:text-sm"
              />
              <p className="text-[11px] text-slate-500 mt-1">Masked locally before cloud transmission</p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Admission Date
                </Label>
                <Input
                  type="date"
                  value={admissionDate}
                  onChange={(e) => setAdmissionDate(e.target.value)}
                  className="mt-1.5 text-xs sm:text-sm"
                />
              </div>
              <div>
                <Label className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Discharge Date
                </Label>
                <Input
                  type="date"
                  value={dischargeDate}
                  onChange={(e) => setDischargeDate(e.target.value)}
                  className="mt-1.5 text-xs sm:text-sm"
                />
              </div>
            </div>
          </div>

          {errorMessage && (
            <Alert variant="destructive" className="mt-6">
              <AlertCircle className="w-4 h-4" />
              <AlertDescription className="text-xs">{errorMessage}</AlertDescription>
            </Alert>
          )}

          <div className="mt-8 pt-6 border-t border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-xs text-slate-500 flex items-center">
              <CheckCircle2 className="w-4 h-4 mr-1.5 text-emerald-500 shrink-0" />
              Zero dummy data: RAG cross-audited against authentic NHA HBP 2022 tariff schedules
            </p>

            <Button
              type="submit"
              size="lg"
              disabled={isSubmitting}
              className="w-full sm:w-auto px-8 bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm shadow-md shadow-blue-500/20 cursor-pointer"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Sanitizing PII & Launching Agent...
                </>
              ) : (
                "Launch Autonomous Audit Pipeline"
              )}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}

