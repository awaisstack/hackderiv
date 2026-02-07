import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Deriv P2P Sentinel | AI Fraud Detection",
  description: "AI-Powered Receipt Fraud Detection for P2P Trading",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
