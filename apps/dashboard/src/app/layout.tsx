import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SignalFlow Monitoring Dashboard",
  description: "Real-time Stream Intelligence & Self-Healing Pipeline",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
