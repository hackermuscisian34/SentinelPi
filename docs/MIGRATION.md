# Self-Host Migration Plan

1. Replace Supabase with self-hosted Postgres + Auth server
2. Update Pi server to use internal auth JWT verification
3. Replace Supabase Realtime with Postgres logical replication or NATS
4. Swap mobile app REST targets to self-host API
5. Migrate data with pg_dump/pg_restore
6. Rotate keys and re-enroll devices
