import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/app/providers";

export const metadata: Metadata = {
  title: "RecruitmentGen AI — Intelligent Recruitment Platform",
  description: "Multi-Agent AI-Powered Recruitment System with Resume Intelligence, JD Analysis, Candidate Matching, Ranking, Skill Evaluation, and Hiring Recommendations.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
