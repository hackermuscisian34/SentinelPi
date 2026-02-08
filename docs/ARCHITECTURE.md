# SentinelPi-EDR Architecture

## Components
- Windows Agent: background service + PySide6 tray client
- Raspberry Pi Edge Server: FastAPI + WebSocket control plane
- Supabase: Auth + Postgres + Realtime
- Mobile SOC: React Native app for pairing, alerts, response

## Data Flow
- Mobile app authenticates with Supabase and uses Pi for pairing + response
- Pi server validates Supabase JWT for user actions, issues pairing codes, enrolls devices
- Agents send telemetry and alerts to Pi server over HTTPS and WS
- Pi server writes device, alert, telemetry summaries to Supabase

## Trust Boundaries
- Pi is authoritative for local response
- Supabase is authoritative for identity and global visibility
- Agents never accept commands from cloud directly
