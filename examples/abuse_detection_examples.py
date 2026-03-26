"""
Example usage of the Abuse Detection Guardrails System.

Demonstrates how to:
1. Detect abuse in messages
2. Configure detection sensitivity
3. Monitor violations
4. Generate reports
5. Handle escalation protocols
"""

import asyncio
from src.guardrails.abuse_detector import detect_abuse
from src.guardrails.config import GuardrailConfig
from src.guardrails.abuse_monitor import AbuseMonitor, AbuseIncident
from datetime import datetime


def example_1_basic_detection():
    """Example 1: Basic abuse detection."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Abuse Detection")
    print("=" * 60)
    
    test_messages = [
        "Hello, how can I get help with my account?",  # Clean
        "This is damn frustrating!",  # Profanity
        "You're a loser and I hate you!",  # Harassment
        "FUCK OFF!!!",  # Critical
        "I need help with my order",  # Clean
    ]
    
    for msg in test_messages:
        has_abuse, abuse_type, severity, count = detect_abuse(msg)
        status = "✓ CLEAN" if not has_abuse else f"🚨 {severity.upper()}"
        print(f"\n{status}: \"{msg}\"")
        if has_abuse:
            print(f"   Type: {abuse_type}, Violations: {count}")


def example_2_severity_levels():
    """Example 2: Different severity levels."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Severity Level Classification")
    print("=" * 60)
    
    severity_examples = {
        "low": "ugh, this is annoying",
        "medium": "AAAAAAA STOP THIS!!!",
        "high": "you're terrible at this, go away",
        "critical": "kill yourself, you piece of shit",
    }
    
    for expected_severity, msg in severity_examples.items():
        has_abuse, abuse_type, severity, count = detect_abuse(msg)
        print(f"\n{severity.upper()}: \"{msg}\"")
        print(f"   Type: {abuse_type}")
        
        # Show response for this severity
        response = GuardrailConfig.get_response_for_severity(severity)
        print(f"   Response: {response[:80]}...")


def example_3_custom_configuration():
    """Example 3: Custom configuration."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Custom Configuration")
    print("=" * 60)
    
    print("\nAdding custom bad words...")
    GuardrailConfig.add_custom_bad_word("islamophobic")
    GuardrailConfig.add_custom_bad_word("xenophobic")
    
    print("Added: islamophobic, xenophobic")
    
    print("\nAdding whitelist pattern...")
    GuardrailConfig.add_whitelist_pattern(r"hell.*o")  # "hello" won't trigger
    print("Added whitelist pattern: 'hello'")
    
    print("\nCurrent custom bad words:", GuardrailConfig.CUSTOM_BAD_WORDS)
    print("Current whitelist patterns:", GuardrailConfig.WHITELIST_PATTERNS)


def example_4_monitoring():
    """Example 4: Incident monitoring and tracking."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Incident Monitoring")
    print("=" * 60)
    
    monitor = AbuseMonitor()
    
    # Simulate multiple violations
    test_cases = [
        ("user_123", "thread_1", "damn", "high", "This is damn annoying"),
        ("user_123", "thread_1", "harassment", "high", "you suck at this"),
        ("user_456", "thread_2", "profanity", "high", "fucking waste of time"),
        ("user_123", "thread_3", "spam", "low", "aaaaaaaaaa"),
    ]
    
    for user_id, thread_id, abuse_type, severity, msg in test_cases:
        incident = AbuseIncident(
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            thread_id=thread_id,
            abuse_type=abuse_type,
            severity=severity,
            message_preview=msg,
            action_taken="logged"
        )
        monitor.log_incident(incident)
    
    # Get violation counts
    print("\nViolation Counts:")
    print(f"  User 123: {monitor.get_user_violation_count('user_123')} total")
    print(f"  User 123 (HIGH only): {monitor.get_user_violation_count('user_123', 'high')}")
    print(f"  User 456: {monitor.get_user_violation_count('user_456')} total")
    
    # Check if user should be blocked
    print("\nUser Status:")
    print(f"  User 123 blocked: {monitor.should_block_user('user_123', max_violations=5)}")
    print(f"  User 123 blocked (strict): {monitor.should_block_user('user_123', max_violations=2)}")


def example_5_user_report():
    """Example 5: Generate user abuse report."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: User Abuse Report")
    print("=" * 60)
    
    monitor = AbuseMonitor()
    
    # Add some violations
    for i in range(3):
        incident = AbuseIncident(
            timestamp=datetime.now().isoformat(),
            user_id="user_789",
            thread_id=f"thread_{i}",
            abuse_type="profanity",
            severity="high" if i % 2 == 0 else "medium",
            message_preview=f"Message {i}",
            ticket_id=f"TKT-{i}",
        )
        monitor.log_incident(incident)
    
    # Generate report
    report = monitor.generate_user_report("user_789")
    
    print(f"\nUser ID: {report['user_id']}")
    print(f"Total Violations: {report['total_violations']}")
    print(f"Should Block: {report['should_block']}")
    print(f"\nSeverity Breakdown:")
    for severity, count in report['severity_breakdown'].items():
        print(f"  {severity.capitalize()}: {count}")
    print(f"\nType Breakdown:")
    for type_name, count in report['type_breakdown'].items():
        print(f"  {type_name.capitalize()}: {count}")


def example_6_system_report():
    """Example 6: Generate system-wide report."""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: System-Wide Report")
    print("=" * 60)
    
    monitor = AbuseMonitor()
    
    # Generate report
    report = monitor.generate_system_report()
    
    print(f"\nTotal Incidents: {report['total_incidents']}")
    print(f"Unique Users: {report['unique_users']}")
    print(f"Unique Sessions: {report['unique_sessions']}")
    print(f"\nSeverity Breakdown:")
    for severity, count in report['severity_breakdown'].items():
        print(f"  {severity.capitalize()}: {count}")
    print(f"\nType Breakdown:")
    for type_name, count in report['type_breakdown'].items():
        print(f"  {type_name.capitalize()}: {count}")


def example_7_response_messages():
    """Example 7: Response messages for different severities."""
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Response Messages")
    print("=" * 60)
    
    severities = ["low", "medium", "high", "critical"]
    
    for severity in severities:
        response = GuardrailConfig.get_response_for_severity(severity)
        print(f"\n{severity.upper()} SEVERITY:")
        print(f"'{response}'")


def example_8_detection_patterns():
    """Example 8: Show detection patterns."""
    print("\n" + "=" * 60)
    print("EXAMPLE 8: Detection Patterns")
    print("=" * 60)
    
    from src.guardrails.config import ABUSEDetectionConfig
    
    config = ABUSEDetectionConfig()
    
    print("\nProfanity Patterns:")
    for i, pattern in enumerate(config.PROFANITY_PATTERNS[:2], 1):
        print(f"  {i}. {pattern}")
    
    print("\nHarassment Patterns:")
    for i, pattern in enumerate(config.HARASSMENT_PATTERNS[:2], 1):
        print(f"  {i}. {pattern}")
    
    print("\nHate Speech Patterns:")
    for i, pattern in enumerate(config.HATE_SPEECH_PATTERNS[:2], 1):
        print(f"  {i}. {pattern}")
    
    print("\nSpam Patterns:")
    for i, pattern in enumerate(config.SPAM_PATTERNS, 1):
        print(f"  {i}. {pattern}")


async def example_9_configuration_options():
    """Example 9: Explore configuration options."""
    print("\n" + "=" * 60)
    print("EXAMPLE 9: Configuration Options")
    print("=" * 60)
    
    print("\nGuardrail Configuration:")
    print(f"  Enable Abuse Detection: {GuardrailConfig.ENABLE_ABUSE_DETECTION}")
    print(f"  Enable Profanity Detection: {GuardrailConfig.PROFANITY_ENABLED}")
    print(f"  Enable Harassment Detection: {GuardrailConfig.HARASSMENT_ENABLED}")
    print(f"  Enable Spam Detection: {GuardrailConfig.SPAM_ENABLED}")
    
    print("\nSensitivity Levels (0.0-1.0):")
    print(f"  Profanity: {GuardrailConfig.PROFANITY_SENSITIVITY}")
    print(f"  Harassment: {GuardrailConfig.HARASSMENT_SENSITIVITY}")
    print(f"  Spam: {GuardrailConfig.SPAM_SENSITIVITY}")
    
    print("\nViolation Thresholds:")
    print(f"  Max Low per Session: {GuardrailConfig.MAX_LOW_VIOLATIONS_PER_SESSION}")
    print(f"  Max Medium per Session: {GuardrailConfig.MAX_MEDIUM_VIOLATIONS_PER_SESSION}")
    print(f"  Max High per Session: {GuardrailConfig.MAX_HIGH_VIOLATIONS_PER_SESSION}")
    print(f"  Max Critical per Session: {GuardrailConfig.MAX_CRITICAL_VIOLATIONS_PER_SESSION}")
    
    print("\nLogging & Escalation:")
    print(f"  Log Violations: {GuardrailConfig.LOG_VIOLATIONS}")
    print(f"  Auto-ticket on High: {GuardrailConfig.AUTO_CREATE_TICKET_ON_HIGH}")
    print(f"  Auto-ticket on Critical: {GuardrailConfig.AUTO_CREATE_TICKET_ON_CRITICAL}")


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "ABUSE DETECTION GUARDRAILS EXAMPLES" + " " * 14 + "║")
    print("╚" + "=" * 58 + "╝")
    
    # Run examples
    example_1_basic_detection()
    example_2_severity_levels()
    example_3_custom_configuration()
    example_4_monitoring()
    example_5_user_report()
    example_6_system_report()
    example_7_response_messages()
    example_8_detection_patterns()
    asyncio.run(example_9_configuration_options())
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
