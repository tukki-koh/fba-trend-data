"use client";
import { useState } from "react";
import { CheckCircle, ShieldCheck, Sparkles } from "lucide-react";
import Link from "next/link";

type Plan = {
  name: string;
  price: string;
  note: string;
  description: string;
  features: string[];
  cta: string;
  href: string;
  highlight: boolean;
};

// Notion の料金ページにある「用途を選ぶとおすすめプランが決まる」導線を移植。
// 会員動向という事実を伝えるのではなく、選択の負担を減らすためのUI装置なので
// 誇張表示のリスクなし。
const USE_CASES = [
  { key: "light", label: "週1回のリサーチで十分", recommend: "スタンダード" },
  { key: "heavy", label: "本格的に仕入れ判断を効率化したい", recommend: "プロ" },
] as const;

export default function PlanPicker({ plans }: { plans: Plan[] }) {
  const [picked, setPicked] = useState<(typeof USE_CASES)[number]["key"] | null>(null);
  const recommended = picked ? USE_CASES.find((u) => u.key === picked)?.recommend : null;

  return (
    <div>
      {/* ── 用途を選ぶ（Notionの「どちらが自分に合う？」導線） ── */}
      <div className="mb-8 text-center">
        <p className="text-sm font-medium text-stone-500 mb-3">まず、あなたに近いものを選んでください</p>
        <div className="flex flex-col sm:flex-row gap-2.5 justify-center max-w-xl mx-auto">
          {USE_CASES.map((u) => (
            <button
              key={u.key}
              type="button"
              onClick={() => setPicked(u.key)}
              aria-pressed={picked === u.key}
              className={`flex-1 text-sm font-semibold px-5 py-3 rounded-2xl border transition-colors ${
                picked === u.key
                  ? "bg-amber-500 border-amber-500 text-white"
                  : "bg-white border-stone-200 text-stone-700 hover:border-amber-300"
              }`}
            >
              {u.label}
            </button>
          ))}
        </div>
        {recommended && (
          <p className="mt-4 inline-flex items-center gap-1.5 text-xs font-semibold text-amber-600 bg-amber-50 border border-amber-200 px-3 py-1.5 rounded-full">
            <Sparkles size={13} /> {recommended}プランがおすすめです
          </p>
        )}
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {plans.map((plan) => {
          const isRecommended = recommended === plan.name;
          return (
            <div
              key={plan.name}
              className={`relative rounded-3xl p-8 flex flex-col transition-shadow ${
                plan.highlight
                  ? "bg-stone-900 text-white shadow-2xl shadow-stone-400/30"
                  : "bg-white border border-stone-200"
              } ${isRecommended ? "ring-2 ring-amber-400 ring-offset-2 ring-offset-[#faf9f7]" : ""}`}
            >
              {plan.highlight && (
                <div className="absolute top-6 right-6 inline-flex items-center gap-1 bg-amber-500 text-white text-[11px] font-bold px-2.5 py-1 rounded-full">
                  全20カテゴリ
                </div>
              )}
              {isRecommended && (
                <div
                  className={`absolute -top-3 left-6 inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-1 rounded-full ${
                    plan.highlight ? "bg-white text-stone-900" : "bg-stone-900 text-white"
                  }`}
                >
                  <Sparkles size={11} /> あなたにおすすめ
                </div>
              )}
              <div className={`text-sm font-semibold mb-1 ${plan.highlight ? "text-amber-400" : "text-amber-600"}`}>{plan.name}</div>
              <div className={`text-sm mb-5 ${plan.highlight ? "text-stone-400" : "text-stone-500"}`}>{plan.description}</div>
              <div className="flex items-baseline gap-2 mb-1 flex-wrap">
                <span className={`text-4xl font-bold tracking-tight ${plan.highlight ? "text-white" : "text-stone-900"}`}>¥{plan.price}</span>
                <span className={`text-sm ${plan.highlight ? "text-stone-400" : "text-stone-500"}`}>/月（税込）</span>
              </div>
              <div className={`text-xs mb-1.5 ${plan.highlight ? "text-stone-400" : "text-stone-500"}`}>{plan.note}</div>
              <div className={`text-xs mb-7 ${plan.highlight ? "text-stone-500" : "text-stone-400"}`}>月額自動更新・いつでも解約可</div>
              <ul className="space-y-3 mb-8 flex-1">
                {plan.features.map((f) => (
                  <li key={f} className={`flex items-start gap-2.5 text-sm ${plan.highlight ? "text-stone-200" : "text-stone-700"}`}>
                    <CheckCircle size={16} className={`mt-0.5 shrink-0 ${plan.highlight ? "text-amber-400" : "text-amber-500"}`} />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              <Link
                href={plan.href}
                className={`w-full text-center py-3.5 rounded-full font-semibold text-base transition-colors ${
                  plan.highlight
                    ? "bg-amber-500 hover:bg-amber-400 text-white"
                    : "bg-stone-900 hover:bg-stone-800 text-white"
                }`}
              >
                {plan.cta}
              </Link>
              <div className={`flex items-center justify-center gap-1.5 text-xs mt-3 ${plan.highlight ? "text-stone-400" : "text-stone-400"}`}>
                <ShieldCheck size={13} className={plan.highlight ? "text-emerald-400" : "text-emerald-500"} />
                14日間全額返金・いつでも解約可
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
