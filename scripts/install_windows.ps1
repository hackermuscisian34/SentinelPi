$ErrorActionPreference = "Stop"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r windows_agent\requirements.txt
