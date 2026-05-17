import type { Metadata } from "next";
import { IBM_Plex_Sans, Space_Grotesk } from "next/font/google";
import "./globals.css";

const display = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["500", "700"],
});

const body = IBM_Plex_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Resume Analyzer",
  description: "Frontend for Resume Analyzer",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${display.variable} ${body.variable}`}>
        <header className="topbar">
          <div className="container topbar-inner">
            <div className="brand">Resume Analyzer</div>
            <div className="muted">FastAPI + Next.js</div>
          </div>
        </header>
        <main className="layout container">{children}</main>
      </body>
    </html>
  );
}
