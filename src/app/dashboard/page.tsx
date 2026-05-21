import { supabaseAdmin } from "@/lib/supabase";
import { FileText, Download, LogOut } from "lucide-react";

async function getReports() {
  const { data } = await supabaseAdmin
    .from("reports")
    .select("*")
    .order("published_at", { ascending: false })
    .limit(12);
  return data ?? [];
}

export default async function DashboardPage() {
  const reports = await getReports();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="bg-white border-b border-gray-200 px-4 h-14 flex items-center justify-between">
        <span className="font-bold text-orange-500">FBAトレンドレーダー</span>
        <a href="/api/auth/signout" className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-900">
          <LogOut size={14} /> ログアウト
        </a>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-10">
        <h1 className="text-2xl font-extrabold mb-2">マイページ</h1>
        <p className="text-gray-500 text-sm mb-8">レポートは毎週月曜日の朝7時に更新されます</p>

        {reports.length === 0 ? (
          <div className="bg-white rounded-2xl border border-gray-200 p-12 text-center text-gray-400">
            <FileText size={48} className="mx-auto mb-4 opacity-30" />
            <p>まだレポートがありません。<br />次の月曜日にお届けします。</p>
          </div>
        ) : (
          <div className="space-y-4">
            {reports.map((report: { id: string; week_label: string; plan: string; file_path: string; published_at: string }) => (
              <div
                key={report.id}
                className="bg-white rounded-2xl border border-gray-200 p-5 flex items-center justify-between"
              >
                <div className="flex items-center gap-4">
                  <div className="bg-orange-100 rounded-xl p-3">
                    <FileText size={22} className="text-orange-500" />
                  </div>
                  <div>
                    <div className="font-bold">{report.week_label} トレンドレポート</div>
                    <div className="text-sm text-gray-400">
                      {new Date(report.published_at).toLocaleDateString("ja-JP")} 配信 ／{" "}
                      <span className="capitalize">{report.plan}</span>
                    </div>
                  </div>
                </div>
                <a
                  href={`/api/report-download?path=${encodeURIComponent(report.file_path)}`}
                  className="flex items-center gap-2 bg-orange-500 hover:bg-orange-600 text-white text-sm font-semibold px-4 py-2 rounded-full transition-colors"
                >
                  <Download size={14} /> ダウンロード
                </a>
              </div>
            ))}
          </div>
        )}

        {/* プラン管理 */}
        <div className="mt-10 bg-white rounded-2xl border border-gray-200 p-6">
          <h2 className="font-bold mb-1">プラン管理</h2>
          <p className="text-sm text-gray-500 mb-4">Stripeのカスタマーポータルでプランの変更・解約ができます</p>
          <a
            href="/api/billing-portal"
            className="inline-flex items-center gap-2 border border-gray-300 hover:border-orange-400 text-sm font-semibold px-5 py-2.5 rounded-full transition-colors"
          >
            プランの変更・解約
          </a>
        </div>
      </main>
    </div>
  );
}
