import { ImageResponse } from "next/og";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

export const alt = "FBAトレンドレーダー｜Amazon売れ筋トレンドを毎週自動配信";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function OgImage() {
  // 背景写真を data URI 化して埋め込む。
  // Satori(ImageResponse) は WebP を扱えないため、必ず JPEG を使うこと。
  const bg = await readFile(join(process.cwd(), "public/images/ogp-flatlay.jpg"));
  const bgSrc = `data:image/jpeg;base64,${bg.toString("base64")}`;

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          position: "relative",
          fontFamily: "sans-serif",
        }}
      >
        {/* 背景写真 */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={bgSrc}
          alt=""
          width={1200}
          height={630}
          style={{ position: "absolute", inset: 0, width: "1200px", height: "630px", objectFit: "cover" }}
        />

        {/* 可読性のための遮蔽。
            Satori の注意点: `inset` は効かないので top/left/width/height を明示する。
            勾配も `background` ショートハンドではなく backgroundImage を使う。 */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "1200px",
            height: "630px",
            display: "flex",
            backgroundColor: "rgba(18,16,14,0.62)",
          }}
        />
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "1200px",
            height: "630px",
            display: "flex",
            backgroundImage:
              "linear-gradient(90deg, rgba(16,14,12,0.92) 0%, rgba(16,14,12,0.78) 45%, rgba(16,14,12,0.10) 100%)",
          }}
        />

        {/* コンテンツ */}
        <div
          style={{
            position: "relative",
            display: "flex",
            flexDirection: "column",
            height: "100%",
            width: "100%",
            padding: "58px 64px",
          }}
        >
          {/* バッジ */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              background: "rgba(245,158,11,0.18)",
              border: "1px solid rgba(245,158,11,0.5)",
              borderRadius: "999px",
              padding: "9px 22px",
              // Satori は width:"fit-content" 非対応。alignSelf で内容幅に収める
              alignSelf: "flex-start",
              marginBottom: "28px",
            }}
          >
            <span style={{ color: "#fcd34d", fontSize: "21px", fontWeight: 700 }}>
              毎週月曜 AM7:00 に自動配信
            </span>
          </div>

          {/* メイン */}
          <div style={{ display: "flex", flexDirection: "column", flex: 1 }}>
            <div
              style={{
                fontSize: "62px",
                fontWeight: 900,
                color: "white",
                lineHeight: 1.15,
                letterSpacing: "-0.02em",
                marginBottom: "20px",
                display: "flex",
                flexDirection: "column",
              }}
            >
              <span>仕入れリサーチは、</span>
              <span>週1通のメールだけでいい。</span>
            </div>
            <div style={{ fontSize: "27px", color: "#e7e5e4", lineHeight: 1.55, display: "flex" }}>
              Amazon JPの売れ筋TOP10を5カテゴリ、価格・リンク付きでお届け
            </div>
          </div>

          {/* 下部バー */}
          <div
            style={{
              display: "flex",
              gap: "26px",
              alignItems: "center",
              borderTop: "1px solid rgba(255,255,255,0.22)",
              paddingTop: "22px",
            }}
          >
            <span style={{ color: "#fcd34d", fontSize: "24px", fontWeight: 800 }}>
              FBAトレンドレーダー
            </span>
            {["月額1,480円〜", "14日間返金保証", "カード登録不要"].map((item) => (
              <span key={item} style={{ color: "#e7e5e4", fontSize: "19px", fontWeight: 600 }}>
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
