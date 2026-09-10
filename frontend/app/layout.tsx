import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import { Toaster } from "../components/ui/toast";

export const metadata: Metadata = {
  title: "Proximate",
  description: "AI teammate for better meetings",
  metadataBase: new URL("https://future-mode-proximate.vercel.app"),
  icons: {
    icon: "/logo.png",
    apple: "/logo.png",
  },
  openGraph: {
    title: "Proximate",
    description: "AI teammate for better meetings",
    url: "https://future-mode-proximate.vercel.app",
    siteName: "Proximate",
    type: "website",
    locale: "zh_TW",
    images: [
      {
        url: "/logo.png",
        width: 1254,
        height: 1254,
        alt: "Proximate logo",
      },
    ],
  },
  twitter: {
    card: "summary",
    title: "Proximate",
    description: "AI teammate for better meetings",
    images: ["/logo.png"],
  },
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="zh-Hant">
      <body>{children}<Toaster /></body>
    </html>
  );
}

