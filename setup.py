#!/usr/bin/env python3
"""
Setup script for Hippies Heaven Lead Generation Bot
Helps with initial configuration and testing
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file from template"""
    template_path = Path('env.template')
    env_path = Path('.env')
    
    if env_path.exists():
        print("✅ .env file already exists")
        return True
    
    if not template_path.exists():
        print("❌ env.template not found")
        return False
    
    # Copy template to .env
    with open(template_path, 'r') as f:
        content = f.read()
    
    with open(env_path, 'w') as f:
        f.write(content)
    
    print("✅ Created .env file from template")
    print("📝 Please edit .env file with your API keys and email settings")
    return True

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import requests
        import pandas
        import openpyxl
        import flask
        import googlemaps
        import reportlab
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def test_bot_help():
    """Test if bot.py runs without errors"""
    try:
        import subprocess
        result = subprocess.run([sys.executable, 'bot.py', '--help'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Bot script is working correctly")
            return True
        else:
            print(f"❌ Bot script error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error testing bot: {e}")
        return False

def main():
    print("🚀 Hippies Heaven Lead Generation Bot Setup")
    print("=" * 50)
    
    # Check dependencies
    print("\n1. Checking dependencies...")
    deps_ok = check_dependencies()
    
    # Create .env file
    print("\n2. Setting up configuration...")
    env_ok = create_env_file()
    
    # Test bot
    print("\n3. Testing bot script...")
    bot_ok = test_bot_help()
    
    print("\n" + "=" * 50)
    if deps_ok and env_ok and bot_ok:
        print("✅ Setup complete! Next steps:")
        print("1. Edit .env file with your API keys")
        print("2. Get Google Places API key from Google Cloud Console")
        print("3. Get Gmail App Password from Google Account settings")
        print("4. Run: python bot.py --mode collect")
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
    
    print("\n📚 For detailed instructions, see README.md")

if __name__ == '__main__':
    main()



