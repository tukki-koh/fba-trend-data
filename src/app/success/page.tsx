import { CheckCircle } from "lucide-react";
import Link from "next/link";

export default function SuccessPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <CheckCircle size={72} className="text-green-500 mx-auto mb-6" />
        <h1 className="text-3xl font-extrabold mb-3">お申し込みありがとうございます！</h1>
        <p className="text-gray-600 mb-2">
          登録メールアドレスに確認メールをお送りしました。
        </p>
        <p className="text-gray-600 mb-8">
          最初のレポートは<strong>次の月曜日の朝7時</strong>に自動で届きます。
        </p>
        <Link
          href="/dashboard"
          className="inline-block bg-orange-500 hover:bg-orange-600 text-white font-bold px-8 py-3 rounded-full transition-colors"
        >
          マイページを見る
        </Link>
      </div>
    </div>
  );
}
