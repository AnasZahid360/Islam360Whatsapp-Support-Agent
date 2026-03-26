#!/usr/bin/env python3
"""
Verification script to test all components before starting
"""

import os
import sys

def check_env_vars():
    """Check if all required environment variables are set"""
    print("🔍 Checking Environment Variables...\n")
    
    required_vars = {
        'LIVEKIT_API_KEY': 'LiveKit API Key',
        'LIVEKIT_API_SECRET': 'LiveKit Secret',
        'LIVEKIT_API_URL': 'LiveKit URL',
        'OPENAI_API_KEY': 'OpenAI API Key (Chat/LLM)',
        'OPENAI_TTS_API_KEY': 'OpenAI TTS API Key',
    }
    
    missing = []
    found = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Show masked value for security
            if var.startswith('OPENAI') or var.startswith('LIVEKIT'):
                masked = value[:10] + '...' + value[-5:] if len(value) > 15 else '***'
                print(f"  ✅ {description:40} {masked}")
                found.append(var)
            else:
                print(f"  ✅ {description:40} {value}")
                found.append(var)
        else:
            print(f"  ❌ {description:40} NOT SET")
            missing.append(var)
    
    print(f"\n✅ Found: {len(found)}/{len(required_vars)}")
    
    if missing:
        print(f"❌ Missing: {', '.join(missing)}")
        print("\nPlease add these to your .env file")
        return False
    
    return True


def check_packages():
    """Check if required packages are installed"""
    print("\n🔍 Checking Python Packages...\n")
    
    packages = {
        'livekit': 'LiveKit SDK',
        'livekit.agents': 'LiveKit Agents',
        'livekit.plugins.silero': 'Silero STT',
        'livekit.plugins.openai': 'OpenAI Plugin',
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
    }
    
    missing = []
    
    for package, name in packages.items():
        try:
            __import__(package)
            print(f"  ✅ {name:40} installed")
        except ImportError:
            print(f"  ❌ {name:40} NOT installed")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("\nInstall with: pip install -r requirements.txt")
        return False
    
    print(f"\n✅ All required packages installed!")
    return True


def check_docker():
    """Check if Docker is available"""
    print("\n🔍 Checking Docker...\n")
    
    import subprocess
    
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ Docker installed: {result.stdout.strip()}")
            return True
        else:
            print(f"  ❌ Docker not available")
            return False
    except FileNotFoundError:
        print(f"  ❌ Docker command not found")
        return False


def main():
    print("\n" + "="*60)
    print("🧪 MakTek LiveKit Voice Setup Verification")
    print("="*60 + "\n")
    
    checks = [
        ("Environment Variables", check_env_vars),
        ("Python Packages", check_packages),
        ("Docker", check_docker),
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results[check_name] = False
    
    print("\n" + "="*60)
    print("📊 Summary")
    print("="*60 + "\n")
    
    all_passed = all(results.values())
    
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status:10} {check_name}")
    
    print()
    
    if all_passed:
        print("✅ All checks passed! Ready to start services.")
        print("\nRun: chmod +x start-all.sh && ./start-all.sh")
        return 0
    else:
        print("❌ Some checks failed. Fix the issues above and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
