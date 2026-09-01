# Adobe Firefly 画像生成プロンプト集（LP集客率向上用）

作成場所: Adobe Firefly（テキストから画像）。AI感を消すコツ＝**「作り込みすぎない」**。
下記の共通ルールを毎回プロンプト末尾に必ず付ける。

## 共通ルール（全プロンプト共通・末尾に追加）
```
candid unposed smartphone photography, shot on iPhone, natural window light,
slightly imperfect asymmetric composition, realistic skin texture and pores,
visible fine grain, no studio lighting, no perfect symmetry, no glossy render,
warm amber and stone color grading, documentary style, not corporate stock photo
```
※「AIっぽさ」は"完璧すぎる構図・完璧すぎる肌・スタジオ照明"から生まれる。
　あえて生活感・非対称・自然光を強く指示することでリアリティが出る。

Firefly設定: コンテンツタイプ=**写真**／効果=**なし**（デフォルトの艶感を避ける）

---

## 1. ヒーロー補助写真（在宅リサーチ卒業カット）
**用途**: ヒーロー右側 or お客様の声セクション背景に使用。最優先。
**アスペクト比**: 4:5（縦長）
**保存名**: `hero-lifestyle.jpg`

```
A Japanese person in their 30s sitting at a small kitchen table in the morning,
relaxed genuine smile, holding a smartphone showing a blurred simple list on
screen (no readable text), a steaming cup of coffee next to a small stack of
plain brown cardboard shipping boxes slightly out of focus in the background,
soft morning sunlight through a window, shallow depth of field, cozy home
atmosphere, casual home clothes,
[共通ルールを追加]
```

---

## 2. お客様の声 ポートレート（4枚）
**用途**: 現在イニシャル丸アイコンの箇所を実写に差し替え（差し替え時にアイコンを大きくする）
**アスペクト比**: 1:1
**保存名**: `testimonial-1.jpg`〜`testimonial-4.jpg`

**① T.M. さん（副業FBA歴2年・30代男性）**
```
Japanese man in his early 30s, casual home cardigan, soft natural smile,
sitting near a window with warm afternoon light, neutral beige wall
background, close-up portrait from chest up,
[共通ルールを追加]
```

**② K.Y. さん（主婦・副業物販・40代女性）**
```
Japanese woman in her early 40s, warm gentle smile, casual home sweater,
soft kitchen background slightly blurred, natural daylight from the side,
close-up portrait from chest up,
[共通ルールを追加]
```

**③ R.I. さん（FBA初心者・20代）**
```
Japanese person in their mid 20s, casual hoodie, relaxed confident
half-smile, simple bright room background slightly blurred, natural
window light, close-up portrait from chest up,
[共通ルールを追加]
```

**④ H.S. さん（せどり経験者・30代男性）**
```
Japanese man in his mid 30s, casual shirt, calm confident expression,
home office background with soft blur, warm indoor lighting, close-up
portrait from chest up,
[共通ルールを追加]
```

---

## 3. OGP／SNSシェア画像用の背景写真
**用途**: `opengraph-image.tsx` の背景（現在グラデーションのみ→写真背景に）
**アスペクト比**: 横長（16:9に近いものを選び、後でPhotoshopで1200×630にトリミング）
**保存名**: `ogp-flatlay.jpg`

```
Top-down flat lay photo on a wooden desk, an open laptop showing a blurred
simple spreadsheet-like UI (no readable text or logos), a notebook with
handwritten notes, a small plain cardboard shipping box, a smartphone, a cup
of coffee, soft natural window light from one side, warm amber and stone
tones, generous empty negative space in the upper-left third of the frame,
[共通ルールを追加]
```

---

## 4. カテゴリ質感写真（5枚・レポート内カテゴリバッジ用）
**用途**: 現在のLucideアイコンを置き換え、カテゴリ選択の説得力を上げる
**アスペクト比**: 1:1
**保存名**: `cat-pet.jpg` / `cat-outdoor.jpg` / `cat-kitchen.jpg` / `cat-beauty.jpg` / `cat-baby.jpg`

**ペット用品**
```
Close-up flat lay of a simple dog leash and a rubber chew toy on a light
wooden floor, soft natural window light, warm tones,
[共通ルールを追加]
```

**アウトドア**
```
Close-up of a canvas backpack and a metal water bottle resting on a wooden
outdoor table, soft daylight, warm natural tones,
[共通ルールを追加]
```

**キッチン**
```
Close-up flat lay of a simple wooden kitchen utensil and a linen cloth on a
light kitchen counter, soft window light, warm neutral tones,
[共通ルールを追加]
```

**ビューティー**
```
Close-up of a simple unlabeled skincare bottle with soft natural shadow on
a light beige surface, gentle window light, warm tones,
[共通ルールを追加]
```

**ベビー**
```
Close-up flat lay of a soft knit baby blanket and a small wooden toy on a
light surface, gentle natural light, warm cozy tones,
[共通ルールを追加]
```

---

## 手配後の流れ（画像を渡してもらったら私がやること）
1. Photoshopツールで実サイズにクロップ・微調整（明るさ/色温度をブランドカラーに統一）
2. `public/images/` に配置し、Next.js `<Image>` コンポーネントへ差し替え
3. お客様の声セクションはアバターを大きく再デザイン（現状36pxは小さすぎるため拡大）
4. OGP画像をFireflyの写真ベースに刷新
5. 圧縮・WebP変換でページ速度を維持したままリアリティを追加
