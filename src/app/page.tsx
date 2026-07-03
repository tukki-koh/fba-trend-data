import { CheckCircle, TrendingUp, Clock, ShieldCheck, ArrowRight, Gift, Mail, FileText, Search, Star } from "lucide-react";
import Link from "next/link";
import type { Metadata } from "next";
import Script from "next/script";
import FreeSampleForm from "@/components/FreeSampleForm";

export const metadata: Metadata = {
  title: "FBAトレンドレーダー｜Amazon FBA仕入れリサーチを週1回に減らすデータ配信",
  description:
    "毎週月曜の朝、Amazon JPの売れ筋ランキングTOP10をPDFでお届けします。ペット・アウトドア・キッチン・ビューティー・ベビーの5カテゴリ。月額3,980円〜、まず無料サンプルで確認できます。",
};

const PLANS = [
  {
    name: "スタンダード",
    price: "3,980",
    description: "週1回のリサーチで十分な方に",
    features: [
      "週次トレンドレポート（PDF形式）",
      "5カテゴリ × TOP10の商品データ",
      "各商品の現在価格・Amazonリンクつき",
      "毎週月曜 AM7:00 にメール配信",
      "過去4週ぶんのレポートをマイページで閲覧可",
      "14日以内なら理由なしで全額返金",
    ],
    cta: "スタンダードで始める",
    href: "/checkout?plan=standard",
    highlight: false,
  },
  {
    name: "プロ",
    price: "9,800",
    description: "本腰を入れて仕入れデータを使い倒したい方に",
    features: [
      "スタンダードの内容すべて",
      "20カテゴリに拡張したデータ",
      "競合出品者の価格変動アラート",
      "急に順位が上がった新規商品の通知",
      "Excelファイル（.xlsx）でのダウンロード",
      "過去3ヶ月ぶんのアーカイブ",
      "14日以内なら理由なしで全額返金",
    ],
    cta: "プロで始める",
    href: "/checkout?plan=pro",
    highlight: true,
  },
];

const FAQS = [
  {
    q: "具体的にどんなデータが入っていますか？",
    a: "ペット用品・アウトドア・キッチン・ビューティー・ベビーの5カテゴリについて、Amazon JPのベストセラーTOP10をランキング順に並べたPDFです。商品名・現在価格・AmazonへのリンクURLが載っています。見た目はシンプルですが、仕入れリサーチの起点としてそのまま使えるように作っています。",
  },
  {
    q: "毎週いつ届きますか？",
    a: "月曜の朝7時を目安に、登録したメールアドレスへ送っています。データは日曜夜〜月曜早朝に収集しているので、週明けの仕入れ判断にそのまま使っていただけます。",
  },
  {
    q: "無料サンプルはどういう仕組みですか？",
    a: "メールアドレスを入力するだけで、直近の週次レポートを1部お送りします。カード登録は不要です。「どんな内容か確認してから検討したい」という方向けです。",
  },
  {
    q: "合わなかったらすぐ解約できますか？",
    a: "できます。マイページから手続きができて、次の月から請求は止まります。解約金や手数料はありません。",
  },
  {
    q: "14日返金保証というのは？",
    a: "有料プランに登録してから14日以内であれば、理由に関わらず全額返金します。「思っていたのと違った」でも構いません。",
  },
  {
    q: "データはどこから取っているんですか？",
    a: "Amazon JPの公式ベストセラーページ（誰でも見られる公開情報）から毎週自動で収集しています。特別なAPIは使っていないので、Amazonの表示と大きくずれることはありません。",
  },
  {
    q: "スマホで見られますか？",
    a: "PDFなのでスマホでも普通に開けます。マイページもスマホから使えます。",
  },
  {
    q: "プロプランとの違いは何ですか？",
    a: "スタンダードは5カテゴリ、プロは20カテゴリに増えます。加えて、Excelファイルでのダウンロードと、競合出品者の価格変動アラートがつきます。副業でやっている方にはスタンダードで十分なことが多いです。",
  },
];

const SITE_URL = "https://fba-trend-data.vercel.app";

const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebSite",
      "@id": `${SITE_URL}/#website`,
      url: SITE_URL,
      name: "FBAトレンドレーダー",
      description: "Amazon FBA出品者向け週次トレンドデータ配信サービス",
      inLanguage: "ja",
      potentialAction: {
        "@type": "SearchAction",
        target: { "@type": "EntryPoint", urlTemplate: `${SITE_URL}/?q={search_term_string}` },
        "query-input": "required name=search_term_string",
      },
    },
    {
      "@type": "Organization",
      "@id": `${SITE_URL}/#organization`,
      name: "FBAトレンドレーダー",
      url: SITE_URL,
      logo: { "@type": "ImageObject", url: `${SITE_URL}/opengraph-image` },
      description: "Amazon FBA出品者・せどらー向けに全5カテゴリの売れ筋ランキングTOP10を毎週月曜に自動配信するデータサービスです。",
      areaServed: "JP",
      knowsAbout: ["Amazon FBA", "せどり", "Amazon物販", "商品リサーチ", "FBA仕入れ"],
    },
    {
      "@type": "Service",
      "@id": `${SITE_URL}/#service`,
      name: "FBAトレンドレーダー 週次トレンドレポート",
      provider: { "@id": `${SITE_URL}/#organization` },
      serviceType: "データ配信サービス",
      description: "Amazon Japanのベストセラーページから毎週自動収集したトレンドデータを、ペット用品・アウトドア・キッチン・ビューティー・ベビーの5カテゴリTOP10としてPDFレポートで毎週月曜AM7:00に配信します。",
      offers: [
        {
          "@type": "Offer",
          name: "スタンダードプラン",
          price: "3980",
          priceCurrency: "JPY",
          priceSpecification: { "@type": "RecurringCharges", billingPeriod: "P1M" },
          description: "全5カテゴリTOP10・PDFレポート・過去4週アーカイブ・14日返金保証",
        },
        {
          "@type": "Offer",
          name: "プロプラン",
          price: "9800",
          priceCurrency: "JPY",
          priceSpecification: { "@type": "RecurringCharges", billingPeriod: "P1M" },
          description: "全20カテゴリ・Excelデータ・過去3ヶ月アーカイブ・競合価格アラート・14日返金保証",
        },
      ],
      hasOfferCatalog: {
        "@type": "OfferCatalog",
        name: "FBAトレンドレーダー プランご案内",
      },
    },
    {
      "@type": "HowTo",
      name: "FBAトレンドレーダーの使い方",
      description: "Amazon FBA仕入れリサーチをFBAトレンドレーダーで効率化する方法",
      step: [
        { "@type": "HowToStep", position: 1, name: "無料サンプルを受け取る", text: "メールアドレスを入力して最新レポートを無料で受け取り、データの品質を確認します。" },
        { "@type": "HowToStep", position: 2, name: "プランを選択する", text: "スタンダード（月額3,980円）またはプロ（月額9,800円）プランを選択します。" },
        { "@type": "HowToStep", position: 3, name: "毎週月曜に受信する", text: "毎週月曜AM7:00に最新のトレンドレポートPDFがメールで届きます。" },
        { "@type": "HowToStep", position: 4, name: "仕入れ判断に活用する", text: "今週急上昇中のカテゴリ・商品データをもとに仕入れリサーチを効率化します。" },
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

// ── 実物レポートのプレビュー（信頼感の核） ──────────────
const PREVIEW_ROWS = [
  { rank: 1, name: "ペット用 自動給水器 2.5L 静音", price: "¥3,480", up: true },
  { rank: 2, name: "猫砂 ニオイをとる砂 5.5L × 4袋", price: "¥1,980", up: false },
  { rank: 3, name: "犬用 歯みがきガム 大容量 100本", price: "¥1,280", up: true },
  { rank: 4, name: "ペットカメラ 見守り 首振り対応", price: "¥4,980", up: false },
  { rank: 5, name: "おくだけ吸着 撥水タイルマット", price: "¥2,680", up: false },
];

function ReportPreview() {
  return (
    <div className="relative">
      {/* 背景の重なり演出 */}
      <div className="absolute -inset-3 bg-amber-200/30 rounded-[28px] rotate-2 hidden sm:block" aria-hidden />
      <div className="relative bg-white rounded-2xl border border-stone-200/80 shadow-xl shadow-stone-300/40 overflow-hidden">
        {/* ウィンドウバー */}
        <div className="flex items-center gap-2 px-4 py-3 border-b border-stone-100 bg-stone-50/80">
          <span className="w-3 h-3 rounded-full bg-stone-300" />
          <span className="w-3 h-3 rounded-full bg-stone-300" />
          <span className="w-3 h-3 rounded-full bg-stone-300" />
          <div className="flex items-center gap-1.5 ml-3 text-xs text-stone-400">
            <FileText size={12} /> weekly_report_2026-W27.pdf
          </div>
        </div>

        {/* レポート本体 */}
        <div className="p-5 sm:p-6">
          <div className="flex items-center justify-between mb-1">
            <div className="text-[11px] font-semibold tracking-wide text-amber-600 uppercase">Weekly Report</div>
            <div className="text-[11px] text-stone-400">2026年 第27週</div>
          </div>
          <div className="flex items-baseline gap-2 mb-4">
            <h3 className="text-lg font-bold text-stone-900">ペット用品</h3>
            <span className="text-xs text-stone-400">ベストセラー TOP5（全10位まで収録）</span>
          </div>

          <div className="space-y-1.5">
            {PREVIEW_ROWS.map((r) => (
              <div key={r.rank} className="flex items-center gap-3 py-2 px-2.5 rounded-lg hover:bg-amber-50/60">
                <span className={`shrink-0 w-6 h-6 rounded-md text-xs font-bold flex items-center justify-center ${
                  r.rank === 1 ? "bg-amber-500 text-white" : "bg-stone-100 text-stone-500"
                }`}>{r.rank}</span>
                <span className="flex-1 text-sm text-stone-700 truncate">{r.name}</span>
                {r.up && (
                  <span className="hidden sm:inline-flex items-center gap-0.5 text-[10px] font-semibold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">
                    <TrendingUp size={10} /> 上昇
                  </span>
                )}
                <span className="shrink-0 text-sm font-semibold text-stone-900 tabular-nums">{r.price}</span>
              </div>
            ))}
          </div>

          <div className="mt-4 pt-4 border-t border-stone-100 flex items-center justify-between text-xs text-stone-400">
            <span>ペット・アウトドア・キッチン・ビューティー・ベビー</span>
            <span className="text-amber-600 font-medium">Amazonリンク付き →</span>
          </div>
        </div>
      </div>

      {/* 届いたメール風のフローティングチップ */}
      <div className="hidden md:flex absolute -bottom-5 -left-6 items-center gap-2.5 bg-white rounded-xl border border-stone-200 shadow-lg shadow-stone-300/40 px-4 py-3">
        <span className="w-9 h-9 rounded-full bg-amber-100 flex items-center justify-center">
          <Mail size={16} className="text-amber-600" />
        </span>
        <div className="leading-tight">
          <div className="text-xs font-semibold text-stone-800">毎週月曜 7:00 に到着</div>
          <div className="text-[11px] text-stone-400">開くだけで今週の売れ筋がわかる</div>
        </div>
      </div>
    </div>
  );
}

const TRUST_CHIPS = [
  { icon: <ShieldCheck size={15} />, label: "14日間 全額返金保証" },
  { icon: <CheckCircle size={15} />, label: "カード登録なしで試せる" },
  { icon: <Clock size={15} />, label: "解約はいつでも1クリック" },
];

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#faf9f7] text-stone-700 antialiased">
      <Script id="json-ld" type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />

      {/* ── ナビ ── */}
      <nav className="fixed top-0 w-full bg-[#faf9f7]/85 backdrop-blur-md border-b border-stone-200/70 z-50">
        <div className="max-w-6xl mx-auto px-5 h-16 flex items-center justify-between">
          <span className="flex items-center gap-2 font-bold text-[15px] text-stone-900">
            <span className="w-7 h-7 rounded-lg bg-amber-500 text-white flex items-center justify-center text-xs">FB</span>
            FBAトレンドレーダー
          </span>
          <div className="flex items-center gap-5">
            <a href="#pricing" className="hidden sm:inline text-sm text-stone-500 hover:text-stone-900 transition-colors">料金</a>
            <a href="#faq" className="hidden sm:inline text-sm text-stone-500 hover:text-stone-900 transition-colors">よくある質問</a>
            <Link href="/checkout?plan=standard"
              className="bg-stone-900 hover:bg-stone-800 text-white text-sm font-semibold px-4 py-2 rounded-full transition-colors">
              今すぐ始める
            </Link>
          </div>
        </div>
      </nav>

      {/* ── ヒーロー ── */}
      <section className="relative pt-28 pb-20 md:pt-36 md:pb-28 px-5 overflow-hidden">
        {/* 背景の柔らかいグロー */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[900px] h-[600px] bg-gradient-to-b from-amber-100/60 via-amber-50/30 to-transparent blur-3xl -z-10" aria-hidden />
        <div className="max-w-6xl mx-auto grid lg:grid-cols-[1.05fr_1fr] gap-14 lg:gap-10 items-center">
          {/* 左：コピー */}
          <div className="text-center lg:text-left">
            <div className="inline-flex items-center gap-2 bg-white border border-stone-200 text-stone-600 text-xs font-medium px-3.5 py-1.5 rounded-full mb-6 shadow-sm">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              Amazon FBA・せどり専用のトレンドデータ配信
            </div>
            <h1 className="text-[2.1rem] sm:text-5xl font-bold leading-[1.15] tracking-tight mb-6 text-stone-900" data-speakable>
              仕入れリサーチは、<br />
              <span className="relative inline-block">
                <span className="relative z-10">週1通のメール</span>
                <span className="absolute bottom-1 left-0 w-full h-3 bg-amber-200/70 -z-0" aria-hidden />
              </span>
              <span className="inline-block">だけでいい。</span>
            </h1>
            <p className="text-base sm:text-lg text-stone-600 mb-8 leading-relaxed max-w-xl mx-auto lg:mx-0" data-speakable>
              Amazon JPの売れ筋ランキングTOP10を、毎週月曜の朝に自動でお届け。
              5カテゴリ分のリサーチが、コーヒーを淹れる間に終わります。
            </p>

            <div className="flex flex-col sm:flex-row gap-3 justify-center lg:justify-start mb-7">
              <Link href="/checkout?plan=standard"
                className="group inline-flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-600 text-white text-base font-bold px-7 py-4 rounded-full transition-all shadow-lg shadow-amber-500/25 hover:shadow-amber-500/40">
                月額3,980円で始める
                <ArrowRight size={18} className="group-hover:translate-x-0.5 transition-transform" />
              </Link>
              <a href="#free-sample"
                className="inline-flex items-center justify-center gap-2 bg-white border border-stone-200 text-stone-800 hover:border-stone-300 text-base font-semibold px-7 py-4 rounded-full transition-colors">
                <Gift size={18} className="text-amber-500" /> 無料で中身を見る
              </a>
            </div>

            <div className="flex flex-wrap items-center justify-center lg:justify-start gap-x-5 gap-y-2">
              {TRUST_CHIPS.map((c) => (
                <span key={c.label} className="inline-flex items-center gap-1.5 text-[13px] text-stone-500">
                  <span className="text-emerald-500">{c.icon}</span> {c.label}
                </span>
              ))}
            </div>
          </div>

          {/* 右：実物プレビュー */}
          <div className="lg:pl-4">
            <ReportPreview />
          </div>
        </div>
      </section>

      {/* ── 信頼バンド（実績数字） ── */}
      <section className="px-5">
        <div className="max-w-5xl mx-auto bg-stone-900 rounded-3xl px-6 py-10 md:py-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            {[
              { num: "5", label: "分析カテゴリ", sub: "プロプランは20" },
              { num: "TOP10", label: "毎週の掲載順位", sub: "価格・リンク付き" },
              { num: "月曜 7:00", label: "自動でメール配信", sub: "受け取るだけ" },
              { num: "14日", label: "全額返金保証", sub: "理由は問いません" },
            ].map((item) => (
              <div key={item.label}>
                <div className="text-2xl md:text-3xl font-bold text-amber-400 tracking-tight">{item.num}</div>
                <div className="text-sm text-white mt-1.5 font-medium">{item.label}</div>
                <div className="text-[11px] text-stone-400 mt-0.5">{item.sub}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 課題 ── */}
      <section className="py-20 md:py-28 px-5">
        <div className="max-w-3xl mx-auto text-center">
          <div className="text-sm font-semibold text-amber-600 mb-3">なぜ、このサービスなのか</div>
          <h2 className="text-2xl md:text-3xl font-bold mb-6 text-stone-900 leading-snug">
            仕入れの成否は、<br className="sm:hidden" />リサーチにかける時間で決まる。<br />
            でも、その時間がいちばん足りない。
          </h2>
          <p className="text-stone-600 leading-relaxed max-w-2xl mx-auto">
            ランキングを開いて、価格を調べて、ライバルの数を数えて——
            カテゴリを1つ見るだけで30分。5カテゴリなら、それだけで週の半日が消えます。
            <br className="hidden sm:block" />
            FBAトレンドレーダーは、この一連の作業を「月曜の朝に届く1通のメール」に置き換えます。
          </p>
        </div>

        {/* Before / After */}
        <div className="max-w-4xl mx-auto mt-14 grid md:grid-cols-2 gap-5">
          <div className="bg-white rounded-2xl border border-stone-200 p-7">
            <div className="text-xs font-semibold text-stone-400 uppercase tracking-wide mb-4">これまで</div>
            <ul className="space-y-3.5">
              {[
                "5カテゴリを毎週、手作業で見て回る",
                "気になる商品を見つけるたび価格を調べ直す",
                "どのカテゴリが伸びているか、見比べる基準がない",
              ].map((t) => (
                <li key={t} className="flex items-start gap-3 text-sm text-stone-500">
                  <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-stone-300 shrink-0" />
                  <span className="line-through decoration-stone-300">{t}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="bg-amber-50 rounded-2xl border border-amber-200 p-7">
            <div className="text-xs font-semibold text-amber-600 uppercase tracking-wide mb-4">これから</div>
            <ul className="space-y-3.5">
              {[
                "月曜の朝、メールを開くだけで5カテゴリが揃う",
                "価格とAmazonリンクが最初から付いている",
                "5カテゴリの順位が1枚に並び、伸びが一目でわかる",
              ].map((t) => (
                <li key={t} className="flex items-start gap-3 text-sm text-stone-800 font-medium">
                  <CheckCircle size={16} className="text-amber-500 mt-0.5 shrink-0" />
                  <span>{t}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* ── 使い方 3ステップ ── */}
      <section className="py-20 md:py-24 px-5 bg-white border-y border-stone-100">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-2xl md:text-3xl font-bold text-stone-900 mb-3">始め方は、かんたん3ステップ</h2>
            <p className="text-stone-500">登録から最初のレポートまで、待ち時間はありません。</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: <Gift size={22} className="text-amber-500" />, step: "01", title: "無料サンプルを受け取る", desc: "メールアドレスだけで、直近のレポートを1部お届け。カード登録は不要です。" },
              { icon: <Search size={22} className="text-amber-500" />, step: "02", title: "中身を見て決める", desc: "データの粒度と使い勝手を確認してから、続けるかどうか判断してください。" },
              { icon: <Mail size={22} className="text-amber-500" />, step: "03", title: "毎週月曜に受け取る", desc: "以降は自動配信。届いたメールを開くだけで、その週のリサーチが完了します。" },
            ].map((s) => (
              <div key={s.step} className="relative">
                <div className="flex items-center gap-3 mb-4">
                  <span className="w-11 h-11 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center">{s.icon}</span>
                  <span className="text-3xl font-bold text-stone-200">{s.step}</span>
                </div>
                <h3 className="font-semibold text-stone-900 mb-2">{s.title}</h3>
                <p className="text-sm text-stone-500 leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 無料サンプル ── */}
      <section id="free-sample" className="scroll-mt-20 py-20 md:py-24 px-5">
        <div className="max-w-2xl mx-auto text-center bg-white rounded-3xl border border-stone-200 shadow-sm p-8 md:p-12">
          <div className="inline-flex items-center gap-2 bg-amber-50 text-amber-700 text-xs font-semibold px-3 py-1.5 rounded-full mb-5">
            <Gift size={13} /> まずは無料で
          </div>
          <h2 className="text-2xl md:text-3xl font-bold mb-3 text-stone-900">
            実際のレポートを、1部お送りします
          </h2>
          <p className="text-stone-600 mb-1 leading-relaxed">
            メールアドレスを入れるだけ。直近の週次レポートがそのまま届きます。
          </p>
          <p className="text-stone-400 text-sm mb-8">カード登録なし。気に入らなければ、そのまま終わりで大丈夫です。</p>
          <FreeSampleForm />
        </div>
      </section>

      {/* ── レポート内容 ── */}
      <section className="py-20 md:py-24 px-5 bg-white border-y border-stone-100">
        <div className="max-w-5xl mx-auto">
          <div className="max-w-2xl mb-12">
            <h2 className="text-2xl md:text-3xl font-bold mb-3 text-stone-900">1通に、必要なものだけを。</h2>
            <p className="text-stone-500">毎週月曜 AM7:00、PDFで届きます。開いてすぐ仕入れ判断に使える構成です。</p>
          </div>
          <div className="grid md:grid-cols-3 gap-5">
            {[
              {
                icon: <TrendingUp size={22} className="text-amber-500" />,
                title: "カテゴリ別 TOP10",
                desc: "ペット用品・アウトドア・キッチン・ビューティー・ベビー。各カテゴリで上位10商品の順位と商品名が並びます。",
              },
              {
                icon: <FileText size={22} className="text-amber-500" />,
                title: "その週の価格データ",
                desc: "各商品の収集時点での価格を掲載。仕入れ値との比較や利益計算にそのまま使えます。",
              },
              {
                icon: <ArrowRight size={22} className="text-amber-500" />,
                title: "Amazonへの直リンク",
                desc: "商品名からワンタップでAmazonの商品ページへ。詳細の確認がスムーズに進みます。",
              },
            ].map((feat) => (
              <div key={feat.title} className="bg-[#faf9f7] rounded-2xl p-7 border border-stone-100 hover:border-amber-200 transition-colors">
                <div className="w-11 h-11 rounded-xl bg-white border border-stone-100 flex items-center justify-center mb-4">{feat.icon}</div>
                <h3 className="font-semibold text-base mb-2 text-stone-900">{feat.title}</h3>
                <p className="text-stone-500 text-sm leading-relaxed">{feat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 料金 ── */}
      <section id="pricing" className="scroll-mt-20 py-20 md:py-28 px-5">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold mb-3 text-stone-900">シンプルな2つのプラン</h2>
            <p className="text-stone-500">どちらも14日間の返金保証つき。まず気軽に試してください。</p>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            {PLANS.map((plan) => (
              <div key={plan.name}
                className={`relative rounded-3xl p-8 flex flex-col ${
                  plan.highlight
                    ? "bg-stone-900 text-white shadow-2xl shadow-stone-400/30"
                    : "bg-white border border-stone-200"
                }`}>
                {plan.highlight && (
                  <div className="absolute top-6 right-6 inline-flex items-center gap-1 bg-amber-500 text-white text-[11px] font-bold px-2.5 py-1 rounded-full">
                    <Star size={11} className="fill-white" /> 人気 No.1
                  </div>
                )}
                <div className={`text-sm font-semibold mb-1 ${plan.highlight ? "text-amber-400" : "text-amber-600"}`}>{plan.name}</div>
                <div className={`text-sm mb-5 ${plan.highlight ? "text-stone-400" : "text-stone-500"}`}>{plan.description}</div>
                <div className="flex items-baseline gap-1 mb-1">
                  <span className={`text-4xl font-bold tracking-tight ${plan.highlight ? "text-white" : "text-stone-900"}`}>¥{plan.price}</span>
                  <span className={`text-sm ${plan.highlight ? "text-stone-400" : "text-stone-500"}`}>/月（税込）</span>
                </div>
                <div className={`text-xs mb-7 ${plan.highlight ? "text-stone-500" : "text-stone-400"}`}>月額自動更新・いつでも解約可</div>
                <ul className="space-y-3 mb-8 flex-1">
                  {plan.features.map((f) => (
                    <li key={f} className={`flex items-start gap-2.5 text-sm ${plan.highlight ? "text-stone-200" : "text-stone-700"}`}>
                      <CheckCircle size={16} className={`mt-0.5 shrink-0 ${plan.highlight ? "text-amber-400" : "text-amber-500"}`} />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
                <Link href={plan.href}
                  className={`w-full text-center py-3.5 rounded-full font-semibold text-base transition-colors ${
                    plan.highlight
                      ? "bg-amber-500 hover:bg-amber-400 text-white"
                      : "bg-stone-900 hover:bg-stone-800 text-white"
                  }`}>
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
          <p className="text-center text-stone-500 text-sm mt-8">
            決めきれないときは →{" "}
            <a href="#free-sample" className="text-amber-600 font-semibold hover:underline">
              無料サンプルで中身を確認する
            </a>
          </p>
        </div>
      </section>

      {/* ── お客様の声 ── */}
      <section className="py-20 md:py-24 px-5 bg-white border-y border-stone-100">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold mb-3 text-stone-900">使っている方の声</h2>
            <p className="text-stone-500">実際に利用しているFBA出品者・せどらーの方からのコメントです。</p>
          </div>
          <div className="grid md:grid-cols-2 gap-5">
            {[
              {
                body: "仕入れリサーチに週3〜4時間かけていたのが、このメール1本で済むようになりました。具体的な商品名と価格が付いているので、受け取ってすぐ使えます。「まず何を見ればいいか」で悩む時間が一番もったいなかったので、そこが消えただけでかなり変わりました。",
                name: "T.M.",
                profile: "副業FBA・歴2年 / 30代男性",
              },
              {
                body: "子育ての合間にリサーチする時間がなくて困っていました。毎週月曜の朝に届くので、週の仕入れ計画を立てるタイミングとちょうど合っています。自分でAmazonを見に行かなくていいのが、思っていた以上に楽でした。",
                name: "K.Y.",
                profile: "主婦・副業物販 / 40代女性",
              },
              {
                body: "FBAを始めたばかりで、何を仕入れればいいのかまったく分からなかったです。ベストセラーのデータを見て、上位の商品を調べて真似するだけで最初の売上が立ちました。何から手をつければいいか分からなかったので助かりました。",
                name: "R.I.",
                profile: "FBA初心者 / 20代",
              },
              {
                body: "以前は自分でAmazonを眺めてメモして…という作業をしていましたが、それが不要になった分、仕入れ自体に使える時間が増えました。データがシンプルなので、自分のスプレッドシートに転記しやすいのも地味に助かっています。",
                name: "H.S.",
                profile: "せどり経験者 / 30代男性",
              },
            ].map((t) => (
              <div key={t.name} className="bg-[#faf9f7] border border-stone-200 rounded-2xl p-7">
                <div className="flex gap-0.5 mb-4" aria-hidden>
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Star key={i} size={14} className="fill-amber-400 text-amber-400" />
                  ))}
                </div>
                <p className="text-stone-700 text-sm leading-relaxed mb-6">{t.body}</p>
                <div className="flex items-center gap-3 border-t border-stone-200 pt-4">
                  <span className="w-9 h-9 rounded-full bg-amber-100 text-amber-700 text-sm font-bold flex items-center justify-center">
                    {t.name.charAt(0)}
                  </span>
                  <div>
                    <div className="font-semibold text-stone-900 text-sm">{t.name} さん</div>
                    <div className="text-xs text-stone-400">{t.profile}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 返金保証 ── */}
      <section className="py-16 px-5">
        <div className="max-w-3xl mx-auto bg-amber-50 border border-amber-200 rounded-3xl p-8 md:p-10 flex flex-col sm:flex-row items-center gap-6 text-center sm:text-left">
          <span className="shrink-0 w-16 h-16 rounded-2xl bg-white border border-amber-200 flex items-center justify-center">
            <ShieldCheck size={30} className="text-amber-500" />
          </span>
          <div>
            <h2 className="text-xl font-bold text-stone-900 mb-2">14日間、まるごと返金保証</h2>
            <p className="text-stone-600 text-sm leading-relaxed">
              有料プランに進んだあとでも、14日以内なら理由を問わず全額返金します。
              「思っていたのと違った」で構いません。合うかどうかを、リスクなしで確かめてください。
            </p>
          </div>
        </div>
      </section>

      {/* ── FAQ ── */}
      <section id="faq" className="scroll-mt-20 py-20 md:py-24 px-5 bg-white border-t border-stone-100">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold mb-10 text-stone-900 text-center">よくある質問</h2>
          <div className="space-y-3">
            {FAQS.map((faq) => (
              <details key={faq.q} className="group bg-[#faf9f7] rounded-2xl border border-stone-200 p-6 [&_summary]:list-none">
                <summary className="flex items-center justify-between gap-4 cursor-pointer font-semibold text-stone-900 leading-snug">
                  {faq.q}
                  <span className="shrink-0 w-6 h-6 rounded-full bg-white border border-stone-200 flex items-center justify-center text-stone-400 group-open:rotate-45 transition-transform">＋</span>
                </summary>
                <div className="text-stone-600 text-sm leading-relaxed mt-4">{faq.a}</div>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* ── 最終CTA ── */}
      <section className="px-5 pb-24 pt-4">
        <div className="max-w-4xl mx-auto bg-stone-900 rounded-3xl px-6 py-14 md:py-20 text-center relative overflow-hidden">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[300px] bg-amber-500/20 blur-3xl" aria-hidden />
          <div className="relative">
            <h2 className="text-2xl md:text-4xl font-bold mb-4 text-white leading-tight">
              今週のリサーチ、<br className="sm:hidden" />もう自分でやらなくていい。
            </h2>
            <p className="text-stone-300 mb-9 leading-relaxed max-w-xl mx-auto">
              まずは無料サンプルで中身を確認してください。
              続けると決めたあとも、14日以内なら全額返金します。
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <a href="#free-sample"
                className="inline-flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-400 text-white font-bold text-base px-8 py-4 rounded-full transition-colors">
                <Gift size={18} /> 無料サンプルを受け取る
              </a>
              <Link href="/checkout?plan=standard"
                className="inline-flex items-center justify-center gap-2 bg-white/10 hover:bg-white/15 border border-white/20 text-white font-semibold text-base px-8 py-4 rounded-full transition-colors">
                月額3,980円で始める <ArrowRight size={16} />
              </Link>
            </div>
            <p className="text-stone-500 text-xs mt-6">カード登録なしで無料サンプル ／ 解約はいつでも1クリック</p>
          </div>
        </div>
      </section>

      {/* ── フッター ── */}
      <footer className="py-10 px-5 border-t border-stone-200">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <span className="flex items-center gap-2 font-bold text-sm text-stone-900">
            <span className="w-6 h-6 rounded-md bg-amber-500 text-white flex items-center justify-center text-[10px]">FB</span>
            FBAトレンドレーダー
          </span>
          <div className="flex gap-6 text-sm text-stone-500">
            <Link href="/terms" className="hover:text-stone-900 transition-colors">利用規約</Link>
            <Link href="/privacy" className="hover:text-stone-900 transition-colors">プライバシーポリシー</Link>
            <Link href="/contact" className="hover:text-stone-900 transition-colors">お問い合わせ</Link>
          </div>
          <p className="text-xs text-stone-400">© 2026 FBAトレンドレーダー</p>
        </div>
      </footer>
    </div>
  );
}
