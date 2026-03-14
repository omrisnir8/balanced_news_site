import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Balanced News Aggregator",
  description: "Multi-perspective unified news feed",
  manifest: "/manifest.json",
  themeColor: "#0d1117",
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'Balanced News'
  }
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {children}
      </body>
    </html>
  );
}
