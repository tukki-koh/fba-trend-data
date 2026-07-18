"use client";
import { useState } from "react";
import { ArrowRight, Gift, CheckCircle, Loader2 } from "lucide-react";

export default function HeroEmailCapture() {
  const [email, setEmail]     = useState("");
  const [status, setStatus]   = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email) return;
    setStatus("loading");
    try {
      const res = await fetch("/api/free-sample", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (res.ok) {
        setStatus("success");
        setMessage(data.message ?? "送信しました！");
      } else {
        setStatus("error");
        setMessage(data.error ?? "エラーが発生しました");
      }
    } catch {
      setStatus("error");
      setMessage("通信エラーが発生しました。再度お試しください。");
    }
  }

  if (status === "success") {
    return (
      <div className="inline-flex items-center justify-center gap-2 bg-emerald-50 border border-emerald-200 text-emerald-700 text-base font-semibold px-7 py-4 rounded-full">
        <CheckCircle size={18} /> 届きます！受信箱をご確認ください
      </div>
    );
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row shrink-0 gap-3 w-full sm:w-auto">
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="メールアドレスを入力"
          disabled={status === "loading"}
          className="px-5 py-4 rounded-full border border-stone-200 bg-white focus:border-amber-400 focus:ring-2 focus:ring-amber-100 focus:outline-none text-stone-900 text-base transition-colors w-full sm:w-64"
        />
        <button
          type="submit"
          disabled={status === "loading" || !email}
          className="inline-flex items-center justify-center gap-2 bg-white border border-stone-200 text-stone-800 hover:border-stone-300 disabled:opacity-60 text-base font-semibold px-7 py-4 rounded-full transition-colors whitespace-nowrap"
        >
          {status === "loading" ? (
            <><Loader2 size={18} className="animate-spin" /> 送信中</>
          ) : (
            <><Gift size={18} className="text-amber-500" /> 無料で中身を見る <ArrowRight size={14} className="opacity-50" /></>
          )}
        </button>
      </form>
      {status === "error" && <p className="text-red-500 text-xs mt-2">{message}</p>}
    </div>
  );
}
