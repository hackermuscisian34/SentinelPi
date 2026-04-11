# SentinelPi EDR – Major Technical Challenges

This document outlines the most significant technical hurdles encountered during the development of SentinelPi EDR and how they were resolved.

### 1. Supabase RLS & Distributed Writing
The Windows Agent uses an "Anonymous" key for public telemetry, which was initially blocked by the default Row Level Security (RLS) policies. We resolved this by implementing specific Postgres policies that allow the `anon` role to insert into telemetry and path tables while keeping the rest of the database restricted to authenticated users.

### 2. Deep Dependency Version Conflict (WebSockets)
A critical conflict occurred where the `supabase` library required an older version of `websockets`, but the Agent's core logic relied on features from the newer `asyncio` submodule. We eventually stabilized the environment by pinning `websockets` to a precise intermediate version and upgrading the `supabase-py` client to resolve internal keyword argument errors.

### 3. Windows Store Python Shadowing
Package installations were frequently failing to be detected because the Windows Store version of Python was shadowing the local virtual environment on the target PC. This was fixed by bypassing the system PATH and explicitly invoking the target Python binary using `-m pip` to ensure dependencies were matched to the correct runtime.

### 4. Telemetry Integrity & Foreign Key Sync
Telemetry summaries often failed to upload because the Edge Server attempted to push data before the device was fully "recognized" in the cloud database. We implemented a local database buffer on the Pi to store telemetry temporarily and added a validation loop that verifies device existence before attempting a cloud sync.

### 5. AI Report Log Noise & Token Limits
Raw ClamAV and YARA logs were too verbose for the Gemini AI model, often exceeding token limits and causing report generation to fail. We developed a custom regex-based log filter on the Agent side that extracts only high-signal lines (e.g., "FOUND", "DETECTED") to provide the AI with concise, high-quality data.

### 6. Local Library Namespace Collision
The Agent's startup was blocked by a folder named `supabase` in the source directory which shadowed the actual installed library and prevented modules from loading. We resolved this by refactoring the local directory structure and renaming conflicting folders to ensure Python's import machinery correctly prioritized the external SDK.

### 7. Activity Monitor Alert Spam
Initial versions of the activity monitor sent a notification for every mouse movement, which overwhelmed the mobile app and the user. We implemented a time-based state machine that only triggers a "User Active" alert upon the first movement after a 5-minute idle threshold, preventing unnecessary alert fatigue.

---
*Generated for SentinelPi EDR – Engineering Troubleshooting Archive*
