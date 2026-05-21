import Stripe from "stripe";

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: "2026-04-22.dahlia",
});

export const PLANS = {
  standard: {
    priceId: process.env.STRIPE_PRICE_STANDARD!,
    name: "スタンダード",
    amount: 3980,
  },
  pro: {
    priceId: process.env.STRIPE_PRICE_PRO!,
    name: "プロ",
    amount: 9800,
  },
} as const;

export type PlanKey = keyof typeof PLANS;
