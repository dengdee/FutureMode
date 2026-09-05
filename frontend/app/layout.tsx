import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import { Toaster } from "../components/ui/toast";

export const metadata: Metadata = {
  title: "Proximate",
  description: "AI teammate for better meetings",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="zh-Hant">
      <body>{children}<Toaster /></body>
    </html>
  );
}

