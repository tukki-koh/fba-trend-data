import { NextRequest, NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase";

const RESEND_API_KEY = process.env.RESEND_API_KEY!;
const FROM_EMAIL     = process.env.FROM_EMAIL!;
const SITE_URL       = process.env.NEXT_PUBLIC_SITE_URL!;

export async function POST(req: NextRequest) {
  const { email } = await req.json();

  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return NextResponse.json({ error: "有効なメールアドレスを入力してください" }, { status: 400 });
  }

  // ① 既存会員チェック（有料会員は除外）
  const { data: existing } = await supabaseAdmin
    .from("members")
    .select("status")
    .eq("email", email)
    .single();

  if (existing && ["active", "trial"].includes(existing.status)) {
    return NextResponse.json(
      { error: "このメールアドレスは既に登録済みです。マイページからログインしてください。" },
      { status: 409 }
    );
  }

  // ② トライアル会員として登録
  const { error: upsertError } = await supabaseAdmin
    .from("members")
    .upsert(
      { email, plan: "trial", status: "trial" },
      { onConflict: "email" }
    );

  if (upsertError) {
    console.error("[free-sample] upsert error:", upsertError);
    return NextResponse.json({ error: "登録に失敗しました" }, { status: 500 });
  }

  // ③ 最新レポートを取得
  const { data: latestReport } = await supabaseAdmin
    .from("reports")
    .select("week_label, file_path")
    .order("published_at", { ascending: false })
    .limit(1)
    .single();

  // ④ ウェルカムメール送信
  const dashboardUrl = `${SITE_URL}/dashboard`;
  const upgradeUrl   = `${SITE_URL}/#pricing`;

  let html: string;

  if (latestReport) {
    // レポートあり → ダウンロードURLを案内
    const { data: signedUrl } = await supabaseAdmin.storage
      .from("reports")
      .createSignedUrl(latestReport.file_path, 60 * 60 * 24 * 7); // 7日間有効

    html = `
      <div style="font-family:sans-serif;max-width:600px;margin:auto;background:#f9fafb;padding:20px;border-radius:12px">
        <div style="background:#f97316;padding:20px 24px;border-radius:10px;margin-bottom:16px">
          <h1 style="color:white;margin:0;font-size:20px">📦 FBAトレンドレーダー</h1>
          <p style="color:#fff7ed;margin:6px 0 0;font-size:13px">無料サンプルレポートをお届けします！</p>
        </div>
        <div style="background:white;padding:24px;border-radius:10px">
          <p style="color:#374151;font-size:15px;line-height:1.7">
            この度はFBAトレンドレーダーにご登録いただき、ありがとうございます！<br>
            最新の週次レポート（${latestReport.week_label}）をご用意しました。
          </p>
          ${signedUrl?.signedUrl ? `
          <a href="${signedUrl.signedUrl}"
             style="display:inline-block;background:#f97316;color:white;padding:14px 32px;
                    border-radius:999px;text-decoration:none;font-weight:bold;font-size:15px;margin:16px 0">
            📄 レポートをダウンロード →
          </a>` : ""}
          <hr style="margin:24px 0;border:none;border-top:1px solid #e5e7eb">
          <p style="color:#374151;font-size:14px;line-height:1.7">
            レポートはいかがでしたか？<br>
            <strong>有料会員になると毎週月曜日に自動で届きます。</strong><br>
            今なら14日間返金保証付きで安心してお試しいただけます。
          </p>
          <a href="${upgradeUrl}"
             style="display:inline-block;background:#1f2937;color:white;padding:12px 28px;
                    border-radius:999px;text-decoration:none;font-weight:bold;font-size:14px;margin-top:8px">
            有料プランを見る（月額1,480円〜）→
          </a>
          <p style="font-size:11px;color:#9ca3af;margin-top:20px">
            配信停止は<a href="${dashboardUrl}" style="color:#f97316">こちら</a>からいつでも可能です。
          </p>
        </div>
      </div>`;
  } else {
    // レポートなし → 次回配信を案内
    html = `
      <div style="font-family:sans-serif;max-width:600px;margin:auto;background:#f9fafb;padding:20px;border-radius:12px">
        <div style="background:#f97316;padding:20px 24px;border-radius:10px;margin-bottom:16px">
          <h1 style="color:white;margin:0;font-size:20px">📦 FBAトレンドレーダー</h1>
          <p style="color:#fff7ed;margin:6px 0 0;font-size:13px">ご登録ありがとうございます！</p>
        </div>
        <div style="background:white;padding:24px;border-radius:10px">
          <p style="color:#374151;font-size:15px;line-height:1.7">
            FBAトレンドレーダーへのご登録ありがとうございます！<br>
            <strong>毎週月曜日の朝7時</strong>に最新のAmazon売れ筋トレンドレポートをお届けします。
          </p>
          <div style="background:#fff7ed;border-radius:8px;padding:16px;margin:16px 0">
            <p style="color:#92400e;font-size:14px;margin:0">
              📅 <strong>次回配信：来週月曜日 AM7:00</strong><br>
              全5カテゴリ × TOP10の売れ筋データをPDFでお届けします
            </p>
          </div>
          <a href="${upgradeUrl}"
             style="display:inline-block;background:#f97316;color:white;padding:14px 32px;
                    border-radius:999px;text-decoration:none;font-weight:bold;font-size:15px;margin-top:8px">
            有料プランで毎週届ける →
          </a>
        </div>
      </div>`;
  }

  const emailRes = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${RESEND_API_KEY}`,
      "Content-Type":  "application/json",
    },
    body: JSON.stringify({
      from:    FROM_EMAIL,
      to:      [email],
      subject: "【FBAトレンドレーダー】無料サンプルレポートをお届けします📦",
      html,
    }),
  });

  if (!emailRes.ok) {
    console.error("[free-sample] resend error:", await emailRes.text());
    return NextResponse.json({ error: "メール送信に失敗しました" }, { status: 500 });
  }

  return NextResponse.json({
    message: latestReport
      ? "最新レポートをメールに送信しました！ご確認ください。\n来週からも毎週月曜日にお届けします。"
      : "登録完了！来週月曜日AM7:00に最新レポートをお届けします。",
  });
}
