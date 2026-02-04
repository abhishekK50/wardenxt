import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ErrorBoundary } from "./components/ErrorBoundary";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: {
    default: "WardenXT - AI-Powered Incident Commander",
    template: "%s | WardenXT"
  },
  description: "From reactive firefighting to proactive prevention. WardenXT uses Google Gemini 3 to analyze incidents, predict failures, and generate executable remediation plans.",
  keywords: ["incident management", "AI", "Gemini 3", "DevOps", "SRE", "predictive analytics", "runbook automation"],
  authors: [{ name: "WardenXT Team" }],
  creator: "WardenXT",
  publisher: "WardenXT",
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://wardenxt.vercel.app",
    siteName: "WardenXT",
    title: "WardenXT - AI-Powered Incident Commander",
    description: "From reactive firefighting to proactive prevention. AI-powered incident management with Google Gemini 3.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "WardenXT - AI-Powered Incident Commander",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "WardenXT - AI-Powered Incident Commander",
    description: "From reactive firefighting to proactive prevention. AI-powered incident management with Google Gemini 3.",
    images: ["/og-image.png"],
  },
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon-16x16.png",
    apple: "/apple-touch-icon.png",
  },
  manifest: "/site.webmanifest",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#0f172a" },
    { media: "(prefers-color-scheme: dark)", color: "#0f172a" },
  ],
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className={`${inter.className} bg-slate-950 text-white antialiased`}>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </body>
    </html>
  );
}
