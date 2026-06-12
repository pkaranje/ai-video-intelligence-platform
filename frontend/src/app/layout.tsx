import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI Video Intelligence",
  description: "Upload a video and get an AI-generated summary with a timestamped event timeline.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className={`${inter.className} min-h-full flex flex-col bg-zinc-50 dark:bg-zinc-950`}>
        {children}
      </body>
    </html>
  );
}
