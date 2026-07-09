import Stripe from "stripe";

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: "2026-04-22.dahlia",
});

// Stripe Price ID（2026-07改定: スタンダード¥1,480 / プロ¥2,480）
// Price ID は機密情報ではないためコードに直接指定する。
// これにより本番のenv変数（旧Price IDのまま）に依存せず、常に正しい価格で課金される。
export const PLANS = {
  standard: {
    priceId: "price_1TrA9F06XUMBHX2UInjsS3Ap",
    name: "スタンダード",
    amount: 1480,
  },
  pro: {
    priceId: "price_1TrA9K06XUMBHX2UDCeE3rJ3",
    name: "プロ",
    amount: 2480,
  },
} as const;

export type PlanKey = keyof typeof PLANS;
