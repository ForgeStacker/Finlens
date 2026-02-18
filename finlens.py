#!/usr/bin/env python3
"""
FinLens Main Entry Point
Supports both local and Docker execution modes
"""

import sys
import os
import subprocess
import time
import webbrowser
import signal
import threading
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.config_loader import load_config
from backend.runner import run_scan
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Version information
VERSION = "1.0.0"
PRODUCT_NAME = "FinLens"

# Global process tracking
running_processes = []
api_server_process = None
frontend_process = None

def _display_banner():
    """Display FinLens banner"""
    banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ███████╗██╗███╗   ██╗██╗     ███████╗███╗   ██╗███████╗   ║
║   ██╔════╝██║████╗  ██║██║     ██╔════╝████╗  ██║██╔════╝   ║
║   █████╗  ██║██╔██╗ ██║██║     █████╗  ██╔██╗ ██║███████╗   ║
║   ██╔══╝  ██║██║╚██╗██║██║     ██╔══╝  ██║╚██╗██║╚════██║   ║
║   ██║     ██║██║ ╚████║███████╗███████╗██║ ╚████║███████║   ║
║   ╚═╝     ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝╚═╝  ╚═══╝╚══════╝   ║
║                                                              ║
║                  Cloud Infrastructure Scanner               ║
║                        Version {VERSION}                         ║
╚══════════════════════════════════════════════════════════════╝

🚀 Starting {PRODUCT_NAME} - One Command, Full Experience!
    """
    print(banner)

def cleanup_processes():
    """Clean up all spawned processes"""
    global running_processes, api_server_process, frontend_process
    
    logger.info("🧹 Cleaning up processes...")
    
    # Terminate frontend process
    if frontend_process and frontend_process.poll() is None:
        try:
            frontend_process.terminate()
            frontend_process.wait(timeout=5)
            logger.info("✅ Frontend server stopped")
        except subprocess.TimeoutExpired:
            frontend_process.kill()
            logger.info("🔥 Frontend server force-killed")
    
    # Terminate API server process
    if api_server_process and api_server_process.poll() is None:
        try:
            api_server_process.terminate()
            api_server_process.wait(timeout=5)
            logger.info("✅ API server stopped")
        except subprocess.TimeoutExpired:
            api_server_process.kill()
            logger.info("🔥 API server force-killed")
    
    # Clean up any other processes
    for process in running_processes:
        if process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=3)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                try:
                    process.kill()
                except ProcessLookupError:
                    pass

def signal_handler(signum, frame):
    """Handle Ctrl+C and other signals"""
    print("\n\n💫 Shutting down FinLens gracefully...")
    cleanup_processes()
    print("👋 FinLens stopped. Thanks for using it!")
    sys.exit(0)

def check_server_health(url, timeout=60, service_name="Server"):
    """Check if a server is responding with progress updates"""
    import requests
    
    logger.info(f"⏳ Waiting for {service_name} to be ready...")
    start_time = time.time()
    attempt = 0
    
    while time.time() - start_time < timeout:
        attempt += 1
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                elapsed = time.time() - start_time
                logger.info(f"✅ {service_name} is ready! (took {elapsed:.1f}s)")
                return True
        except requests.RequestException:
            pass
        
        # Show progress every 5 seconds
        if attempt % 5 == 0:
            elapsed = time.time() - start_time
            logger.info(f"⏳ Still waiting for {service_name}... ({elapsed:.0f}s elapsed)")
        
        time.sleep(1)
    
    logger.error(f"❌ {service_name} failed to start within {timeout}s")
    return False

def start_api_server():
    """Start the API server in background"""
    global api_server_process
    
    logger.info("🚀 Starting API server on port 8083...")
    api_server_process = subprocess.Popen(
        [sys.executable, "api_server.py"],
        cwd=project_root / "frontend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    running_processes.append(api_server_process)
    return api_server_process

def start_frontend_server():
    """Start the frontend development server"""
    global frontend_process
    
    logger.info("🎨 Starting frontend server on port 5173...")
    
    # Check if npm is installed
    try:
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("❌ npm not found. Please install Node.js and npm first.")
        return None
    
    # Install dependencies if needed
    frontend_dir = project_root / "frontend"
    if not (frontend_dir / "node_modules").exists():
        logger.info("📦 Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
    
    # Start dev server
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    running_processes.append(frontend_process)
    return frontend_process

def open_browser():
    """Open the browser to the frontend URL with better timing"""
    url = "http://localhost:5173"
    logger.info(f"🌐 Opening browser at {url}")
    
    # Add a small delay to ensure frontend is fully loaded
    time.sleep(3)
    
    try:
        import platform
        system = platform.system().lower()
        
        if system == "darwin":  # macOS
            subprocess.run(["open", url], check=False)
        elif system == "linux":
            subprocess.run(["xdg-open", url], check=False)
        elif system == "windows":
            subprocess.run(["start", url], shell=True, check=False)
        else:
            # Fallback to webbrowser
            webbrowser.open(url)
            
        logger.info(f"✅ Browser opened successfully")
    except Exception as e:
        logger.warning(f"⚠️ Could not open browser automatically: {e}")
        logger.info(f"📌 Please open your browser manually and go to: {url}")

def docker_mode():
    """Run in Docker mode - sequential processing with visible progress"""
    logger.info("🐳 Running in Docker mode")
    
    # Load configuration
    try:
        config = load_config()
        logger.info("✅ Configuration loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load configuration: {e}")
        return False
    
    # Run data collection first with visible progress
    logger.info("🔍 Starting AWS data collection...")
    logger.info("📊 This may take 2-5 minutes depending on your AWS resources")
    logger.info("⏳ Please wait while we scan your infrastructure...")
    
    try:
        start_time = time.time()
        
        # Enhanced logging for visibility
        logger.info("🌐 Initializing AWS SDK and loading profiles...")
        run_scan(config)
        
        elapsed_time = time.time() - start_time
        logger.info("="*60)
        logger.info(f"✅ SUCCESS: Data collection completed in {elapsed_time:.1f} seconds!")
        logger.info("📈 All AWS resources have been scanned and indexed")
        logger.info("="*60)
    except Exception as e:
        logger.error(f"❌ Data collection failed: {e}")
        return False
    
    # Start API server and keep running
    logger.info("🚀 Starting API server on port 8083...")
    logger.info("🌐 Frontend will be available at http://localhost:5173")
    
    try:
        # Direct API server startup - no complex imports
        logger.info("📡 Starting API server directly...")
        
        api_server_path = '/app/api_server.py'  # Direct Docker path
        if not os.path.exists(api_server_path):
            api_server_path = os.path.join(os.path.dirname(__file__), 'api_server.py')
        
        if not os.path.exists(api_server_path):
            # Copy from frontend directory 
            import shutil
            frontend_api = os.path.join(os.path.dirname(__file__), 'frontend', 'api_server.py')
            if os.path.exists(frontend_api):
                shutil.copy2(frontend_api, '/app/api_server.py')
                api_server_path = '/app/api_server.py'
        
        logger.info(f"🔄 Running API server from: {api_server_path}")
        
        # Run API server as subprocess to handle errors gracefully
        import subprocess
        process = subprocess.Popen(
            [sys.executable, api_server_path], 
            cwd='/app',
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        logger.info("📡 API server process started, monitoring...")
        
        # Monitor the process and log output
        while True:
            line = process.stdout.readline()
            if line:
                logger.info(f"API: {line.strip()}")
            if process.poll() is not None:
                break
            
    except Exception as e:
        logger.error(f"❌ API server failed: {e}")
        logger.info("🔄 Trying simple fallback...")
        
        # Ultimate fallback - just keep the container alive
        try:
            logger.info("⏳ Keeping container alive for debugging...")
            while True:
                time.sleep(10)
                logger.info("💓 Container heartbeat")
        except KeyboardInterrupt:
            logger.info("🛑 Shutdown requested")
            
        return False

def local_mode():
    """Run in local mode - full orchestration"""
    logger.info("🖥️  Running in local mode")
    
    try:
        # Load configuration
        config = load_config()
        logger.info("✅ Configuration loaded successfully")
        
        # Phase 1: Data Collection
        logger.info("🔍 Starting AWS data collection...")
        run_scan(config)
        logger.info("✅ Data collection complete")
        
        # Phase 2: Start API Server
        logger.info("🚀 Starting API server...")
        start_api_server()
        if not check_server_health("http://localhost:8083/api/discovery", 60, "API Server"):
            logger.error("❌ API server failed to start")
            return False
        
        # Phase 3: Start Frontend Server
        logger.info("🎨 Starting frontend server...")
        start_frontend_server()
        if not check_server_health("http://localhost:5173", 60, "Frontend Server"):
            logger.error("❌ Frontend server failed to start")
            return False
        
        # Phase 4: Open Browser
        logger.info("🌐 Opening browser...")
        # Run in background thread to not block
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Phase 5: Keep Running with Status Updates
        logger.info("\n" + "="*60)
        logger.info("🎉 FinLens is ready! All services are running.")
        logger.info("📊 Dashboard: http://localhost:5173")
        logger.info("🔌 API: http://localhost:8083")
        logger.info("⏹️  Press Ctrl+C to stop all services")
        logger.info("="*60 + "\n")
        
        # Wait for user to stop with periodic status checks
        try:
            last_status_check = time.time()
            while True:
                time.sleep(5)
                
                # Check process health every 30 seconds
                current_time = time.time()
                if current_time - last_status_check > 30:
                    logger.info("📊 Status: All services running normally")
                    last_status_check = current_time
                
                # Check if processes are still running
                if api_server_process and api_server_process.poll() is not None:
                    logger.error("❌ API server stopped unexpectedly")
                    break
                if frontend_process and frontend_process.poll() is not None:
                    logger.error("❌ Frontend server stopped unexpectedly")
                    break
        except KeyboardInterrupt:
            logger.info("\n🛑 Received stop signal, shutting down gracefully...")
            pass
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in local mode: {e}")
        return False
    finally:
        cleanup_processes()

def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    _display_banner()
    
    # Check for Docker mode
    if "--docker-mode" in sys.argv:
        return docker_mode()
    else:
        return local_mode()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
