import sys
import requests
import asyncio
import os

# Add current dir to path so we can import app
sys.path.append(os.getcwd())

from app.agent import AgentClient
from app.config import config

PI_URL = f"http://{config.PI_SERVER_IP}:{config.PI_SERVER_PORT}"

def get_code():
    print(f"Requesting pairing code from {PI_URL}...")
    # Send dummy device name
    resp = requests.post(f"{PI_URL}/pairing", json={"device_name": "ManualEnroll"})
    resp.raise_for_status()
    code = resp.json()["pairing_code"]
    print(f"Got code: {code}")
    return code

def enroll():
    agent = AgentClient()
    if agent.enrolled():
        print("Agent already enrolled!")
        # We want to re-enroll just in case keys are bad, but let's try just enrolling normally first.
        # If it says enrolled, we assume it's good. 
        # But if user says it's not working, maybe keys are bad?
        # Let's force re-enrollment if script is run?
        # No, let's trust enrolled() check first.
        return

    try:
        code = get_code()
        print(f"Enrolling with code {code}...")
        # def enroll(self, pi_ip: str, pairing_code: str) -> dict:
        res = agent.enroll(config.PI_SERVER_IP, code)
        print("Enrollment successful:", res)
    except Exception as e:
        print("Enrollment failed:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    enroll()
