import type { Metadata, Viewport } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";

const jakarta = Plus_Jakarta_Sans({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "Rate Tracker",
  description: "Sri Lankan fixed deposit rates from banks and finance companies, ranked by AER.",
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  themeColor: "#0E0E10",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={jakarta.variable}>
      <body>{children}</body>
    </html>
  );
}
