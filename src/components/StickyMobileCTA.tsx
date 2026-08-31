"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Gift, ArrowRight } from "lucide-react";

/**
 * モバイル専用の追従CTAバー。
 * Amazonのスマホ商品ページが「カートに入れる」を画面下部に固定し、
 * スクロール位置に関わらず購入導線を常に1タップ以内に置いているのを手本にした。
 * ヒーローを通り過ぎてから表示し、ファーストビューの邪魔をしない。
 */
export default function StickyMobileCTA() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > 640);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div
      className={`sm:hidden fixed inset-x-0 bottom-0 z-50 transition-transform duration-300 ${
        visible ? "translate-y-0" : "translate-y-full"
      }`}
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      <div className="mx-3 mb-3 flex items-center gap-2 rounded-2xl border border-stone-200 bg-white/95 p-2 shadow-lg shadow-stone-400/30 backdrop-blur">
        <a
          href="#free-sample"
          className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-xl border border-stone-200 px-3 py-3 text-sm font-semibold text-stone-800"
        >
          <Gift size={15} className="text-amber-500" /> 無料サンプル
        </a>
        <Link
          href="/checkout?plan=standard"
          className="flex-1 inline-flex items-center justify-center gap-1 rounded-xl bg-amber-500 px-3 py-3 text-sm font-bold text-white"
        >
          月1,480円で始める <ArrowRight size={15} />
        </Link>
      </div>
    </div>
  );
}
