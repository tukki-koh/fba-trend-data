import { CheckCircle, TrendingUp, BarChart2, Zap, ArrowRight, Star, Gift } from "lucide-react";
import Link from "next/link";
import type { Metadata } from "next";
import Script from "next/script";
import FreeSampleForm from "@/components/FreeSampleForm";

export const metadata: Metadata = {
  title: "FBAトレンドレーダー｜Amazon売れ筋トレンドを毎週自動配信",
  description:
    "Amazon FBA出品者・せどらー向けに全5カテゴリの売れ筋ランキングTOP10を毎週月曜に自動配信。仕入れ判断・商品リサーチを効率化。月額3,980円〜・14日返金保証。まず無料サンプルを受け取れます。",
};

const PLANS = [
  {
    name: "スタンダード",
    price: "3,980",
    description: "副業FBA出品者向け",
    features: [
      "週次トレンドレポート（PDF）",
      "全5カテゴリ TOP10ランキング",
      "急上昇商品・注目キーワード",
      "毎週月曜 AM7:00 自動配信",
      "過去4週分のアーカイブ閲覧",
      "14日間返金保証",
    ],
    cta: "スタンダードで始める",
    href: "/checkout?plan=standard",
    highlight: false,
  },
  {
    name: "プロ",
    price: "9,800",
    description: "本業・法人FBA出品者向け",
    features: [
      "スタンダードの全機能",
      "全20カテゴリ詳細データ",
      "競合出品者の価格変動アラート",
      "新規参入商品の急騰データ",
      "Excelデータ(.xlsx)ダウンロード",
      "過去3ヶ月アーカイブ閲覧",
      "14日間返金保証",
    ],
    cta: "プロで始める",
    href: "/checkout?plan=pro",
    highlight: true,
  },
];

const FAQS = [
  {
    q: "どんなデータが届きますか？",
    a: "Amazon Japanの各カテゴリで急上昇している商品の売れ筋ランキング・価格データ・注目商品をまとめたPDFレポートが毎週届きます。",
  },
  {
    q: "いつレポートが届きますか？",
    a: "毎週月曜日の朝7時に、登録メールアドレスへ自動送信されます。",
  },
  {
    q: "無料サンプルとは何ですか？",
    a: "メールアドレスを入力するだけで最新レポートを1回無料でお届けします。クレジットカード不要で、品質を確認してからご契約いただけます。",
  },
  {
    q: "解約はいつでもできますか？",
    a: "はい。マイページから1クリックでいつでも解約できます。違約金・解約手数料は一切ありません。",
  },
  {
    q: "14日返金保証とは？",
    a: "ご契約から14日以内であれば、理由を問わず全額返金します。まずお試しください。",
  },
  {
    q: "データの精度はどのくらいですか？",
    a: "Amazon Japan公式の公開ベストセラーページから毎週収集した最新データを使用しています。毎週月曜の朝に自動更新されます。",
  },
  {
    q: "スマホでも見られますか？",
    a: "はい。PDFレポートはスマートフォン・タブレット・PCすべてで閲覧できます。マイページもスマホ対応しています。",
  },
  {
    q: "どのカテゴリのデータが届きますか？",
    a: "ペット用品・アウトドア・キッチン・ビューティー・ベビーの5カテゴリのTOP10ランキングが届きます。プロプランでは20カテゴリに拡大されます。",
  },
];

const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebSite",
      "@id": "https://fba-trend-data.vercel.app/#website",
      url: "https://fba-trend-data.vercel.app",
      name: "FBAトレンドレーダー",
      description: "Amazon FBA出品者向け週次トレンドデータ配信サービス",
      inLanguage: "ja",
    },
    {
      "@type": "SoftwareApplication",
      name: "FBAトレンドレーダー",
      applicationCategory: "BusinessApplication",
      offers: [
        { "@type": "Offer", name: "スタンダードプラン", price: "3980", priceCurrency: "JPY" },
        { "@type": "Offer", name: "プロプラン", price: "9800", priceCurrency: "JPY" },
      ],
    },
    {
      "@type": "FAQPage",
      mainEntity: FAQS.map((faq) => ({
        "@type": "Question",
        name: faq.q,
        acceptedAnswer: { "@type": "Answer", text: faq.a },
      })),
    },
  ],
};

export default function HomePage() {
  return (
    <div className="min-h-screen bg-white text-gray-900">
      <Script id="json-ld" type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />

      {/* ── ナビ ── */}
      <nav className="fixed top-0 w-full bg-white/90 backdrop-blur-sm border-b border-gray-100 z-50">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <span className="font-bold text-lg text-orange-500">📦 FBAトレンドレーダー</span>
          <div className="flex items-center gap-3">
            <a href="#free-sample"
              className="hidden sm:inline-flex items-center gap-1 text-orange-600 font-semibold text-sm hover:underline">
              <Gift size={14} /> 無料で試す
            </a>
            <Link href="/checkout?plan=standard"
              className="bg-orange-500 hover:bg-orange-600 text-white text-sm font-semibold px-4 py-2 rounded-full transition-colors">
              今すぐ始める
            </Link>
          </div>
        </div>
      </nav>

      {/* ── 緊急性バナー ── */}
      <div className="bg-orange-500 text-white text-sm font-semibold text-center py-2.5 pt-16">
        🔥 毎週月曜 AM7:00 に最新レポートを自動配信中 ―
        <a href="#free-sample" className="underline ml-1">まず無料で受け取る →</a>
      </div>

      {/* ── ヒーロー ── */}
      <section className="pt-12 pb-20 px-4 bg-gradient-to-b from-orange-50 to-white">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-orange-100 text-orange-700 text-sm font-semibold px-4 py-1.5 rounded-full mb-6">
            <Zap size={14} /> Amazon FBA出品者・せどらー向け
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold leading-tight tracking-tight mb-6">
            今週<span className="text-orange-500">Amazon で売れる商品</span>を<br />
            データで先回りする
          </h1>
          <p className="text-lg text-gray-600 mb-8 leading-relaxed">
            全5カテゴリのベストセラーランキングTOP10を毎週自動収集。<br className="hidden md:block" />
            仕入れリサーチの時間をゼロにして、利益を最大化。
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-4">
            <Link href="/checkout?plan=standard"
              className="inline-flex items-center justify-center gap-2 bg-orange-500 hover:bg-orange-600 text-white text-lg font-bold px-8 py-4 rounded-full transition-colors shadow-lg shadow-orange-200">
              月額3,980円で始める <ArrowRight size={20} />
            </Link>
            <a href="#free-sample"
              className="inline-flex items-center justify-center gap-2 border-2 border-orange-400 text-orange-600 hover:bg-orange-50 text-base font-bold px-8 py-4 rounded-full transition-colors">
              <Gift size={18} /> まず無料で試す
            </a>
          </div>
          <p className="text-sm text-gray-400">14日間返金保証 ／ クレジットカード不要でキャンセル可</p>
        </div>
      </section>

      {/* ── 実績数字 ── */}
      <section className="py-14 bg-gray-900 text-white">
        <div className="max-w-5xl mx-auto px-4 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          {[
            { num: "5",    label: "分析カテゴリ" },
            { num: "TOP10", label: "ランキング公開" },
            { num: "毎週月曜", label: "自動配信" },
            { num: "14日", label: "全額返金保証" },
          ].map((item) => (
            <div key={item.label}>
              <div className="text-3xl md:text-4xl font-extrabold text-orange-400">{item.num}</div>
              <div className="text-sm text-gray-400 mt-1">{item.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── 無料サンプルセクション ── */}
      <section id="free-sample" className="py-20 px-4 bg-gradient-to-b from-orange-50 to-white">
        <div className="max-w-2xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-orange-100 text-orange-700 text-sm font-bold px-4 py-1.5 rounded-full mb-6">
            <Gift size={14} /> 完全無料・クレジットカード不要
          </div>
          <h2 className="text-3xl font-extrabold mb-4">
            まず<span className="text-orange-500">無料</span>でレポートを受け取る
          </h2>
          <p className="text-gray-600 mb-8 leading-relaxed">
            メールアドレスを入力するだけで、最新の週次レポートを<strong>1回無料</strong>でお届けします。<br />
            品質を確認してから有料プランをご検討いただけます。
          </p>
          <FreeSampleForm />
          <div className="mt-8 flex flex-wrap justify-center gap-4 text-sm text-gray-500">
            {["✅ 登録30秒", "✅ カード不要", "✅ いつでも配信停止可", "✅ 迷惑メールなし"].map((t) => (
              <span key={t}>{t}</span>
            ))}
          </div>
        </div>
      </section>

      {/* ── 課題 → 解決 ── */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-extrabold text-center mb-14">こんな悩みを抱えていませんか？</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {[
              "何を仕入れればいいかわからない",
              "リサーチに毎週10時間以上かかっている",
              "売れると思った商品がすぐレッドオーシャンになる",
              "競合が何を仕入れているか全くわからない",
            ].map((pain) => (
              <div key={pain} className="flex items-start gap-3 bg-red-50 border border-red-100 rounded-xl p-5">
                <span className="text-red-400 mt-0.5 text-xl">✕</span>
                <span className="text-gray-800 font-medium">{pain}</span>
              </div>
            ))}
          </div>
          <div className="mt-10 text-center text-2xl font-bold text-gray-400">↓ FBAトレンドレーダーで解決</div>
          <div className="grid md:grid-cols-2 gap-6 mt-10">
            {[
              "今週急上昇中のカテゴリ・商品がひと目でわかる",
              "リサーチ時間をほぼゼロに削減できる",
              "トレンドを1〜2週早く掴んでブルーオーシャンで勝負",
              "データに基づいた仕入れ判断ができる",
            ].map((sol) => (
              <div key={sol} className="flex items-start gap-3 bg-green-50 border border-green-100 rounded-xl p-5">
                <CheckCircle className="text-green-500 mt-0.5 shrink-0" size={20} />
                <span className="text-gray-800 font-medium">{sol}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── レポート内容 ── */}
      <section className="py-20 px-4 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-extrabold text-center mb-4">レポートに含まれるデータ</h2>
          <p className="text-center text-gray-500 mb-12">毎週月曜日、PDFで自動配信</p>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: <TrendingUp size={28} className="text-orange-500" />,
                title: "カテゴリ別TOP10",
                desc: "ペット・アウトドア・キッチン・ビューティー・ベビーの5カテゴリ、各TOP10の商品データ",
              },
              {
                icon: <BarChart2 size={28} className="text-orange-500" />,
                title: "価格データつき",
                desc: "各商品の現在価格を一覧で確認。仕入れ判断・利益計算がすぐできる",
              },
              {
                icon: <Star size={28} className="text-orange-500" />,
                title: "Amazon直リンク",
                desc: "各商品のAmazonページに直接アクセス。リサーチ時間を大幅に短縮",
              },
            ].map((feat) => (
              <div key={feat.title} className="bg-white rounded-2xl p-7 shadow-sm border border-gray-100">
                <div className="mb-4">{feat.icon}</div>
                <h3 className="font-bold text-lg mb-2">{feat.title}</h3>
                <p className="text-gray-600 text-sm leading-relaxed">{feat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 料金 ── */}
      <section id="pricing" className="py-20 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-extrabold text-center mb-4">料金プラン</h2>
          <p className="text-center text-gray-500 mb-12">全プラン14日間返金保証 ／ いつでも解約可能</p>
          <div className="grid md:grid-cols-2 gap-8">
            {PLANS.map((plan) => (
              <div key={plan.name}
                className={`rounded-2xl p-8 border-2 flex flex-col ${
                  plan.highlight
                    ? "border-orange-500 bg-orange-50 shadow-xl shadow-orange-100"
                    : "border-gray-200 bg-white"
                }`}>
                {plan.highlight && (
                  <div className="inline-block bg-orange-500 text-white text-xs font-bold px-3 py-1 rounded-full mb-4 self-start">
                    🔥 人気 No.1
                  </div>
                )}
                <div className="text-sm font-semibold text-gray-500 mb-1">{plan.description}</div>
                <div className="text-4xl font-extrabold mb-1">
                  ¥{plan.price}<span className="text-base font-normal text-gray-500">/月</span>
                </div>
                <div className="text-xs text-gray-400 mb-6">税込・月額自動更新</div>
                <ul className="space-y-3 mb-8 flex-1">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2.5 text-sm">
                      <CheckCircle size={16} className="text-orange-500 mt-0.5 shrink-0" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
                <Link href={plan.href}
                  className={`w-full text-center py-3.5 rounded-full font-bold text-base transition-colors ${
                    plan.highlight
                      ? "bg-orange-500 hover:bg-orange-600 text-white"
                      : "bg-gray-900 hover:bg-gray-700 text-white"
                  }`}>
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
          <p className="text-center text-gray-400 text-sm mt-8">
            まだ迷っていますか？ →{" "}
            <a href="#free-sample" className="text-orange-500 font-semibold hover:underline">
              無料でサンプルレポートを受け取る
            </a>
          </p>
        </div>
      </section>

      {/* ── FAQ ── */}
      <section className="py-20 px-4 bg-gray-50">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-3xl font-extrabold text-center mb-12">よくある質問</h2>
          <div className="space-y-4">
            {FAQS.map((faq) => (
              <div key={faq.q} className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="font-bold text-gray-900 mb-2">Q. {faq.q}</div>
                <div className="text-gray-600 text-sm leading-relaxed">A. {faq.a}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 最終CTA ── */}
      <section className="py-20 px-4 bg-orange-500 text-white text-center">
        <h2 className="text-3xl font-extrabold mb-4">今週の急上昇商品を先に掴む</h2>
        <p className="text-orange-100 mb-8 text-lg">まずは無料サンプルで品質を確認してください</p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <a href="#free-sample"
            className="inline-flex items-center justify-center gap-2 bg-white text-orange-600 font-bold text-lg px-10 py-4 rounded-full hover:bg-orange-50 transition-colors shadow-lg">
            <Gift size={20} /> 無料でレポートを受け取る
          </a>
          <Link href="/checkout?plan=standard"
            className="inline-flex items-center justify-center gap-2 border-2 border-white text-white font-bold text-base px-8 py-4 rounded-full hover:bg-orange-600 transition-colors">
            月額3,980円で始める <ArrowRight size={18} />
          </Link>
        </div>
        <p className="mt-4 text-orange-100 text-sm">14日間返金保証 ／ いつでも解約可能</p>
      </section>

      {/* ── フッター ── */}
      <footer className="py-8 px-4 bg-gray-900 text-gray-500 text-sm text-center">
        <div className="flex justify-center gap-6 mb-4">
          <Link href="/terms" className="hover:text-gray-300">利用規約</Link>
          <Link href="/privacy" className="hover:text-gray-300">プライバシーポリシー</Link>
          <Link href="/contact" className="hover:text-gray-300">お問い合わせ</Link>
        </div>
        <p>© 2026 FBAトレンドレーダー. All rights reserved.</p>
      </footer>
    </div>
  );
}
