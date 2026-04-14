import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: {
    default: "ApplyMap - Source-Backed Common App Optimization",
    template: "%s | ApplyMap",
  },
  description:
    "Choose, rank, and rewrite your strongest honors and activities for a specific university — with source-backed guidance, not fake admission predictions.",
  keywords: ["Common App", "college application", "activities", "honors", "international students"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
