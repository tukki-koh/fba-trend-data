# AI社員の役割分担（FBAトレンドレーダー）

最終更新: 2026-09-01

全社員が**クラウド（GitHub Actions）で稼働**します。PCやアプリを閉じていても動きます。
**1つのファイルには必ず1人だけ**が責任を持ちます（重複作業を作らないため）。

---

## 担当ファイル一覧（この表が正）

| 社員 | 稼働 | 担当ファイル（この社員だけが書き換える） | 実装 |
|---|---|---|---|
| 会員レポート配信担当 | 月 7:00 | Supabase(reports) ／ 会員へのメール | `collect_trends.py` |
| CRMドリップ担当 | 毎日 9:00 | Supabase(members) ／ 育成メール | `email_drip.py` |
| note編集者 | 火 21:00 | note.com の記事 | `collect_trends.py` |
| Instagram制作担当 | 火 21:00 | Instagram投稿（画像・キャプション） | `generate_instagram.py` |
| Facebook運用担当 | 日・水・金 | Facebookの投稿 | `post_facebook.py` |
| **SNSハッシュタグ担当** | 水 10:00 | `instagram_content/hashtags_current.md` | `cloud_marketing_agent.py` |
| **Google広告最適化担当** | 水 9:30（隔週） | `marketing/google_ads_assets.md` | `cloud_agents.py ads` |
| **成長・ベンチマーク担当** | 土 10:00 | `src/app/page.tsx` の **JSX本文のみ** | `cloud_agents.py growth` |
| **月次SEO/GEO担当** | 毎月5日 10:00 | `public/llms.txt` ＋ `src/app/layout.tsx` の **metadata** | `cloud_agents.py seo` |

---

## 過去に起きた重複と、その解消（再発防止のため記録）

### 1. `public/llms.txt` を2人が書いていた
- 週次マーケ社員（毎週水）と月次SEO/GEO担当（毎月5日）が同じファイルを毎回上書きしていた
- **解消**: SEO/GEOの専門領域なので**月次SEO/GEO担当に一本化**。
  週次側は「SNSハッシュタグ担当」に改名し、llms.txt から手を引いた

### 2. ハッシュタグを作っても誰も使っていなかった（完全な無駄）
- 週次社員が `hashtags_current.md` を毎週生成していたが、
  実際の投稿 `generate_instagram.py` は**ハードコードされたタグ**を使っていた
- **解消**: `generate_instagram.py` がこのファイルを読むように接続。
  ファイルが無い・壊れている場合は既定タグに自動で戻るため、投稿が止まることはない

### 3. 同じ社員がクラウドとアプリの両方に存在していた
- ads / growth / seo が、クラウド版と Claude常駐版の**二重で走る**状態だった
- **解消**: Claude常駐版（`~/.claude/scheduled-tasks/`）の4件をすべて**無効化**。
  クラウド版のみを正とする

### 4. `page.tsx` の metadata が2人の境界にあった
- `page.tsx` には JSX本文と `metadata`・`jsonLd` が同居しており、
  成長担当（page.tsx担当）とSEO担当（metadata担当）が衝突しうる状態だった
- **解消**: 成長担当のプロンプトで **metadata と jsonLd を触ることを明示的に禁止**

---

## 社員を追加・変更するときのルール

1. **担当ファイルが既存社員と重ならないこと**（上の表で必ず確認する）
2. 生成物は**必ず誰かが使う**こと（使われない生成はコストの無駄）
3. コードを触る社員は、`npm run build` の検証を必ず通すこと
   （失敗したら変更を破棄。本番は絶対に壊さない）
4. コミットの作者は `yuezuangcheng@gmail.com` にすること
   （別メールだとVercelが `TEAM_ACCESS_REQUIRED` でデプロイをブロックする）
5. この表を更新すること
