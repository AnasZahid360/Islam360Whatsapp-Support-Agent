# Abuse Detection & Guardrails System

## Overview

The Abuse Detection system is a comprehensive guardrail that protects the chatbot from abusive language, profanity, harassment, and toxic behavior. It uses multi-level severity classification and automatic escalation protocols to handle different types of abuse.

## Features

### 1. **Multi-Level Detection**
- **Profanity Detection**: Detects common curse words and vulgar language
- **Harassment Detection**: Identifies hostile, threatening, or demeaning language
- **Hate Speech Detection**: Catches discriminatory and hateful content
- **Spam Detection**: Identifies repetitive patterns and unusual character usage

### 2. **Severity Classification**
Detected abuse is classified into four severity levels:

| Severity | Action | Response |
|----------|--------|----------|
| **LOW** | Warning | Gentle reminder to keep conversation respectful |
| **MEDIUM** | Warning + Note | Professional request to rephrase, support team notified |
| **HIGH** | Escalation + Ticket | Creates support ticket, offers human representative connection |
| **CRITICAL** | Escalation + Termination | Creates ticket, terminates conversation, requires escalation |

### 3. **Automatic Escalation Protocols**

#### Low Severity Violations
- User receives a gentle warning
- Conversation continues normally
- Tracked in session history

#### Medium Severity Violations
- Professional warning message
- Support team is notified
- Tracked for user behavior analysis

#### High Severity Violations
- Automatic support ticket creation
- User offered escalation to human representative
- Conversation may be terminated
- User escalation status set to "proposed"

#### Critical Severity Violations
- Immediate conversation termination
- Automatic support ticket creation with URGENT priority
- User account flagged for review
- Mandatory escalation to human representative
- User violation count incremented

### 4. **User Tracking & Blocking**

The system maintains violation history per user:
- Tracks all violations across conversations
- Maintains session-level violation counts
- Automatically blocks users after exceeding threshold:
  - Default: 5 violations in system
  - Configurable per violation type

```python
# Check if user should be blocked
if monitor.should_block_user(user_id):
    # Block user from further interactions
```

### 5. **Incident Logging & Monitoring**

All abuse incidents are logged with:
- Timestamp
- User ID & Thread ID
- Abuse type and severity
- Message preview (first 200 chars)
- Support ticket ID
- Action taken

Logs are stored in: `./logs/abuse_incidents/`

## Configuration

Edit `src/guardrails/config.py` to customize:

```python
class GuardrailConfig:
    # Enable/disable specific checks
    ENABLE_ABUSE_DETECTION = True
    PROFANITY_ENABLED = True
    HARASSMENT_ENABLED = True
    SPAM_ENABLED = True
    
    # Sensitivity levels (0.0 to 1.0)
    PROFANITY_SENSITIVITY = 0.8
    HARASSMENT_SENSITIVITY = 0.7
    SPAM_SENSITIVITY = 0.6
    
    # Auto-create tickets for high/critical
    AUTO_CREATE_TICKET_ON_HIGH = True
    AUTO_CREATE_TICKET_ON_CRITICAL = True
    
    # User blocking thresholds
    MAX_LOW_VIOLATIONS_PER_SESSION = 5
    MAX_MEDIUM_VIOLATIONS_PER_SESSION = 3
    MAX_HIGH_VIOLATIONS_PER_SESSION = 2
    MAX_CRITICAL_VIOLATIONS_PER_SESSION = 1
```

## Adding Custom Bad Words

```python
from src.guardrails.config import GuardrailConfig

# Add custom bad words
GuardrailConfig.add_custom_bad_word("inappropriate_word")

# Add custom harassment patterns
GuardrailConfig.add_custom_harassment_pattern(r"pattern_to_match")

# Add whitelist patterns (skip detection)
GuardrailConfig.add_whitelist_pattern(r"pattern_to_exclude")
```

## API Reference

### `detect_abuse(text: str) -> Tuple[bool, str, str, int]`

Detects abuse in text and returns severity classification.

**Returns:**
- `has_abuse`: Boolean indicating if abuse was found
- `abuse_type`: Type of abuse ("profanity", "harassment", "hate_speech", "spam", "none")
- `severity`: Severity level ("low", "medium", "high", "critical", "none")
- `violation_count`: Number of violations found

**Example:**
```python
from src.guardrails.abuse_detector import detect_abuse

has_abuse, abuse_type, severity, count = detect_abuse("damn, this is terrible!")
# Returns: (True, "profanity", "high", 1)
```

### `AbuseMonitor` Class

Tracks and logs all abuse incidents.

**Methods:**

```python
from src.guardrails.abuse_monitor import abuse_monitor

# Log an incident
incident = AbuseIncident(...)
abuse_monitor.log_incident(incident)

# Get user violation count
count = abuse_monitor.get_user_violation_count(user_id)
count = abuse_monitor.get_user_violation_count(user_id, severity="high")

# Get session violations
violations = abuse_monitor.get_session_violations(thread_id)

# Check if user should be blocked
should_block = abuse_monitor.should_block_user(user_id, max_violations=5)

# Check if session needs escalation
needs_escalation = abuse_monitor.should_escalate_to_human(thread_id)

# Generate reports
user_report = abuse_monitor.generate_user_report(user_id)
system_report = abuse_monitor.generate_system_report()
```

## Graph Integration

The abuse detector is integrated as a node in the agent graph:

```
START 
  ↓
input_guardrail (PII detection)
  ↓
abuse_detector ← NEW NODE
  ↓
supervisor
  ↓
retriever_agent → generator_agent → hallucination_check
  ↓
escalator_agent
  ↓
END
```

## State Fields

New fields added to `AgentState`:

```python
abuse_violation: bool          # Flag indicating abuse was detected
abuse_type: str               # Type of abuse (profanity, harassment, etc.)
abuse_severity: str           # Severity level (low, medium, high, critical)
abuse_count: int              # Count of violations in current session
```

## Response Messages

Customizable response messages for each severity level:

**Low Severity:**
> "I appreciate your question, but I'd like to keep our conversation respectful. Let's focus on how I can help you with your support needs. How can I assist you today?"

**Medium Severity:**
> "I understand you may be frustrated, but I need to ask that we keep our conversation professional. I'm here to help resolve your issue. Please rephrase your question and I'll do my best to assist."

**High Severity:**
> "I'm concerned about the language in your message. I'm here to help you professionally, but I need us to communicate respectfully. A support ticket has been created so our team can assist you further. Would you like to connect with a human representative?"

**Critical Severity:**
> "I'm unable to continue this conversation due to abusive language. Our support team has been notified and will contact you. If you'd like to continue, please ensure your communication is respectful."

## Monitoring & Analytics

### User Report
```python
report = abuse_monitor.generate_user_report(user_id)
# Returns:
# {
#     "user_id": "user_123",
#     "total_violations": 5,
#     "severity_breakdown": {
#         "low": 2,
#         "medium": 1,
#         "high": 1,
#         "critical": 1
#     },
#     "type_breakdown": {
#         "profanity": 3,
#         "harassment": 2
#     },
#     "should_block": True,
#     "incidents": [...]
# }
```

### System Report
```python
report = abuse_monitor.generate_system_report()
# Returns aggregate statistics across all users and sessions
```

## Logging

Abuse incidents are logged to JSON Lines files:

**Location:** `./logs/abuse_incidents/abuse_incidents_YYYY-MM-DD.jsonl`

**Format:**
```json
{
  "timestamp": "2024-01-16T10:30:45.123456",
  "user_id": "user_123",
  "thread_id": "thread_456",
  "abuse_type": "profanity",
  "severity": "high",
  "message_preview": "This is a damn bad response...",
  "ticket_id": "TKT-20240116-789",
  "action_taken": "escalated"
}
```

## Best Practices

1. **Regular Monitoring**: Review system reports regularly
2. **Adjust Sensitivity**: Fine-tune sensitivity levels based on false positive rates
3. **Custom Patterns**: Add domain-specific harassment patterns
4. **User Education**: Inform users about respectful communication guidelines
5. **Support Training**: Ensure support team knows how to handle escalated abuse cases
6. **Privacy**: Keep abuse logs secure and confidential

## Troubleshooting

### High False Positives
- Lower sensitivity levels in config
- Add patterns to whitelist
- Review detected patterns and adjust

### Missed Abuse
- Increase sensitivity levels
- Add custom bad words or patterns
- Review logs to identify missing patterns

### Performance Issues
- Consider async processing for large patterns
- Implement caching for frequent checks
- Monitor log file size growth

## Future Enhancements

- [ ] Multi-language support (Urdu, Arabic)
- [ ] Machine learning-based abuse detection
- [ ] Contexual abuse detection
- [ ] Sentiment analysis integration
- [ ] Automated moderation actions
- [ ] Abuse pattern trending & analytics dashboard
