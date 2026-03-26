"""
Abuse Detection Guardrails - Integration Guide

This guide explains how to integrate the abuse detection guardrails
with your chatbot system.
"""

# ============================================================================
# 1. GRAPH INTEGRATION
# ============================================================================

# The abuse_detector_node is automatically integrated into the graph flow:
#
# START
#   ↓
# input_guardrail (PII detection)
#   ↓
# abuse_detector (← NEW) ← Checks for profanity, harassment, etc.
#   ↓
# supervisor
#   ↓
# retriever_agent → generator_agent → hallucination_check
#   ↓
# escalator_agent
#   ↓
# END
#
# When abuse is detected:
# - LOW severity: Warning and continue to supervisor
# - MEDIUM severity: Warning, note support team, continue to supervisor
# - HIGH severity: Create ticket, escalate to human, route to END
# - CRITICAL severity: Create ticket, terminate, route to END


# ============================================================================
# 2. API ENDPOINTS
# ============================================================================

# New abuse detection endpoints added to api.py:

# Detection Endpoints:
# POST /abuse/detect
#   - Detect abuse in a message
#   - Params: message (str)
#   - Returns: {has_abuse, abuse_type, severity, violation_count}

# Reporting Endpoints:
# GET /abuse/user/{user_id}
#   - Get comprehensive abuse report for a user
#   - Returns: {total_violations, severity_breakdown, type_breakdown, should_block, recent_incidents}

# GET /abuse/user/{user_id}/violations
#   - Get violation count for a user
#   - Optional params: severity (filter by severity level)
#   - Returns: {user_id, violation_count, should_block}

# GET /abuse/user/{user_id}/status
#   - Get quick status check for a user
#   - Returns: {total_violations, should_block, recent_violation_types, latest_incident}

# GET /abuse/session/{thread_id}
#   - Get abuse incidents for a session
#   - Returns: {thread_id, total_violations, incidents: [...]}

# GET /abuse/system-report
#   - Get system-wide abuse statistics
#   - Returns: {total_incidents, unique_users, unique_sessions, severity_breakdown, type_breakdown}

# Combined Endpoints:
# POST /abuse/check-and-flag
#   - Check a message and get comprehensive status
#   - Params: user_id, thread_id, message
#   - Returns: {abuse_detected, abuse_type, severity, user_violations, session_violations, should_escalate, should_block, action_recommended}


# ============================================================================
# 3. CONFIGURATION
# ============================================================================

# Edit src/guardrails/config.py to customize:

from src.guardrails.config import GuardrailConfig, ABUSEDetectionConfig

# Enable/disable checks
GuardrailConfig.ENABLE_ABUSE_DETECTION = True
GuardrailConfig.PROFANITY_ENABLED = True
GuardrailConfig.HARASSMENT_ENABLED = True
GuardrailConfig.SPAM_ENABLED = True

# Adjust sensitivity (0.0 to 1.0)
GuardrailConfig.PROFANITY_SENSITIVITY = 0.8
GuardrailConfig.HARASSMENT_SENSITIVITY = 0.7
GuardrailConfig.SPAM_SENSITIVITY = 0.6

# Set blocking thresholds
GuardrailConfig.MAX_LOW_VIOLATIONS_PER_SESSION = 5
GuardrailConfig.MAX_MEDIUM_VIOLATIONS_PER_SESSION = 3
GuardrailConfig.MAX_HIGH_VIOLATIONS_PER_SESSION = 2
GuardrailConfig.MAX_CRITICAL_VIOLATIONS_PER_SESSION = 1

# Auto-escalation settings
GuardrailConfig.AUTO_CREATE_TICKET_ON_HIGH = True
GuardrailConfig.AUTO_CREATE_TICKET_ON_CRITICAL = True

# Add custom bad words
GuardrailConfig.add_custom_bad_word("myword")
GuardrailConfig.add_custom_bad_word("badword")

# Add custom harassment patterns
GuardrailConfig.add_custom_harassment_pattern(r"pattern_regex")

# Add whitelist patterns (skip detection)
GuardrailConfig.add_whitelist_pattern(r"pattern_to_exclude")


# ============================================================================
# 4. MONITORING
# ============================================================================

# Use the AbuseMonitor to track violations:

from src.guardrails.abuse_monitor import abuse_monitor, AbuseIncident
from datetime import datetime

# Log an incident
incident = AbuseIncident(
    timestamp=datetime.now().isoformat(),
    user_id="user_123",
    thread_id="thread_456",
    abuse_type="profanity",
    severity="high",
    message_preview="This is damn bad",
    ticket_id="TKT-123",
    action_taken="escalated"
)
abuse_monitor.log_incident(incident)

# Get user statistics
count = abuse_monitor.get_user_violation_count("user_123")
high_count = abuse_monitor.get_user_violation_count("user_123", severity="high")
should_block = abuse_monitor.should_block_user("user_123")

# Get session statistics
session_violations = abuse_monitor.get_session_violations("thread_456")
should_escalate = abuse_monitor.should_escalate_to_human("thread_456")

# Generate reports
user_report = abuse_monitor.generate_user_report("user_123")
system_report = abuse_monitor.generate_system_report()


# ============================================================================
# 5. DETECTION IN CODE
# ============================================================================

# Use the detect_abuse function directly:

from src.guardrails.abuse_detector import detect_abuse

message = "This is damn annoying!"
has_abuse, abuse_type, severity, count = detect_abuse(message)

if has_abuse:
    print(f"Abuse detected: {abuse_type} ({severity})")
    print(f"Action: {GuardrailConfig.get_severity_action(severity)}")
    print(f"Response: {GuardrailConfig.get_response_for_severity(severity)}")


# ============================================================================
# 6. STATE UPDATES
# ============================================================================

# The following fields are added to AgentState:

# abuse_violation: bool           # Flag if abuse was detected
# abuse_type: str                # Type of abuse detected
# abuse_severity: str            # Severity level
# abuse_count: int               # Count of violations in session


# ============================================================================
# 7. FRONTEND INTEGRATION
# ============================================================================

# In your frontend, you can:

# 1. Show warning messages based on severity
#    - Display gentle warnings for low severity
#    - Show escalation options for high severity
#    - Block interaction for critical

# 2. Make real-time checks
#    POST /abuse/detect?message=user_input
#    - Show warning as user types
#    - Prevent sending if critical

# 3. Monitor user status
#    GET /abuse/user/{user_id}/status
#    - Show warning if user has many violations
#    - Prevent interaction if user should be blocked

# Example frontend code:
/*
// Check message before sending
async function checkMessage(message) {
  const response = await fetch('/abuse/detect?message=' + encodeURIComponent(message), {
    method: 'POST'
  });
  const result = await response.json();
  
  if (result.has_abuse) {
    if (result.severity === 'critical') {
      showError('This message contains inappropriate language. Cannot send.');
      return false;
    } else if (result.severity === 'high') {
      showWarning(`Warning: This message contains ${result.abuse_type}.`);
    }
  }
  return true;
}

// Check user status
async function checkUserStatus(userId) {
  const response = await fetch(`/abuse/user/${userId}/status`);
  const status = await response.json();
  
  if (status.should_block) {
    showError('Your account has been suspended due to violations.');
    disableChat();
  }
}
*/


# ============================================================================
# 8. LOGGING & STORAGE
# ============================================================================

# Incidents are logged to JSON Lines files:
# Location: ./logs/abuse_incidents/abuse_incidents_YYYY-MM-DD.jsonl

# Each line is a JSON object:
# {
#   "timestamp": "2024-01-16T10:30:45.123456",
#   "user_id": "user_123",
#   "thread_id": "thread_456",
#   "abuse_type": "profanity",
#   "severity": "high",
#   "message_preview": "This is damn bad...",
#   "ticket_id": "TKT-123",
#   "action_taken": "escalated"
# }

# Access logs:
import json
from pathlib import Path

log_dir = Path("./logs/abuse_incidents")
for log_file in log_dir.glob("abuse_incidents_*.jsonl"):
    with open(log_file, 'r') as f:
        for line in f:
            incident = json.loads(line)
            print(incident)


# ============================================================================
# 9. TESTING
# ============================================================================

# Run the example script:
# python examples/abuse_detection_examples.py

# Test the API endpoints:
# python scripts/test_abuse_detection_api.py

# Run inline tests:
# python -c "
# from src.guardrails.abuse_detector import detect_abuse
# has_abuse, abuse_type, severity, count = detect_abuse('damn this is bad')
# assert has_abuse == True
# assert severity == 'high'
# print('✓ Tests passed')
# "


# ============================================================================
# 10. TROUBLESHOOTING
# ============================================================================

# Issue: False positives (benign words flagged as abuse)
# Solution:
#   1. Add words to whitelist: GuardrailConfig.add_whitelist_pattern(r"pattern")
#   2. Reduce sensitivity: GuardrailConfig.PROFANITY_SENSITIVITY = 0.6
#   3. Review and update patterns in src/guardrails/config.py

# Issue: Missed abuse (real abuse not detected)
# Solution:
#   1. Increase sensitivity: GuardrailConfig.PROFANITY_SENSITIVITY = 1.0
#   2. Add custom patterns: GuardrailConfig.add_custom_bad_word("word")
#   3. Review logs to find missing patterns

# Issue: Performance degradation
# Solution:
#   1. Monitor log file size: ./logs/abuse_incidents/
#   2. Archive old logs periodically
#   3. Consider async processing for high-volume scenarios

# Issue: Users being blocked unfairly
# Solution:
#   1. Review user reports: GET /abuse/user/{user_id}
#   2. Check specific incidents: GET /abuse/session/{thread_id}
#   3. Adjust thresholds: GuardrailConfig.MAX_*_VIOLATIONS_PER_SESSION
#   4. Implement manual unblocking mechanism


# ============================================================================
# 11. BEST PRACTICES
# ============================================================================

# 1. Regular monitoring
#    - Review system report weekly
#    - Check for trending violation patterns
#    - Adjust configuration as needed

# 2. User communication
#    - Provide clear feedback about violations
#    - Explain why content was flagged
#    - Offer path to resolve (escalation, resubmission)

# 3. Support team training
#    - Educate on abuse patterns
#    - Document escalation procedures
#    - Provide decision-making guidelines

# 4. Privacy & compliance
#    - Keep abuse logs secure
#    - Comply with data retention policies
#    - Implement proper access controls

# 5. Continuous improvement
#    - Collect feedback on false positives
#    - Update patterns regularly
#    - Test new detections before deployment

# ============================================================================
