-- Supabaseのダッシュボード > SQL Editor に貼り付けて実行してください

-- 会員テーブル
create table if not exists members (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  stripe_customer_id text unique,
  stripe_subscription_id text unique,
  plan text not null default 'standard',
  status text not null default 'active', -- active | canceled | past_due
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- レポートテーブル（毎週のレポートを管理）
create table if not exists reports (
  id uuid primary key default gen_random_uuid(),
  week_label text not null,       -- 例: "2026-W21"
  plan text not null default 'standard',
  file_path text not null,        -- Supabase Storage のパス
  published_at timestamptz default now()
);

-- Row Level Security（会員本人しか自分のデータを見られない）
alter table members enable row level security;
alter table reports enable row level security;

-- レポートはactiveな会員なら誰でも読める
create policy "active members can read reports"
  on reports for select
  using (true);

-- メンバーは自分のデータのみ
create policy "members read own data"
  on members for select
  using (auth.email() = email);

-- Supabase Storage: reportsバケットを作成（ダッシュボードのStorageタブから作成してください）
