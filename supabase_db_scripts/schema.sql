-- SentinelPi-EDR Supabase Schema

create table if not exists devices (
  device_id uuid primary key,
  device_hostname text not null,
  agent_version text not null,
  status text not null default 'offline',
  created_at timestamptz not null default now(),
  last_seen timestamptz
);

create table if not exists pairing_codes (
  id bigserial primary key,
  pairing_code text not null,
  device_name text not null,
  expires_at timestamptz not null,
  created_by uuid references auth.users(id),
  created_at timestamptz not null default now()
);

create table if not exists alerts (
  id bigserial primary key,
  device_id uuid references devices(device_id),
  timestamp timestamptz not null,
  severity text not null,
  title text not null,
  description text not null,
  metadata jsonb not null default '{}'
);

create table if not exists telemetry_summaries (
  id bigserial primary key,
  device_id uuid references devices(device_id),
  timestamp timestamptz not null,
  summary jsonb not null
);

create table if not exists audit_logs (
  id bigserial primary key,
  device_id uuid references devices(device_id),
  action text not null,
  actor uuid references auth.users(id),
  timestamp timestamptz not null
);

alter table devices enable row level security;
alter table pairing_codes enable row level security;
alter table alerts enable row level security;
alter table telemetry_summaries enable row level security;
alter table audit_logs enable row level security;

-- Policies: authenticated users can read devices, alerts, telemetry, and audit logs
create policy "devices_read" on devices
  for select using (auth.role() = 'authenticated');

create policy "pairing_insert" on pairing_codes
  for insert with check (auth.role() = 'authenticated');

create policy "pairing_read" on pairing_codes
  for select using (auth.role() = 'authenticated');

create policy "alerts_read" on alerts
  for select using (auth.role() = 'authenticated');

create policy "telemetry_read" on telemetry_summaries
  for select using (auth.role() = 'authenticated');

create policy "audit_read" on audit_logs
  for select using (auth.role() = 'authenticated');

-- Service role for inserts from Pi server
create policy "devices_insert_service" on devices
  for insert with check (auth.role() = 'service_role');

create policy "alerts_insert_service" on alerts
  for insert with check (auth.role() = 'service_role');

create policy "telemetry_insert_service" on telemetry_summaries
  for insert with check (auth.role() = 'service_role');

create policy "audit_insert_service" on audit_logs
  for insert with check (auth.role() = 'service_role');
