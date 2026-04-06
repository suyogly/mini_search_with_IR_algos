import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Mini Search",
  description: "Keyword, TF-IDF, and BM25 search over your snippets",
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
