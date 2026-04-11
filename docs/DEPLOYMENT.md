# Deployment

## Supabase
1. Create project
2. Run `supabase/schema.sql` in SQL editor
3. Capture `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`

## Raspberry Pi
1. Copy repo to Pi
2. Set environment variables:
   - Use `pi_server/.env.example` as a template and create `pi_server/.env`
   - Required:
     - `SENTINELPI_SUPABASE_URL`
     - `SENTINELPI_SUPABASE_ANON_KEY`
     - `SENTINELPI_SUPABASE_SERVICE_ROLE_KEY`
   - Optional:
     - `SENTINELPI_HOST=0.0.0.0`
     - `SENTINELPI_PORT=8000`
3. Run:
   - `bash scripts/install_pi.sh`
   - `bash pi_server/start.sh`

## Windows Agent
1. Use `windows_agent/.env.example` as a template and create `.env` in the repo root
2. Run ` .\.venv\Scripts\Activate.ps1'
3. Launch `python -m windows_agent.app.main`
4. Enroll using pairing code from mobile app

## Mobile App
1. Use `mobile_app/.env.example` as a template and create `mobile_app/.env`
2. Run `npm install` then `npm run start`
