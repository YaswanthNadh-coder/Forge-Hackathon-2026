import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/header";
import { Footer } from "@/components/footer";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Ayushman-Shield — Autonomous PM-JAY Hospital Bill Auditor & CGRMS Grievance Agent",
  description:
    "Zero-dummy-data civic digital governance agent that ingests hospital bills, scrubs PII locally, cross-audits charges against NHA HBP 2022 tariff schedules, generates vernacular voice summaries via Sarvam AI, and files grievances on CGRMS with live Playwright browser automation & HITL OTP gating.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" style={{ colorScheme: "dark" }}>
      <body className={`${inter.className} min-h-screen flex flex-col bg-slate-50/50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 antialiased`}>
        <Header />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
