import { NextRequest, NextResponse } from "next/server";
import { stripe, PLANS, PlanKey } from "@/lib/stripe";

export async function POST(req: NextRequest) {
  const { plan, email } = await req.json();

  if (!plan || !(plan in PLANS)) {
    return NextResponse.json({ error: "無効なプランです" }, { status: 400 });
  }

  const selectedPlan = PLANS[plan as PlanKey];
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL;

  try {
    const session = await stripe.checkout.sessions.create({
      mode: "subscription",
      payment_method_types: ["card"],
      customer_email: email,
      line_items: [
        {
          price: selectedPlan.priceId,
          quantity: 1,
        },
      ],
      success_url: `${siteUrl}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${siteUrl}/#pricing`,
      locale: "ja",
      subscription_data: {
        metadata: { plan },
      },
      metadata: { plan },
    });

    return NextResponse.json({ url: session.url });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    console.error("[checkout error]", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
