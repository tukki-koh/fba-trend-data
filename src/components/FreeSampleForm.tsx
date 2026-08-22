"use client";
import { useState } from "react";
import { ArrowRight, CheckCircle, Loader2, Mail, CalendarClock } from "lucide-react";

export default function FreeSampleForm() {
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
    // Duolingo流「次に何が起きるかを具体的に示す」設計を移植。
    // 送信後の「本当に届く？」という不安を、抽象的な完了表示ではなく
    // 具体的な2ステップのタイムラインで解消し、離脱・迷惑メール化を防ぐ。
    return (
      <div className="bg-green-50 border border-green-200 rounded-2xl p-8 text-center">
        <CheckCircle size={48} className="text-green-500 mx-auto mb-4" />
        <p className="text-lg font-bold text-green-800 mb-2">送信完了！</p>
        <p className="text-green-700 text-sm leading-relaxed">{message}</p>

        <div className="mt-6 max-w-xs mx-auto text-left space-y-3">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 shrink-0 w-6 h-6 rounded-full bg-green-500 text-white text-xs font-bold flex items-center justify-center">1</div>
            <div>
              <p className="text-sm font-semibold text-green-800 flex items-center gap-1.5"><Mail size={14} /> 数分以内</p>
              <p className="text-xs text-green-700">確認メールが届きます</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="mt-0.5 shrink-0 w-6 h-6 rounded-full bg-green-200 text-green-800 text-xs font-bold flex items-center justify-center">2</div>
            <div>
              <p className="text-sm font-semibold text-green-800 flex items-center gap-1.5"><CalendarClock size={14} /> 次の月曜 7:00</p>
              <p className="text-xs text-green-700">サンプルレポートが届きます</p>
            </div>
          </div>
        </div>

        <p className="text-green-600 text-xs mt-5">
          ※メールが届かない場合は迷惑メールフォルダをご確認ください
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-md mx-auto">
      <div className="flex flex-col sm:flex-row gap-3">
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="メールアドレスを入力"
          className="flex-1 px-5 py-4 rounded-full border border-stone-300 focus:border-amber-400 focus:ring-2 focus:ring-amber-100 focus:outline-none text-stone-900 text-base transition-colors"
          disabled={status === "loading"}
        />
        <button
          type="submit"
          disabled={status === "loading" || !email}
          className="inline-flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-600 disabled:bg-amber-300 text-white font-bold px-7 py-4 rounded-full transition-colors whitespace-nowrap"
        >
          {status === "loading" ? (
            <><Loader2 size={18} className="animate-spin" /> 送信中…</>
          ) : (
            <>無料で受け取る <ArrowRight size={18} /></>
          )}
        </button>
      </div>
      {status === "error" && (
        <p className="text-red-500 text-sm mt-2 text-center">{message}</p>
      )}
      <p className="text-xs text-stone-400 mt-3 text-center">
        クレジットカード不要・配信停止はいつでも可能
      </p>
    </form>
  );
}
