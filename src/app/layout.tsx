import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const SITE_URL = "https://fba-trend-data.vercel.app";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "FBAトレンドレーダー｜Amazon売れ筋トレンドを毎週自動配信",
    template: "%s｜FBAトレンドレーダー",
  },
  description:
    "Amazon FBA出品者・せどらー向けに全5カテゴリの売れ筋ランキングTOP10を毎週月曜に自動配信。仕入れ判断・商品リサーチを効率化。月額3,980円〜・14日返金保証。",
  keywords: [
    "Amazon FBA", "せどり", "Amazon売れ筋", "FBA仕入れ", "Amazonトレンド",
    "物販", "副業", "Amazon転売", "ベストセラー", "週次レポート",
    "商品リサーチ", "FBA出品", "Amazon物販", "仕入れデータ",
  ],
  authors: [{ name: "FBAトレンドレーダー" }],
  creator: "FBAトレンドレーダー",
  openGraph: {
    type: "website",
    locale: "ja_JP",
    url: SITE_URL,
    siteName: "FBAトレンドレーダー",
    title: "FBAトレンドレーダー｜Amazon売れ筋トレンドを毎週自動配信",
    description:
      "全5カテゴリの売れ筋ランキングTOP10を毎週月曜に自動配信。せどり・FBA仕入れの判断を効率化。月額3,980円〜。",
    images: [
      {
        url: "/opengraph-image",
        width: 1200,
        height: 630,
        alt: "FBAトレンドレーダー",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "FBAトレンドレーダー｜Amazon売れ筋を毎週自動配信",
    description: "全5カテゴリの売れ筋TOP10を毎週月曜に自動配信。月額3,980円〜。",
    images: ["/opengraph-image"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true },
  },
  alternates: { canonical: SITE_URL },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ja"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
