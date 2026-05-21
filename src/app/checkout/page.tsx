"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { ArrowRight, Lock, CheckCircle } from "lucide-react";
import { Suspense } from "react";

const PLAN_INFO = {
  standard: { name: "スタンダード", price: "3,980", features: ["週次トレンドPDF", "急上昇TOP10", "注目キーワード20件"] },
  pro: { name: "プロ", price: "9,800", features: ["全カテゴリ詳細データ", "競合価格アラート", "Excelデータ"] },
};

function CheckoutForm() {
  const params = useSearchParams();
  const plan = (params.get("plan") ?? "standard") as "standard" | "pro";
  const info = PLAN_INFO[plan] ?? PLAN_INFO.standard;

  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleCheckout() {
    if (!email || !email.includes("@")) {
      setError("正しいメールアドレスを入力してください");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan, email }),
      });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        setError("エラーが発生しました。もう一度お試しください。");
      }
    } catch {
      setError("通信エラーが発生しました。");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8">
        <h1 className="text-2xl font-extrabold mb-1">お申し込み</h1>
        <p className="text-gray-500 text-sm mb-6">
          {info.name}プラン ／ 月額¥{info.price}（税込）
        </p>

        <div className="bg-orange-50 rounded-xl p-4 mb-6">
          {info.features.map((f) => (
            <div key={f} className="flex items-center gap-2 text-sm py-1">
              <CheckCircle size={14} className="text-orange-500" />
              <span>{f}</span>
            </div>
          ))}
        </div>

        <label className="block text-sm font-semibold mb-2">メールアドレス</label>
        <input
          type="email"
          placeholder="your@email.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full border border-gray-300 rounded-xl px-4 py-3 text-base mb-4 focus:outline-none focus:ring-2 focus:ring-orange-400"
        />

        {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

        <button
          onClick={handleCheckout}
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 bg-orange-500 hover:bg-orange-600 disabled:opacity-60 text-white font-bold text-lg py-4 rounded-full transition-colors"
        >
          {loading ? "処理中..." : <>カード情報入力へ進む <ArrowRight size={18} /></>}
        </button>

        <div className="flex items-center justify-center gap-2 mt-4 text-gray-400 text-xs">
          <Lock size={12} /> SSL暗号化 ／ Stripeによる安全な決済
        </div>
        <p className="text-center text-xs text-gray-400 mt-2">14日間全額返金保証</p>
      </div>
    </div>
  );
}

export default function CheckoutPage() {
  return (
    <Suspense>
      <CheckoutForm />
    </Suspense>
  );
}
