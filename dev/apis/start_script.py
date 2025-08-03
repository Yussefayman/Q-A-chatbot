#!/usr/bin/env python3
"""
QuestAI API Server
Simple startup script for the FastAPI backend
"""

import os
import sys
import subprocess


def check_project_structure():
    """Check if we're in the right place"""
    print("\n🔍 Checking project structure...")
    
    # Check if main.py exists in current directory
    if not os.path.exists("main.py"):
        print("❌ main.py not found in current directory")
        print("Make sure you're running this from the 'apis' folder")
        return False
    
    # Check if parent directories exist
    parent_dirs = ["../dev", "../qa-frontend"]
    for dir_path in parent_dirs:
        if os.path.exists(dir_path):
            print(f"✅ Found {dir_path}")
        else:
            print(f"⚠️  {dir_path} not found (this is optional)")
    
    return True


def main():
    """Main function to start the API server"""
    print("🤖 QuestAI API Server")
    print("=" * 25)
    
    
    print("\n🚀 Starting API server...")
    print("📍 API will be available at: http://localhost:8000")
    print("📖 Documentation: http://localhost:8000/docs")
    print("🔄 Press Ctrl+C to stop\n")

    if not check_project_structure():
        print("\n❌ Please make sure you're in the 'apis' directory and main.py exists")
        sys.exit(1)
    
    try:
        # Start the server with more specific module path
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--log-level", "info"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting server: {e}")
        print("\nTry running manually:")
        print("python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    except FileNotFoundError:
        print("\n❌ uvicorn not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "uvicorn[standard]"])
        print("Now try running: python start.py")

if __name__ == "__main__":
    main()