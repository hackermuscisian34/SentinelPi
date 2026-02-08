#!/usr/bin/env bash
set -euo pipefail
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip clamav
python3 -m venv .venv
source .venv/bin/activate
pip install -r pi_server/requirements.txt
