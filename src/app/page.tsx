import { CheckCircle, TrendingUp, BarChart2, Zap, ArrowRight, Star, Gift } from "lucide-react";
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
    cta: "スタンダードプランで始める",
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
    cta: "プロプランで始める",
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

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#fafaf9] text-gray-800">
      <Script id="json-ld" type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />

      {/* ── ナビ ── */}
      <nav className="fixed top-0 w-full bg-[#fafaf9]/95 backdrop-blur-sm border-b border-amber-100 z-50">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <span className="font-bold text-lg text-amber-600">📦 FBAトレンドレーダー</span>
          <div className="flex items-center gap-3">
            <a href="#free-sample"
              className="hidden sm:inline-flex items-center gap-1 text-amber-700 font-semibold text-sm hover:underline">
              <Gift size={14} /> 無料で試す
            </a>
            <Link href="/checkout?plan=standard"
              className="bg-amber-500 hover:bg-amber-600 text-white text-sm font-semibold px-4 py-2 rounded-full transition-colors">
              今すぐ始める
            </Link>
          </div>
        </div>
      </nav>

      {/* ── お知らせバー ── */}
      <div className="bg-amber-50 border-b border-amber-200 text-amber-800 text-sm text-center py-2.5 pt-16">
        毎週月曜 AM7:00 配信中 —
        <a href="#free-sample" className="font-semibold underline ml-1 hover:text-amber-900">無料サンプルを受け取る</a>
      </div>

      {/* ── ヒーロー ── */}
      <section className="pt-12 pb-20 px-4 bg-gradient-to-b from-amber-50/70 to-[#fafaf9]">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-amber-100 text-amber-700 text-sm font-medium px-4 py-1.5 rounded-full mb-6">
            <Zap size={14} /> Amazon FBA・せどり向けデータ配信
          </div>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight tracking-tight mb-6 text-gray-900" data-speakable>
            仕入れリサーチ、<br />
            <span className="text-amber-600">週1回のメールだけ</span>で済ませる
          </h1>
          <p className="text-lg text-gray-600 mb-4 leading-relaxed" data-speakable>
            Amazon JPのベストセラーTOP10を毎週月曜の朝にお届けします。<br className="hidden md:block" />
            ペット用品・アウトドア・キッチン・ビューティー・ベビーの5カテゴリ。
          </p>
          <p className="text-sm text-gray-500 mb-8 leading-relaxed max-w-xl mx-auto">
            自分でリサーチすると1カテゴリでも30分以上かかります。
            このサービスはそこを自動化して、月曜の朝に届く1通のメールに全部まとめています。
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-4">
            <Link href="/checkout?plan=standard"
              className="inline-flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-600 text-white text-lg font-bold px-8 py-4 rounded-2xl transition-colors shadow-md shadow-amber-100">
              月額3,980円で始める <ArrowRight size={20} />
            </Link>
            <a href="#free-sample"
              className="inline-flex items-center justify-center gap-2 border border-amber-300 text-amber-700 hover:bg-amber-50 text-base font-semibold px-8 py-4 rounded-2xl transition-colors bg-white">
              <Gift size={18} /> まず無料で中身を確認する
            </a>
          </div>
          <p className="text-sm text-gray-400">14日間返金保証 ／ 解約はマイページから1クリック</p>
        </div>
      </section>

      {/* ── 実績数字 ── */}
      <section className="py-14 bg-slate-700 text-white">
        <div className="max-w-5xl mx-auto px-4 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          {[
            { num: "5",     label: "分析カテゴリ" },
            { num: "TOP10", label: "ランキング公開" },
            { num: "毎週月曜", label: "自動配信" },
            { num: "14日",  label: "全額返金保証" },
          ].map((item) => (
            <div key={item.label}>
              <div className="text-3xl md:text-4xl font-bold text-amber-300">{item.num}</div>
              <div className="text-sm text-slate-300 mt-1">{item.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── 無料サンプルセクション ── */}
      <section id="free-sample" className="py-20 px-4 bg-gradient-to-b from-amber-50/50 to-[#fafaf9]">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4 text-gray-900">
            まずレポートの中身を見てみる
          </h2>
          <p className="text-gray-600 mb-2 leading-relaxed">
            メールアドレスだけで、直近の週次レポートを1部お送りします。
          </p>
          <p className="text-gray-500 text-sm mb-8">カード登録なし。気に入らなければそのまま終わりで大丈夫です。</p>
          <FreeSampleForm />
          <p className="mt-6 text-xs text-gray-400">登録後は毎週月曜に配信案内が届きます。不要になったらいつでも停止できます。</p>
        </div>
      </section>

      {/* ── 課題 → 解決 ── */}
      <section className="py-20 px-4 bg-white">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold mb-6 text-gray-900">仕入れリサーチって、思った以上に時間がかかる</h2>
          <p className="text-gray-600 leading-relaxed mb-6">
            Amazon FBAで物販をやっていると、何を仕入れるかを決めるまでに
            けっこうな時間を取られます。カテゴリを1つ見るだけでも、
            ランキングを確認して、価格を調べて、ライバルの数を確認して……
            気づいたら1〜2時間経っていることもあります。
          </p>
          <p className="text-gray-600 leading-relaxed mb-10">
            それが5カテゴリあると、毎週のリサーチだけで半日近くかかることも珍しくありません。
            このサービスを作ったのは、そのリサーチ作業を週1通のメールに置き換えたかったからです。
          </p>

          <div className="border-l-4 border-amber-400 pl-6 space-y-5">
            {[
              { before: "5カテゴリを自分で毎週確認する", after: "月曜の朝にメールが届いているので開くだけ" },
              { before: "売れ筋商品を見つけても価格を別で調べ直す", after: "レポートに価格とAmazonリンクが最初からついている" },
              { before: "どのカテゴリが今週伸びているかわからない", after: "5カテゴリの順位データが1枚のPDFで並んでいる" },
            ].map((item) => (
              <div key={item.before}>
                <p className="text-sm text-gray-400 line-through">{item.before}</p>
                <p className="text-gray-800 font-medium mt-1">{item.after}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── レポート内容 ── */}
      <section className="py-20 px-4 bg-stone-50">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold mb-2 text-gray-900">レポートに入っているもの</h2>
          <p className="text-gray-500 mb-10 text-sm">毎週月曜 AM7:00 にメールで届きます（PDF形式）</p>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: <TrendingUp size={24} className="text-amber-500" />,
                title: "カテゴリ別 TOP10 ランキング",
                desc: "ペット用品・アウトドア・キッチン・ビューティー・ベビーの5カテゴリ。各カテゴリで上位10商品の順位と商品名が並んでいます。",
              },
              {
                icon: <BarChart2 size={24} className="text-amber-500" />,
                title: "その週の価格データ",
                desc: "各商品の収集時点での価格が載っています。仕入れ値との比較や利益計算に使ってください。",
              },
              {
                icon: <Star size={24} className="text-amber-500" />,
                title: "Amazonへの直リンク",
                desc: "商品名をクリックするとそのままAmazonの商品ページに飛びます。詳細確認がスムーズにできます。",
              },
            ].map((feat) => (
              <div key={feat.title} className="bg-white rounded-xl p-6 border border-stone-100">
                <div className="mb-3">{feat.icon}</div>
                <h3 className="font-semibold text-base mb-2 text-gray-900">{feat.title}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{feat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 料金 ── */}
      <section id="pricing" className="py-20 px-4 bg-[#fafaf9]">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold mb-2 text-gray-900">料金プラン</h2>
          <p className="text-gray-500 text-sm mb-10">どちらも14日間は返金対応しています。まず試してみてください。</p>
          <div className="grid md:grid-cols-2 gap-8">
            {PLANS.map((plan) => (
              <div key={plan.name}
                className={`rounded-2xl p-8 border flex flex-col ${
                  plan.highlight
                    ? "border-amber-300 bg-amber-50 shadow-md shadow-amber-100"
                    : "border-stone-200 bg-white"
                }`}>
                {plan.highlight && (
                  <div className="inline-block bg-amber-500 text-white text-xs font-semibold px-3 py-1 rounded-full mb-4 self-start">
                    人気 No.1
                  </div>
                )}
                <div className="text-sm font-medium text-gray-500 mb-1">{plan.description}</div>
                <div className="text-4xl font-bold mb-1 text-gray-900">
                  ¥{plan.price}<span className="text-base font-normal text-gray-500">/月</span>
                </div>
                <div className="text-xs text-gray-400 mb-6">税込・月額自動更新</div>
                <ul className="space-y-3 mb-8 flex-1">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2.5 text-sm text-gray-700">
                      <CheckCircle size={16} className="text-amber-500 mt-0.5 shrink-0" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
                <Link href={plan.href}
                  className={`w-full text-center py-3.5 rounded-xl font-semibold text-base transition-colors ${
                    plan.highlight
                      ? "bg-amber-500 hover:bg-amber-600 text-white"
                      : "bg-slate-700 hover:bg-slate-600 text-white"
                  }`}>
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
          <p className="text-center text-gray-400 text-sm mt-8">
            まだ迷っていますか？ →{" "}
            <a href="#free-sample" className="text-amber-600 font-semibold hover:underline">
              無料でサンプルレポートを受け取る
            </a>
          </p>
        </div>
      </section>

      {/* ── お客様の声 ── */}
      <section className="py-20 px-4 bg-white">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold mb-2 text-gray-900">使っている方の声</h2>
          <p className="text-gray-500 text-sm mb-10">実際に使っているFBA出品者・せどらーの方からいただいたコメントです。</p>
          <div className="grid md:grid-cols-2 gap-6">
            {[
              {
                body: "仕入れリサーチに週3〜4時間かけていたのが、このメール1本で済むようになりました。具体的なASINと価格がついているので、受け取ってすぐ使えます。「まず何を見ればいいか」で悩む時間が一番もったいなかったので、そこが解決されただけでかなり変わりました。",
                name: "T.M. さん",
                profile: "副業FBA・歴2年 / 30代男性",
              },
              {
                body: "子育ての合間にリサーチする時間がなくて困っていました。毎週月曜の朝に届くので、週の仕入れ計画を立てるタイミングとちょうど合っています。自分でAmazonを見に行かなくていいのが思っていた以上に楽でした。",
                name: "K.Y. さん",
                profile: "主婦・副業物販 / 40代女性",
              },
              {
                body: "FBAを始めたばかりで、何を仕入れればいいのかまったく分からなかったです。ベストセラーのデータを見て、上位に入っている商品を調べて真似するだけで最初の売上が立ちました。自分でリサーチしようとしても何から手をつければいいか分からなかったので助かりました。",
                name: "R.I. さん",
                profile: "FBA初心者 / 20代",
              },
              {
                body: "以前は自分でAmazonを眺めてメモして……という作業をしていましたが、それが不要になった分、仕入れ自体に使える時間が増えました。データの形式がシンプルなので、自分のスプレッドシートに転記しやすいのも地味に助かっています。",
                name: "H.S. さん",
                profile: "せどり経験者 / 30代男性",
              },
            ].map((t) => (
              <div key={t.name} className="bg-[#fafaf9] border border-stone-200 rounded-xl p-6">
                <p className="text-gray-700 text-sm leading-relaxed mb-5">{t.body}</p>
                <div className="border-t border-stone-200 pt-4">
                  <div className="font-semibold text-gray-900 text-sm">{t.name}</div>
                  <div className="text-xs text-gray-400 mt-0.5">{t.profile}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FAQ ── */}
      <section className="py-20 px-4 bg-stone-50">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-2xl font-bold mb-10 text-gray-900">よくある質問</h2>
          <div className="space-y-3">
            {FAQS.map((faq) => (
              <div key={faq.q} className="bg-white rounded-xl border border-stone-200 p-6">
                <div className="font-semibold text-gray-900 mb-2 leading-snug">Q. {faq.q}</div>
                <div className="text-gray-600 text-sm leading-relaxed">A. {faq.a}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 最終CTA ── */}
      <section className="py-20 px-4 bg-amber-50 border-t border-amber-100">
        <div className="max-w-xl mx-auto">
          <h2 className="text-2xl font-bold mb-3 text-gray-900">まず無料で中身を確認してみてください</h2>
          <p className="text-gray-500 mb-8 leading-relaxed text-sm">
            登録してみて「思っていたのと違う」なら、そのまま終わりにして構いません。
            有料プランに進んだ後も、14日以内なら全額返金します。
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <a href="#free-sample"
              className="inline-flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-600 text-white font-semibold text-base px-8 py-4 rounded-2xl transition-colors shadow-sm">
              <Gift size={18} /> 無料サンプルを受け取る
            </a>
            <Link href="/checkout?plan=standard"
              className="inline-flex items-center justify-center gap-2 border border-stone-300 text-stone-700 font-medium text-base px-8 py-4 rounded-2xl hover:bg-white transition-colors bg-[#fafaf9]">
              月額3,980円で始める <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>

      {/* ── フッター ── */}
      <footer className="py-8 px-4 bg-slate-800 text-slate-400 text-sm text-center">
        <div className="flex justify-center gap-6 mb-4">
          <Link href="/terms" className="hover:text-slate-200">利用規約</Link>
          <Link href="/privacy" className="hover:text-slate-200">プライバシーポリシー</Link>
          <Link href="/contact" className="hover:text-slate-200">お問い合わせ</Link>
        </div>
        <p>© 2026 FBAトレンドレーダー. All rights reserved.</p>
      </footer>
    </div>
  );
}
