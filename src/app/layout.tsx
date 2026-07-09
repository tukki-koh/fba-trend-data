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
    "Amazon FBA仕入れリサーチが週1通のメールで完了。売れ筋TOP10×5カテゴリを毎週月曜7時に自動配信、価格・リンク付き。月額1,480円〜・14日返金保証。",
  keywords: [
    "Amazon FBA", "せどり", "Amazon売れ筋", "FBA仕入れ", "Amazonトレンド",
    "物販", "副業", "Amazon転売", "ベストセラー", "週次レポート",
    "商品リサーチ", "FBA出品", "Amazon物販", "仕入れデータ",
    "Amazonランキング", "FBAトレンドレーダー", "仕入れリサーチ効率化",
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
      "売れ筋TOP10×5カテゴリを毎週月曜7時に自動配信。価格・Amazonリンク付きでリサーチ時間を大幅短縮。月額1,480円〜・14日返金保証。",
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
    description: "売れ筋TOP10×5カテゴリを毎週月曜7時に自動配信。月額1,480円〜・14日返金保証、無料サンプルあり。",
    images: ["/opengraph-image"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true },
  },
  alternates: { canonical: SITE_URL },
  verification: {
    google: "yRI78JJGL2gw663JYPdPRHUFfWEef4FQLNvZOC8x18k",
  },
  other: {
    // GEO: AIクローラー向け追加メタ情報
    "speakable-selector": "h1, h2, [data-speakable]",
    "content-language": "ja",
  },
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
      <head>
        {/* GEO: AIクローラーへの追加シグナル */}
        <meta name="robots" content="max-snippet:-1, max-image-preview:large, max-video-preview:-1" />
        <link rel="me" href={SITE_URL} />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
