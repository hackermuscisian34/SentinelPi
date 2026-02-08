# End-to-End Testing

1. Supabase
   - Create a user
   - Verify RLS allows authenticated read access to `devices`, `alerts`

2. Pi Server
   - `curl http://<pi_ip>:8000/health` returns `ok`
   - `POST /pairing` with valid bearer token returns pairing code

3. Windows Agent
   - Enroll with pairing code
   - Verify device row in Supabase
   - Confirm telemetry summaries populate

4. Mobile App
   - Login
   - See device list
   - Generate pairing code
   - Receive realtime alert updates

5. Response Commands
   - Execute `trigger_scan`
   - Execute `isolate_network` and `restore_network`
   - Verify audit log entry in Supabase
