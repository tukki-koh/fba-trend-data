import { NextResponse } from "next/server";

export async function GET() {
  const key = process.env.STRIPE_SECRET_KEY ?? "";
  const priceStd = process.env.STRIPE_PRICE_STANDARD ?? "";
  return NextResponse.json({
    stripe_key_prefix: key.slice(0, 12) + "...",
    stripe_key_length: key.length,
    price_standard: priceStd.slice(0, 15) + "...",
    site_url: process.env.NEXT_PUBLIC_SITE_URL,
  });
}
