import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "FBAトレンドレーダー｜Amazon売れ筋トレンドを毎週自動配信";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OgImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          background: "linear-gradient(135deg, #f97316 0%, #ea580c 50%, #c2410c 100%)",
          padding: "60px",
          fontFamily: "sans-serif",
        }}
      >
        {/* 暗いオーバーレイ */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: "rgba(0,0,0,0.35)",
            display: "flex",
          }}
        />

        {/* コンテンツ */}
        <div style={{ position: "relative", display: "flex", flexDirection: "column", height: "100%" }}>
          {/* バッジ */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              background: "rgba(255,255,255,0.2)",
              borderRadius: "999px",
              padding: "8px 24px",
              width: "fit-content",
              marginBottom: "32px",
            }}
          >
            <span style={{ color: "white", fontSize: "22px", fontWeight: "bold" }}>
              📦 毎週月曜日に自動配信
            </span>
          </div>

          {/* メインタイトル */}
          <div style={{ display: "flex", flexDirection: "column", flex: 1 }}>
            <div style={{ fontSize: "72px", fontWeight: "900", color: "white", lineHeight: 1.1, marginBottom: "16px" }}>
              FBAトレンドレーダー
            </div>
            <div style={{ fontSize: "40px", color: "#fed7aa", fontWeight: "700", marginBottom: "32px" }}>
              Amazon売れ筋を毎週データで先回り
            </div>
            <div style={{ fontSize: "28px", color: "#fff7ed", lineHeight: 1.6 }}>
              全5カテゴリ × TOP10 完全公開
            </div>
          </div>

          {/* 下部バー */}
          <div
            style={{
              display: "flex",
              gap: "40px",
              borderTop: "1px solid rgba(255,255,255,0.3)",
              paddingTop: "28px",
              marginTop: "auto",
            }}
          >
            {["✅ せどり・FBA仕入れに", "✅ 月額3,980円〜", "✅ 14日返金保証", "✅ いつでも解約OK"].map((item) => (
              <span key={item} style={{ color: "white", fontSize: "22px", fontWeight: "600" }}>
                {item}
              </span>
            ))}
          </div>
        </div>
      </div>
    ),
    { ...size }
  );
}
