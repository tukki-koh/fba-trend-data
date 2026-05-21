import { NextRequest, NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase";

export async function GET(req: NextRequest) {
  const path = req.nextUrl.searchParams.get("path");
  if (!path) return NextResponse.json({ error: "パスが指定されていません" }, { status: 400 });

  // Supabase Storageから署名付きURLを発行（60秒間有効）
  const { data, error } = await supabaseAdmin.storage
    .from("reports")
    .createSignedUrl(path, 60);

  if (error || !data?.signedUrl) {
    return NextResponse.json({ error: "ダウンロードURLの生成に失敗しました" }, { status: 500 });
  }

  return NextResponse.redirect(data.signedUrl);
}
