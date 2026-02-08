# Security Hardening Checklist

- Use HTTPS with valid certs for Pi server
- Restrict Pi server network exposure to SOC subnet/VPN
- Rotate Supabase service role key
- Store Pi server secrets only in environment variables
- Enable firewall on Pi and Windows
- Run agent and Pi server with least privilege
- Configure ClamAV updates and scheduled scans
- Enforce device re-enrollment on key rotation
- Set strict RLS policies and remove anon access
- Monitor logs and alerts for enrollment anomalies
