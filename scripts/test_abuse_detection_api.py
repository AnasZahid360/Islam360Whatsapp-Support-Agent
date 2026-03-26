"""
Test script for Abuse Detection API endpoints.

Tests:
1. Abuse detection endpoint
2. User abuse reports
3. Session abuse reports
4. System-wide reports
5. User status checks
6. Combined check and flag
"""

import requests
import json
from typing import Dict, Any

# API base URL
BASE_URL = "http://127.0.0.1:8000"


def print_response(title: str, response: Dict[str, Any]):
    """Pretty print API response."""
    print(f"\n{'='*60}")
    print(f"✓ {title}")
    print(f"{'='*60}")
    print(json.dumps(response, indent=2))


def test_abuse_detection():
    """Test the abuse detection endpoint."""
    print("\n" + "="*60)
    print("TEST 1: Abuse Detection")
    print("="*60)
    
    test_cases = [
        ("hello, how can I get help?", "Clean message"),
        ("This is damn frustrating!", "Profanity"),
        ("You're terrible and I hate you!", "Harassment"),
        ("FUCK OFF!!!!", "Critical abuse"),
        ("aaaaaaaaaaaa STOP", "Spam"),
    ]
    
    for message, description in test_cases:
        try:
            response = requests.post(
                f"{BASE_URL}/abuse/detect",
                params={"message": message}
            )
            result = response.json()
            
            status = "🚨 DETECTED" if result["has_abuse"] else "✓ CLEAN"
            print(f"\n{status}: {description}")
            print(f"  Message: '{message}'")
            if result["has_abuse"]:
                print(f"  Type: {result['abuse_type']}")
                print(f"  Severity: {result['severity']}")
                print(f"  Violations: {result['violation_count']}")
        except Exception as e:
            print(f"❌ Error: {e}")


def test_user_violations():
    """Test user violation count endpoint."""
    print("\n" + "="*60)
    print("TEST 2: User Violation Status")
    print("="*60)
    
    test_user = "test_user_123"
    
    try:
        # Get all violations
        response = requests.get(
            f"{BASE_URL}/abuse/user/{test_user}/violations"
        )
        result = response.json()
        print_response(f"User {test_user} Violation Count", result)
        
        # Get high severity only
        response = requests.get(
            f"{BASE_URL}/abuse/user/{test_user}/violations",
            params={"severity": "high"}
        )
        result = response.json()
        print_response(f"User {test_user} HIGH Severity Count", result)
    except Exception as e:
        print(f"❌ Error: {e}")


def test_user_status():
    """Test user quick status endpoint."""
    print("\n" + "="*60)
    print("TEST 3: User Abuse Status")
    print("="*60)
    
    test_users = ["test_user_123", "new_user_456", "bad_user_789"]
    
    for user_id in test_users:
        try:
            response = requests.get(f"{BASE_URL}/abuse/user/{user_id}/status")
            result = response.json()
            
            print(f"\nUser: {user_id}")
            print(f"  Total Violations: {result['total_violations']}")
            print(f"  Should Block: {result['should_block']}")
            if result['recent_violation_types']:
                print(f"  Recent Types: {result['recent_violation_types']}")
            if result['latest_incident']:
                print(f"  Latest: {result['latest_incident']['severity']} ({result['latest_incident']['type']})")
        except Exception as e:
            print(f"❌ Error: {e}")


def test_user_report():
    """Test comprehensive user report endpoint."""
    print("\n" + "="*60)
    print("TEST 4: Comprehensive User Report")
    print("="*60)
    
    test_user = "test_user_123"
    
    try:
        response = requests.get(f"{BASE_URL}/abuse/user/{test_user}")
        result = response.json()
        print_response(f"User Report: {test_user}", result)
    except Exception as e:
        print(f"❌ Error: {e}")


def test_session_report():
    """Test session/thread report endpoint."""
    print("\n" + "="*60)
    print("TEST 5: Session Abuse Report")
    print("="*60)
    
    test_thread = "thread_20260316_001"
    
    try:
        response = requests.get(f"{BASE_URL}/abuse/session/{test_thread}")
        result = response.json()
        
        print(f"\nThread: {test_thread}")
        print(f"Total Violations: {result['total_violations']}")
        if result['incidents']:
            print("Recent Incidents:")
            for incident in result['incidents'][-3:]:
                print(f"  - {incident['severity'].upper()}: {incident['abuse_type']} ({incident['timestamp']})")
        else:
            print("No incidents found")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_system_report():
    """Test system-wide report endpoint."""
    print("\n" + "="*60)
    print("TEST 6: System-Wide Abuse Report")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/abuse/system-report")
        result = response.json()
        print_response("System-Wide Report", result)
    except Exception as e:
        print(f"❌ Error: {e}")


def test_check_and_flag():
    """Test combined check and flag endpoint."""
    print("\n" + "="*60)
    print("TEST 7: Check and Flag Combined")
    print("="*60)
    
    test_cases = [
        ("test_user_001", "thread_001", "hello how can I help"),
        ("test_user_002", "thread_002", "This is damn bad"),
        ("test_user_003", "thread_003", "fuck off you bastard"),
    ]
    
    for user_id, thread_id, message in test_cases:
        try:
            response = requests.post(
                f"{BASE_URL}/abuse/check-and-flag",
                params={
                    "user_id": user_id,
                    "thread_id": thread_id,
                    "message": message
                }
            )
            result = response.json()
            
            print(f"\nUser: {user_id} | Thread: {thread_id}")
            print(f"Message: '{message}'")
            print(f"Abuse Detected: {result['abuse_detected']}")
            if result['abuse_detected']:
                print(f"  Type: {result['abuse_type']}")
                print(f"  Severity: {result['severity']}")
                print(f"  Action: {result['action_recommended']}")
                print(f"  Should Block: {result['should_block_user']}")
                print(f"  Should Escalate: {result['should_escalate_to_human']}")
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " " * 12 + "ABUSE DETECTION API TEST SUITE" + " " * 16 + "║")
    print("╚" + "="*58 + "╝")
    
    print("\n📝 NOTE: Make sure the API server is running on http://127.0.0.1:8000")
    
    try:
        # Health check
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✓ API server is running\n")
        else:
            print("❌ API server not responding correctly")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API server: {e}")
        return
    
    # Run all tests
    test_abuse_detection()
    test_user_violations()
    test_user_status()
    test_user_report()
    test_session_report()
    test_system_report()
    test_check_and_flag()
    
    print("\n" + "="*60)
    print("✓ All tests completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
