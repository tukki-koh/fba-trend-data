import { NextRequest, NextResponse } from "next/server";
import { stripe } from "@/lib/stripe";
import { supabaseAdmin } from "@/lib/supabase";

export async function GET(req: NextRequest) {
  const email = req.headers.get("x-user-email");
  if (!email) return NextResponse.redirect(new URL("/", req.url));

  const { data: member } = await supabaseAdmin
    .from("members")
    .select("stripe_customer_id")
    .eq("email", email)
    .single();

  if (!member?.stripe_customer_id) {
    return NextResponse.redirect(new URL("/", req.url));
  }

  const session = await stripe.billingPortal.sessions.create({
    customer: member.stripe_customer_id,
    return_url: `${process.env.NEXT_PUBLIC_SITE_URL}/dashboard`,
  });

  return NextResponse.redirect(session.url);
}
