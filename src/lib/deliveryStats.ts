import { supabaseAdmin } from "@/lib/supabase";

export type DeliveryStats = {
  /** 実際に配信された週次レポートの本数（同一週の重複行は1件に集約） */
  totalReports: number;
  /** 直近の配信から遡って、抜けなく続いている連続配信週数 */
  consecutiveWeeks: number;
  /** 最初の配信日（JST表示用にフォーマット済み） */
  firstDeliveryLabel: string;
};

// フォールバック値。Supabase接続に失敗した場合のみ使用する（本番では実データを表示する）
const FALLBACK_STATS: DeliveryStats = {
  totalReports: 0,
  consecutiveWeeks: 0,
  firstDeliveryLabel: "",
};

function parseWeekLabel(label: string): { year: number; week: number } | null {
  const m = /^(\d{4})-W(\d{1,2})$/.exec(label);
  if (!m) return null;
  return { year: Number(m[1]), week: Number(m[2]) };
}

// b が a の「次のISO週」であればtrue（年またぎも考慮）
function isNextIsoWeek(a: { year: number; week: number }, b: { year: number; week: number }): boolean {
  if (a.year === b.year && b.week === a.week + 1) return true;
  if (b.year === a.year + 1 && b.week === 1 && a.week >= 52) return true;
  return false;
}

/**
 * reportsテーブルから実際の配信本数・連続配信週数を集計する。
 * 同じweek_labelが複数行あっても（再送・開発時のテスト挿入など）1本として数える。
 */
export async function getDeliveryStats(): Promise<DeliveryStats> {
  try {
    const { data, error } = await supabaseAdmin
      .from("reports")
      .select("week_label, published_at")
      .order("published_at", { ascending: true });

    if (error || !data || data.length === 0) {
      if (error) console.error("[deliveryStats] fetch error:", error);
      return FALLBACK_STATS;
    }

    // week_label ごとに最も早いpublished_atを採用
    const earliestByWeek = new Map<string, string>();
    for (const row of data) {
      const prev = earliestByWeek.get(row.week_label);
      if (!prev || row.published_at < prev) {
        earliestByWeek.set(row.week_label, row.published_at);
      }
    }

    const weeks = Array.from(earliestByWeek.keys())
      .map((label) => ({ label, parsed: parseWeekLabel(label) }))
      .filter((w): w is { label: string; parsed: { year: number; week: number } } => w.parsed !== null)
      .sort((a, b) => a.parsed.year - b.parsed.year || a.parsed.week - b.parsed.week);

    const totalReports = weeks.length;

    let consecutiveWeeks = totalReports > 0 ? 1 : 0;
    for (let i = weeks.length - 1; i > 0; i--) {
      if (isNextIsoWeek(weeks[i - 1].parsed, weeks[i].parsed)) {
        consecutiveWeeks++;
      } else {
        break;
      }
    }

    const firstPublishedAt = data[0].published_at;
    const firstDeliveryLabel = new Date(firstPublishedAt).toLocaleDateString("ja-JP", {
      year: "numeric",
      month: "long",
      day: "numeric",
      timeZone: "Asia/Tokyo",
    });

    return { totalReports, consecutiveWeeks, firstDeliveryLabel };
  } catch (e) {
    console.error("[deliveryStats] unexpected error:", e);
    return FALLBACK_STATS;
  }
}
