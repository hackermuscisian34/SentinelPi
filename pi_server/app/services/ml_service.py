
import os
import google.generativeai as genai  # type: ignore
from typing import Dict, Any, Optional
import json

class MLService:
    def __init__(self):
        self.api_key = os.getenv("SENTINELPI_GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            print("WARNING: SENTINELPI_GEMINI_API_KEY not found. ML features disabled.")
            self.model = None

    async def generate_report(self, alert: Dict[str, Any]) -> Optional[str]:
        if not self.model:
            return None

        try:
            # Construct prompt
            meta = alert.get("metadata", {})
            if isinstance(meta, str):
                try:
                   meta = json.loads(meta)
                except Exception:
                   pass
            
            clamav_out = meta.get("clamav", {}).get("output", "")
            yara_out = meta.get("yara", {}).get("output", "")
            description = alert.get("description", "")
            title = alert.get("title", "")

            # Pre-process output to reduce token usage and focus on threats
            def filter_log(log_text):
                if not log_text:
                    return ""
                lines = log_text.splitlines()
                # Keep lines that are not just "OK" or empty
                interesting = [line for line in lines if " OK" not in line and line.strip()]
                if not interesting:
                    return "No threats detected in the scanned files."
                return "\n".join(interesting[:50]) # Limit to 50 interesting lines to save tokens

            clamav_filtered = filter_log(clamav_out)
            yara_filtered = filter_log(yara_out)
            
            # If no threats found in filtered log, explicit message
            if "No threats detected" in clamav_filtered and "No threats detected" in yara_filtered:
                 prompt = f"""
                 You are Sentinel Pi, an advanced AI security analyst.
                 
                 **Scan Context:**
                 - Title: {title}
                 - Raw Description: {description}
                 
                 **Instructions:**
                 Generate a "SENTINEL PI – SECURITY SCAN REPORT" in HTML format.
                 The report MUST follow this EXACT structure and tone:

                 <div style="font-family: sans-serif; padding: 20px; color: #1f2937;">
                    <h2 style="color: #10b981; border-bottom: 2px solid #10b981; padding-bottom: 10px;">🛡️ SENTINEL PI – SECURITY SCAN REPORT</h2>
                    
                    <h3 style="margin-top: 20px;">1️⃣ Overall Result</h3>
                    <p><strong>Status:</strong> ✅ No threats found</p>
                    <p>The system scan did not detect any viruses, malware, or suspicious files. Your computer appears safe at the time of scanning.</p>

                    <h3 style="margin-top: 20px;">2️⃣ AI Security Insight</h3>
                    <p>Our security AI reviewed the scan behavior.</p>
                    <ul style="background: #ecfdf5; padding: 15px; border-left: 4px solid #10b981; list-style: none;">
                        <li><strong>Summary:</strong> No harmful files were detected.</li>
                        <li><strong>Analysis:</strong> Everything scanned is clean and safe.</li>
                        <li><strong>Advice:</strong> As a precaution, regular full system scans are still recommended.</li>
                    </ul>

                    <h3 style="margin-top: 20px;">3️⃣ Scan Information</h3>
                    <p>
                    <strong>Scan Date:</strong> (Insert Today's Date)<br>
                    <strong>Threat Level:</strong> 🟢 Low (Informational only)<br>
                    <strong>Engine:</strong> ClamAV Antivirus + YARA<br>
                    <strong>Scope:</strong> Checked system folders, downloads, and user files.
                    </p>

                    <h3 style="margin-top: 20px;">4️⃣ Important Findings</h3>
                    <p>✔ Clean Files (Summary of what was scanned based on logs)</p>
                    <ul>
                        <li>User account images</li>
                        <li>Desktop shortcuts</li>
                        <li>Documents and settings</li>
                    </ul>
                    <p>➡ All scanned files were reported as SAFE.</p>

                    <h3 style="margin-top: 20px;">5️⃣ Security Interpretation</h3>
                    <p><strong>What this means for you:</strong></p>
                    <ul>
                        <li>Your PC is not infected right now.</li>
                        <li>Installed apps and files look normal.</li>
                        <li>👉 <strong>System Health = GOOD</strong></li>
                    </ul>

                    <h3 style="margin-top: 20px;">6️⃣ Safety Recommendations</h3>
                    <ul>
                        <li>Run a full system scan once a week.</li>
                        <li>Keep Windows and antivirus updated.</li>
                        <li>Avoid downloading software from unknown websites.</li>
                    </ul>

                    <hr style="margin-top: 30px; border: 0; border-top: 1px solid #e5e7eb;">
                    <p style="text-align: center; color: #6b7280; font-size: 0.9em;">Generated by SentinelPi EDR • Automated Proactive Threat Defense</p>
                 </div>

                 **IMPORTANT:** 
                 - Return ONLY the HTML code.
                 - Fill in the "Scan Information" and "Important Findings" sections based on the actual logs provided below, but keep the tone exactly as above.
                 - Logs for context: {clamav_filtered}
                 """
            else:
                 prompt = f"""
                 You are Sentinel Pi, an advanced AI security analyst.
                 
                 **Scan Context:**
                 - Title: {title}
                 - Raw Description: {description}
                 - Antivirus Output: {clamav_filtered}
                 - YARA Output: {yara_filtered}
                 
                 **Instructions:**
                 Generate a "SENTINEL PI – SECURITY SCAN REPORT" in HTML format for a THREAT DETECTION event.
                 
                 Structure it similarly to the clean report but use RED accents and ALERT icons.
                 
                 <div style="font-family: sans-serif; padding: 20px; color: #1f2937;">
                    <h2 style="color: #ef4444; border-bottom: 2px solid #ef4444; padding-bottom: 10px;">🛡️ SENTINEL PI – SECURITY SCAN REPORT</h2>
                    
                    <h3 style="margin-top: 20px;">1️⃣ Overall Result</h3>
                    <p><strong>Status:</strong> 🚨 POTENTIAL THREAT DETECTED</p>
                    <p>The system scan detected suspicious files or patterns that require attention.</p>

                    <h3 style="margin-top: 20px;">2️⃣ AI Security Insight</h3>
                    <div style="background: #fef2f2; padding: 15px; border-left: 4px solid #ef4444;">
                        <p><strong>Analysis:</strong> The security agent detected a potential threat pattern.</p>
                        <p><strong>Recommendation:</strong> Quarantine the affected files immediately and run a full system scan.</p>
                    </div>

                    <h3 style="margin-top: 20px;">3️⃣ Threat Details</h3>
                    <p><strong>Threat Level:</strong> 🔴 HIGH</p>
                    <p><strong>Detected Items:</strong></p>
                    <pre style="background: #1f2937; color: #f87171; padding: 10px; border-radius: 5px; overflow-x: auto;">
                    (Insert specific files/threats found from logs here)
                    </pre>

                    <h3 style="margin-top: 20px;">4️⃣ Remediation Steps</h3>
                    <ol>
                        <li>Isolate the device from the network (if not already done).</li>
                        <li>Review the specific files listed above.</li>
                        <li>Delete or Quarantine the files using the "Quarantine" action.</li>
                    </ol>

                    <hr style="margin-top: 30px; border: 0; border-top: 1px solid #e5e7eb;">
                    <p style="text-align: center; color: #6b7280; font-size: 0.9em;">Generated by SentinelPi EDR</p>
                 </div>

                 **IMPORTANT:** 
                 - Return ONLY the HTML code. 
                 - EXTRACT the specific threats from the logs and list them in the "Threat Details" section.
                 """

            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            print(f"Error generating ML report: {e}")
            return None
