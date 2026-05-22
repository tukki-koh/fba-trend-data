import { CheckCircle, TrendingUp, BarChart2, Zap, ArrowRight, Star } from "lucide-react";
import Link from "next/link";
import type { Metadata } from "next";
import Script from "next/script";

export const metadata: Metadata = {
  title: "FBAトレンドレーダー｜Amazon売れ筋トレンドを毎週自動配信",
  description:
    "Amazon FBA出品者・せどらー向けに全5カテゴリの売れ筋ランキングTOP10を毎週月曜に自動配信。仕入れ判断・商品リサーチを効率化。月額3,980円〜・14日返金保証。",
};

const PLANS = [
  {
    name: "スタンダード",
    price: "3,980",
    description: "副業FBA出品者向け",
    features: [
      "週次トレンドレポート（PDF）",
      "注目カテゴリ TOP10",
      "急上昇キーワード20件",
      "メール自動配信",
      "過去4週分のアーカイブ閲覧",
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
      "カテゴリ別詳細データ（全20カテゴリ）",
      "競合出品者の価格変動アラート",
      "新規参入商品の急騰データ",
      "Excelデータ(.xlsx)ダウンロード",
      "過去3ヶ月アーカイブ閲覧",
    ],
    cta: "プロで始める",
    href: "/checkout?plan=pro",
    highlight: true,
  },
];

const FAQS = [
  {
    q: "どんなデータが届きますか？",
    a: "Amazon Japanの各カテゴリで急上昇している商品の売れ筋ランキング変動、新規参入商品の急騰パターン、注目キーワードなどをまとめたPDFレポートが毎週届きます。",
  },
  {
    q: "いつレポートが届きますか？",
    a: "毎週月曜日の朝7時に、登録メールアドレスへ自動送信されます。",
  },
  {
    q: "解約はいつでもできますか？",
    a: "はい。マイページから1クリックでいつでも解約できます。違約金・解約手数料は一切ありません。",
  },
  {
    q: "無料トライアルはありますか？",
    a: "現在は14日間の全額返金保証を提供しています。万が一満足いただけない場合は全額返金します。",
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
        {
          "@type": "Offer",
          name: "スタンダードプラン",
          price: "3980",
          priceCurrency: "JPY",
          billingIncrement: "P1M",
          description: "全5カテゴリTOP10週次PDFレポート",
        },
        {
          "@type": "Offer",
          name: "プロプラン",
          price: "9800",
          priceCurrency: "JPY",
          billingIncrement: "P1M",
          description: "全20カテゴリ詳細データ＋競合分析",
        },
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
      <Script
        id="json-ld"
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      {/* ナビゲーション */}
      <nav className="fixed top-0 w-full bg-white/90 backdrop-blur-sm border-b border-gray-100 z-50">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <span className="font-bold text-lg text-orange-500">FBAトレンドレーダー</span>
          <Link
            href="/checkout?plan=standard"
            className="bg-orange-500 hover:bg-orange-600 text-white text-sm font-semibold px-4 py-2 rounded-full transition-colors"
          >
            今すぐ始める
          </Link>
        </div>
      </nav>

      {/* ヒーロー */}
      <section className="pt-28 pb-20 px-4 bg-gradient-to-b from-orange-50 to-white">
        <div className="max-w-3xl mx-auto text-center animate-fade-in-up">
          <div className="inline-flex items-center gap-2 bg-orange-100 text-orange-700 text-sm font-semibold px-4 py-1.5 rounded-full mb-6">
            <Zap size={14} />
            毎週月曜日に自動配信
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold leading-tight tracking-tight mb-6">
            Amazonで<span className="text-orange-500">今週売れる商品</span>を<br />
            データで先回りする
          </h1>
          <p className="text-xl text-gray-600 mb-10 leading-relaxed">
            FBAトレンドレーダーは、Amazon Japan全カテゴリの売れ筋変動・急騰商品・注目キーワードを<br className="hidden md:block" />
            毎週自動分析してあなたのメールに届けるデータ配信サービスです。
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/checkout?plan=standard"
              className="inline-flex items-center justify-center gap-2 bg-orange-500 hover:bg-orange-600 text-white text-lg font-bold px-8 py-4 rounded-full transition-colors shadow-lg shadow-orange-200"
            >
              月額3,980円で始める <ArrowRight size={20} />
            </Link>
            <a
              href="#pricing"
              className="inline-flex items-center justify-center gap-2 border border-gray-300 hover:border-orange-400 text-gray-700 text-lg font-semibold px-8 py-4 rounded-full transition-colors"
            >
              プランを見る
            </a>
          </div>
          <p className="mt-4 text-sm text-gray-500">14日間返金保証 ／ クレジットカード不要でキャンセル可</p>
        </div>
      </section>

      {/* 数字で実績 */}
      <section className="py-14 bg-gray-900 text-white">
        <div className="max-w-5xl mx-auto px-4 grid grid-cols-3 gap-8 text-center">
          {[
            { num: "20+", label: "分析カテゴリ数" },
            { num: "週次", label: "データ更新頻度" },
            { num: "14日", label: "全額返金保証" },
          ].map((item) => (
            <div key={item.label}>
              <div className="text-3xl md:text-4xl font-extrabold text-orange-400">{item.num}</div>
              <div className="text-sm text-gray-400 mt-1">{item.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* 課題 → 解決 */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-extrabold text-center mb-14">
            こんな悩みを抱えていませんか？
          </h2>
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
              "今週急上昇中の商品カテゴリがひと目でわかる",
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

      {/* 機能 */}
      <section className="py-20 px-4 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-extrabold text-center mb-14">レポートに含まれるデータ</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: <TrendingUp size={28} className="text-orange-500" />,
                title: "急上昇商品 TOP20",
                desc: "前週比でランキングが急騰している商品と詳細データ",
              },
              {
                icon: <BarChart2 size={28} className="text-orange-500" />,
                title: "カテゴリ別トレンド",
                desc: "20カテゴリ別の売れ筋傾向と注目商品の属性分析",
              },
              {
                icon: <Star size={28} className="text-orange-500" />,
                title: "注目キーワード20件",
                desc: "検索数が急増しているキーワードと関連カテゴリ",
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

      {/* 料金 */}
      <section id="pricing" className="py-20 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-extrabold text-center mb-4">料金プラン</h2>
          <p className="text-center text-gray-500 mb-12">全プラン14日間返金保証付き</p>
          <div className="grid md:grid-cols-2 gap-8">
            {PLANS.map((plan) => (
              <div
                key={plan.name}
                className={`rounded-2xl p-8 border-2 flex flex-col ${
                  plan.highlight
                    ? "border-orange-500 bg-orange-50 shadow-xl shadow-orange-100"
                    : "border-gray-200 bg-white"
                }`}
              >
                {plan.highlight && (
                  <div className="inline-block bg-orange-500 text-white text-xs font-bold px-3 py-1 rounded-full mb-4 self-start">
                    人気 No.1
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
                <Link
                  href={plan.href}
                  className={`w-full text-center py-3.5 rounded-full font-bold text-base transition-colors ${
                    plan.highlight
                      ? "bg-orange-500 hover:bg-orange-600 text-white"
                      : "bg-gray-900 hover:bg-gray-700 text-white"
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
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

      {/* CTA */}
      <section className="py-20 px-4 bg-orange-500 text-white text-center">
        <h2 className="text-3xl font-extrabold mb-4">今週の急上昇商品を先に掴む</h2>
        <p className="text-orange-100 mb-8 text-lg">毎週月曜日7時、あなたのメールに自動配信</p>
        <Link
          href="/checkout?plan=standard"
          className="inline-flex items-center gap-2 bg-white text-orange-600 font-bold text-lg px-10 py-4 rounded-full hover:bg-orange-50 transition-colors shadow-lg"
        >
          月額3,980円で今すぐ始める <ArrowRight size={20} />
        </Link>
        <p className="mt-4 text-orange-100 text-sm">14日間返金保証 ／ いつでも解約可能</p>
      </section>

      {/* フッター */}
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
