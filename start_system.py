#!/usr/bin/env python3
"""
System launcher for Cyber Sentinel ML
Starts both the model server and web application
"""

import os
import sys
import time
import subprocess
import signal
import platform
from threading import Thread

class SystemLauncher:
    def __init__(self):
        self.model_server_process = None
        self.web_app_process = None
        self.running = True
        
    def start_model_server(self):
        """Start the model server in a separate process"""
        print("🚀 Starting Model Server...")
        try:
            # Start model server
            self.model_server_process = subprocess.Popen(
                [sys.executable, 'model_server.py'],
                cwd=os.getcwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Monitor model server output
            def monitor_server():
                while self.running and self.model_server_process:
                    output = self.model_server_process.stdout.readline()
                    if output:
                        print(f"[Model Server] {output.strip()}")
                    elif self.model_server_process.poll() is not None:
                        break
            
            Thread(target=monitor_server, daemon=True).start()
            
            # Wait for server to start
            time.sleep(3)
            
            # Check if server is still running
            if self.model_server_process.poll() is None:
                print("✅ Model Server started successfully")
                return True
            else:
                print("❌ Model Server failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Error starting Model Server: {e}")
            return False
    
    def start_web_application(self, mode='fallback'):
        """Start the web application"""
        print(f"🌐 Starting Web Application ({mode} mode)...")
        try:
            script_name = f'run_{mode}.py'
            if not os.path.exists(script_name):
                script_name = 'app.py'
            
            self.web_app_process = subprocess.Popen(
                [sys.executable, script_name],
                cwd=os.getcwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Monitor web app output
            def monitor_web():
                while self.running and self.web_app_process:
                    output = self.web_app_process.stdout.readline()
                    if output:
                        print(f"[Web App] {output.strip()}")
                    elif self.web_app_process.poll() is not None:
                        break
            
            Thread(target=monitor_web, daemon=True).start()
            
            # Wait a moment for startup
            time.sleep(2)
            
            if self.web_app_process.poll() is None:
                print("✅ Web Application started successfully")
                return True
            else:
                print("❌ Web Application failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Error starting Web Application: {e}")
            return False
    
    def stop_all(self):
        """Stop all processes"""
        print("\n🛑 Shutting down system...")
        self.running = False
        
        if self.web_app_process:
            try:
                self.web_app_process.terminate()
                self.web_app_process.wait(timeout=5)
                print("✅ Web Application stopped")
            except:
                self.web_app_process.kill()
        
        if self.model_server_process:
            try:
                self.model_server_process.terminate()
                self.model_server_process.wait(timeout=5)
                print("✅ Model Server stopped")
            except:
                self.model_server_process.kill()
    
    def run(self, mode='fallback'):
        """Run the complete system"""
        print("🔧 Cyber Sentinel System Launcher")
        print("=" * 50)
        
        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            self.stop_all()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start model server
        if not self.start_model_server():
            print("❌ Failed to start Model Server. Exiting.")
            return False
        
        # Start web application
        if not self.start_web_application(mode):
            print("❌ Failed to start Web Application. Stopping server.")
            self.stop_all()
            return False
        
        print("\n🎉 System started successfully!")
        print("=" * 50)
        print("📊 Dashboard: http://localhost:5000")
        print("🔍 Real-time Detection: http://localhost:5000/detection")
        print("📈 History: http://localhost:5000/history")
        print("\n💡 Services running:")
        print("   ✅ Model Server (port 9999)")
        print(f"   ✅ Web Application ({mode} mode)")
        print("\n⚠️  Press Ctrl+C to stop all services")
        print("=" * 50)
        
        try:
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
                
                # Check if processes are still running
                if self.model_server_process.poll() is not None:
                    print("❌ Model Server stopped unexpectedly")
                    break
                
                if self.web_app_process.poll() is not None:
                    print("❌ Web Application stopped unexpectedly")
                    break
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_all()
        
        return True

def main():
    """Main launcher function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cyber Sentinel System Launcher')
    parser.add_argument('--mode', choices=['production', 'fallback'], 
                       default='fallback', help='Startup mode')
    
    args = parser.parse_args()
    
    launcher = SystemLauncher()
    success = launcher.run(args.mode)
    
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()
