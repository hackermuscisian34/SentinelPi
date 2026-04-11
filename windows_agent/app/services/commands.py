import logging
import subprocess
from typing import Dict, Any
import os

logger = logging.getLogger("agent.commands")


class CommandExecutor:
    def execute(self, command: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if command == "kill_process":
                pid = str(args.get("pid"))
                subprocess.check_output(["taskkill", "/PID", pid, "/F"], text=True)
                return {"status": "ok"}
            if command == "isolate_network":
                self._set_network_state(False)
                return {"status": "ok"}
            if command == "restore_network":
                self._set_network_state(True)
                return {"status": "ok"}
            if command == "trigger_scan":
                scan_paths = []
                direct_path = args.get("path")
                target = args.get("target")

                def filter_output(text):
                    """Keep important ClamAV/YARA lines — threats AND clean summary lines."""
                    if not text:
                        return ""
                    interesting = []
                    for line in text.splitlines():
                        if any(kw in line for kw in (
                            "FOUND", "DETECTED", "ERROR", "Scanned",
                            "Infected", "Data scanned", "Time", ": OK",
                            "matched", "rules",
                        )):
                            interesting.append(line)
                    return "\n".join(interesting[:100])

                # 1. Determine Paths
                if direct_path:
                    if os.path.exists(direct_path):
                        scan_paths.append(direct_path)
                    else:
                        return {"status": "error", "message": f"Path not found: {direct_path}"}

                elif target:
                    if target == "full_pc":
                        import string
                        from ctypes import windll
                        bitmask = windll.kernel32.GetLogicalDrives()
                        for letter in string.ascii_uppercase:
                            if bitmask & 1:
                                scan_paths.append(f"{letter}:\\")
                            bitmask >>= 1

                    elif target == "user_profile" or target == "downloads":
                        users_dir = "C:\\Users"
                        if os.path.exists(users_dir):
                            for item in os.listdir(users_dir):
                                full_path = os.path.join(users_dir, item)
                                if os.path.isdir(full_path) and item not in ["Public", "Default", "Default User", "All Users", "desktop.ini"]:
                                    if target == "downloads":
                                        dl_path = os.path.join(full_path, "Downloads")
                                        if os.path.exists(dl_path):
                                            scan_paths.append(dl_path)
                                    else:
                                        scan_paths.append(full_path)
                        if not scan_paths:
                            current_user = os.path.expanduser("~")
                            if target == "downloads":
                                scan_paths.append(os.path.join(current_user, "Downloads"))
                            else:
                                scan_paths.append(current_user)

                if not scan_paths:
                    return {"status": "error", "message": "No valid paths found to scan"}

                # 2. Execute Scans
                clamav_parts = []
                yara_parts = []

                for path in scan_paths:
                    logger.info(f"Scanning: {path}")
                    # Run ClamAV
                    cr = self._run_clamav(path, remove=False)
                    c_raw = cr.get("output") or cr.get("message", "")
                    c_out = filter_output(c_raw)
                    # Always include something so clean scans still generate an alert
                    clamav_parts.append(f"--- {path} ---\n{c_out or c_raw[:500] or '(no output)'}")

                    # Run YARA
                    yr = self._run_yara(path)
                    y_raw = yr.get("output") or yr.get("message", "")
                    y_out = filter_output(y_raw)
                    if y_out:
                        yara_parts.append(f"--- {path} ---\n{y_out}")

                clamav_combined = "\n".join(clamav_parts)
                yara_combined   = "\n".join(yara_parts)

                return {
                    "status": "ok",
                    "clamav": {"output": clamav_combined},
                    "yara":   {"output": yara_combined},
                }

            if command == "quarantine":
                path = args.get("path", "C:\\")
                return self._run_clamav(path, remove=True)

            if command == "discover_paths":
                import string
                from ctypes import windll
                
                paths = []
                
                # 1. Get Drives
                bitmask = windll.kernel32.GetLogicalDrives()
                for letter in string.ascii_uppercase:
                    if bitmask & 1:
                        drive = f"{letter}:\\"
                        paths.append({"path": drive, "label": f"Drive {letter}", "is_directory": True})
                    bitmask >>= 1
                
                # 2. Get User Profiles
                users_dir = "C:\\Users"
                if os.path.exists(users_dir):
                    for item in os.listdir(users_dir):
                        full_path = os.path.join(users_dir, item)
                        # Filter out system/hidden/default folders
                        if os.path.isdir(full_path) and not item.startswith(".") and item not in ["Public", "Default", "Default User", "All Users", "desktop.ini"]:
                             paths.append({"path": full_path, "label": f"User: {item}", "is_directory": True})
                             
                             # Add Downloads optionally
                             dl = os.path.join(full_path, "Downloads")
                             if os.path.exists(dl):
                                 paths.append({"path": dl, "label": f"Downloads ({item})", "is_directory": True})

                return {"status": "ok", "paths": paths}

            if command == "list_networks":
                return self._list_networks()

            if command == "list_wifi":
                return self._list_wifi_ssids()

            if command == "block_network":
                adapter_name = args.get("name", "")
                if not adapter_name:
                    return {"status": "error", "message": "No adapter name provided"}
                return self._set_adapter_state(adapter_name, enable=False)

            if command == "unblock_network":
                adapter_name = args.get("name", "")
                if not adapter_name:
                    return {"status": "error", "message": "No adapter name provided"}
                return self._set_adapter_state(adapter_name, enable=True)

            return {"status": "error", "message": "Unknown command"}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def _set_network_state(self, enable: bool) -> Dict[str, Any]:
        try:
            if not enable:
                cmd = "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | ForEach-Object {Disable-NetAdapter -Name $_.Name -Confirm:$false}"
            else:
                cmd = "Get-NetAdapter | Where-Object {$_.Status -eq 'Disabled'} | ForEach-Object {Enable-NetAdapter -Name $_.Name -Confirm:$false}"
            subprocess.check_output(["powershell", "-Command", cmd], text=True, timeout=20)
            state = "enabled" if enable else "disabled"
            return {"status": "ok", "message": f"All adapters {state}."}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": f"PowerShell error: {e.output}"}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}


    def _list_networks(self) -> Dict[str, Any]:
        """Return all network adapters with name, status, and interface type."""
        import json
        try:
            ps_cmd = (
                "Get-NetAdapter | Select-Object Name, Status, InterfaceDescription, InterfaceType | ConvertTo-Json"
            )
            out = subprocess.check_output(
                ["powershell", "-Command", ps_cmd],
                text=True, timeout=10
            ).strip()
            if not out:
                return {"status": "ok", "adapters": []}
            data = json.loads(out)
            if isinstance(data, dict):
                data = [data]
            adapters = [
                {
                    "name": a.get("Name", ""),
                    "status": a.get("Status", "Unknown"),
                    "description": a.get("InterfaceDescription", ""),
                    "type": str(a.get("InterfaceType", "")),
                }
                for a in data
            ]
            return {"status": "ok", "adapters": adapters}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def _list_wifi_ssids(self) -> Dict[str, Any]:
        """Return all visible WiFi networks via netsh wlan show networks."""
        try:
            out = subprocess.check_output(
                ["netsh", "wlan", "show", "networks", "mode=bssid"],
                text=True, timeout=10,
                stderr=subprocess.STDOUT
            )
            networks = []
            current: Dict[str, Any] = {}
            for line in out.splitlines():
                line = line.strip()
                if line.startswith("SSID") and "BSSID" not in line:
                    # "SSID 1 : MyNetwork"
                    if current.get("ssid"):
                        networks.append(current)
                    parts = line.split(":", 1)
                    current = {"ssid": parts[1].strip() if len(parts) > 1 else "", "signal": "", "auth": ""}
                elif line.startswith("Signal"):
                    parts = line.split(":", 1)
                    current["signal"] = parts[1].strip() if len(parts) > 1 else ""
                elif line.startswith("Authentication"):
                    parts = line.split(":", 1)
                    current["auth"] = parts[1].strip() if len(parts) > 1 else ""
            if current.get("ssid"):
                networks.append(current)
            # Deduplicate by SSID
            seen = set()
            unique = []
            for n in networks:
                if n["ssid"] and n["ssid"] not in seen:
                    seen.add(n["ssid"])
                    unique.append(n)
            return {"status": "ok", "networks": unique}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def _set_adapter_state(self, name: str, enable: bool) -> Dict[str, Any]:
        """Enable or disable a specific network adapter by name."""
        try:
            action = "Enable-NetAdapter" if enable else "Disable-NetAdapter"
            ps_cmd = f'{action} -Name "{name}" -Confirm:$false'
            subprocess.check_output(
                ["powershell", "-Command", ps_cmd],
                text=True, timeout=15
            )
            state = "enabled" if enable else "disabled"
            return {"status": "ok", "message": f"Adapter '{name}' {state}."}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": f"PowerShell error: {e.output}"}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}



    def _run_clamav(self, path: str, remove: bool = False) -> Dict[str, Any]:
        try:
            clamscan = os.getenv("CLAMAV_PATH", "clamscan.exe")

            # Support both absolute paths and PATH-based lookups
            import shutil
            if os.path.isabs(clamscan):
                if not os.path.isfile(clamscan):
                    return {"status": "error", "message": f"ClamAV not found at: {clamscan}"}
            elif not shutil.which(clamscan):
                return {"status": "error", "message": f"ClamAV '{clamscan}' not found in PATH"}

            args = [clamscan, "-r", path]
            if remove:
                args.append("--remove")

            try:
                output = subprocess.check_output(args, text=True, stderr=subprocess.STDOUT)
                return {"status": "ok", "output": output}
            except subprocess.CalledProcessError as e:
                # ClamAV exit codes:
                #   0 = no virus found
                #   1 = virus(es) FOUND — valid output, not a failure
                #   2 = error (DB issue, bad file, etc.)
                if e.returncode == 1:
                    return {"status": "ok", "output": e.output}
                else:
                    return {"status": "scan_error", "output": e.output or "",
                            "message": f"ClamAV exited with code {e.returncode}"}
        except FileNotFoundError:
            return {"status": "error", "message": "ClamAV executable not found"}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}


    def _run_yara(self, path: str) -> Dict[str, Any]:
        try:
             # Try to find yara binary
            yara_bin = os.getenv("YARA_PATH", "yara64.exe")
            rule_path = os.getenv("YARA_RULES", "rules.yar")
            
            # Check if rules exist, if not create a dummy one for testing
            if not os.path.exists(rule_path):
                return {"status": "skipped", "message": "YARA rules file not found"}

            cmd = [yara_bin, "-r", rule_path, path]
            # stderr=subprocess.STDOUT to capture errors in output
            output = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
            return {"status": "ok", "output": output}
        except FileNotFoundError:
             return {"status": "error", "message": "YARA executable not found"}
        except subprocess.CalledProcessError as e:
            # YARA returns 1 if matches found (sometimes) or errors
            return {"status": "completed", "output": e.output, "exit_code": e.returncode}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

