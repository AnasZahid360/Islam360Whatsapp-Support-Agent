# Abuse Detection & Guardrails System - Implementation Summary

## ✅ Completed Implementation

A comprehensive abuse detection and guardrails system has been successfully integrated into the chatbot to detect and handle abusive language, profanity, harassment, and toxic behavior.

---

## 📁 Files Created

### Core Modules
1. **`src/guardrails/abuse_detector.py`**
   - Main abuse detection engine
   - Detects profanity, harassment, hate speech, and spam
   - Supports 4 severity levels: LOW, MEDIUM, HIGH, CRITICAL
   - Automatic escalation protocols
   - Integration with support ticket creation

2. **`src/guardrails/config.py`**
   - Centralized configuration for all guardrails
   - Customizable detection patterns
   - Sensitivity levels (0.0 to 1.0)
   - Response message templates
   - Violation thresholds and limits

3. **`src/guardrails/abuse_monitor.py`**
   - Incident logging and monitoring
   - User violation tracking
   - Session-level statistics
   - Report generation (user, session, system-wide)
   - JSON Lines file persistence
   - User blocking logic

### Documentation & Examples
4. **`GUARDRAILS.md`**
   - Comprehensive guardrails documentation
   - Configuration guide
   - API reference
   - Monitoring and analytics
   - Best practices and troubleshooting

5. **`ABUSE_DETECTION_INTEGRATION.py`**
   - Integration guide with code examples
   - Frontend integration examples
   - Configuration patterns
   - Testing instructions
   - Troubleshooting guide

6. **`examples/abuse_detection_examples.py`**
   - 9 complete examples demonstrating:
     - Basic abuse detection
     - Severity level classification
     - Custom configuration
     - Incident monitoring
     - User reports
     - System reports
     - Response messages
     - Detection patterns
     - Configuration options

### Testing & API
7. **`scripts/test_abuse_detection_api.py`**
   - Complete test suite for API endpoints
   - 7 different test scenarios
   - Validation of all new endpoints

---

## 📝 Files Modified

### 1. **`src/state.py`**
Added new fields to `AgentState`:
- `abuse_violation: bool` - Flag indicating if abuse was detected
- `abuse_type: str` - Type of abuse (profanity, harassment, etc.)
- `abuse_severity: str` - Severity level (low, medium, high, critical)
- `abuse_count: int` - Count of violations in current session

### 2. **`src/graph.py`**
- Added import for `abuse_detector_node`
- Registered `abuse_detector` as a graph node
- Updated graph architecture to include abuse detection in pipeline
- Positioned after `input_guardrail` and before `supervisor`

### 3. **`src/guardrails/input_guardrail.py`**
- Updated routing to point to `abuse_detector` instead of `supervisor`
- Changed return type annotation from `Literal["supervisor", "__end__"]` to `Literal["abuse_detector", "__end__"]`

### 4. **`src/guardrails/__init__.py`**
- Added exports for all abuse detection modules
- Public API includes:
  - `abuse_detector_node`
  - `detect_abuse`
  - Configuration classes
  - `AbuseMonitor` and `AbuseIncident`

### 5. **`api.py`**
Added 8 new API endpoints:
- `POST /abuse/detect` - Detect abuse in a message
- `GET /abuse/user/{user_id}` - Get user abuse report
- `GET /abuse/user/{user_id}/violations` - Get violation count
- `GET /abuse/user/{user_id}/status` - Quick user status
- `GET /abuse/session/{thread_id}` - Get session incidents
- `GET /abuse/system-report` - System-wide statistics
- `POST /abuse/check-and-flag` - Combined check and flag

Added Pydantic models:
- `AbuseDetectionResult`
- `UserAbuseReport`
- `SystemAbuseReport`

---

## 🎯 Key Features Implemented

### 1. Multi-Level Abuse Detection
- **Profanity Detection**: Common curse words and vulgar language
- **Harassment Detection**: Hostile, threatening, demeaning language
- **Hate Speech Detection**: Discriminatory and hateful content
- **Spam Detection**: Repetitive patterns and unusual character usage

### 2. Severity Classification
| Severity | Action | Response |
|----------|--------|----------|
| LOW | Warning | Gentle reminder to keep respectful |
| MEDIUM | Warning + Note | Professional request to rephrase |
| HIGH | Escalation + Ticket | Connect to human representative |
| CRITICAL | Termination + Ticket | Conversation terminated |

### 3. Automatic Escalation Protocols
- **LOW**: Continue conversation with warning
- **MEDIUM**: Support team notification
- **HIGH**: Create ticket, offer escalation
- **CRITICAL**: Create ticket, terminate conversation

### 4. User Tracking & Blocking
- Track violations per user across sessions
- Track violations per session
- Automatic user blocking after threshold exceeded
- Configurable blocking thresholds

### 5. Incident Logging & Monitoring
- JSON Lines file persistence (./logs/abuse_incidents/)
- User violation history
- Session-level statistics
- Comprehensive reporting
- System-wide analytics

### 6. Configurable Sensitivity
- Adjustable detection sensitivity (0.0 to 1.0)
- Custom bad words and patterns
- Whitelist patterns (exclude from detection)
- Custom harassment patterns

---

## 🔌 API Endpoints

### Detection
```bash
POST /abuse/detect?message=<text>
# Returns: {has_abuse, abuse_type, severity, violation_count}

POST /abuse/check-and-flag?user_id=<id>&thread_id=<id>&message=<text>
# Returns: {abuse_detected, abuse_type, severity, user_violations, session_violations, should_escalate, should_block, action_recommended}
```

### User Reports
```bash
GET /abuse/user/<user_id>
# Returns: {user_id, total_violations, severity_breakdown, type_breakdown, should_block, recent_incidents}

GET /abuse/user/<user_id>/violations?severity=<level>
# Returns: {user_id, violation_count, should_block}

GET /abuse/user/<user_id>/status
# Returns: {total_violations, should_block, recent_violation_types, latest_incident}
```

### Session Reports
```bash
GET /abuse/session/<thread_id>
# Returns: {thread_id, total_violations, incidents}
```

### System Reports
```bash
GET /abuse/system-report
# Returns: {total_incidents, unique_users, unique_sessions, severity_breakdown, type_breakdown}
```

---

## 🔧 Configuration Examples

### Enable/Disable Checks
```python
from src.guardrails.config import GuardrailConfig

GuardrailConfig.ENABLE_ABUSE_DETECTION = True
GuardrailConfig.PROFANITY_ENABLED = True
GuardrailConfig.HARASSMENT_ENABLED = True
GuardrailConfig.SPAM_ENABLED = True
```

### Adjust Sensitivity
```python
GuardrailConfig.PROFANITY_SENSITIVITY = 0.8  # 0.0-1.0
GuardrailConfig.HARASSMENT_SENSITIVITY = 0.7
GuardrailConfig.SPAM_SENSITIVITY = 0.6
```

### Blocking Thresholds
```python
GuardrailConfig.MAX_LOW_VIOLATIONS_PER_SESSION = 5
GuardrailConfig.MAX_MEDIUM_VIOLATIONS_PER_SESSION = 3
GuardrailConfig.MAX_HIGH_VIOLATIONS_PER_SESSION = 2
GuardrailConfig.MAX_CRITICAL_VIOLATIONS_PER_SESSION = 1
```

### Custom Words & Patterns
```python
GuardrailConfig.add_custom_bad_word("word")
GuardrailConfig.add_custom_harassment_pattern(r"pattern_regex")
GuardrailConfig.add_whitelist_pattern(r"pattern_to_exclude")
```

---

## 📊 Monitoring & Analytics

### User Report Example
```json
{
  "user_id": "user_123",
  "total_violations": 5,
  "severity_breakdown": {
    "low": 2,
    "medium": 1,
    "high": 1,
    "critical": 1
  },
  "type_breakdown": {
    "profanity": 3,
    "harassment": 2
  },
  "should_block": true,
  "incidents": [...]
}
```

### System Report Example
```json
{
  "total_incidents": 127,
  "unique_users": 45,
  "unique_sessions": 89,
  "severity_breakdown": {
    "low": 65,
    "medium": 35,
    "high": 20,
    "critical": 7
  },
  "type_breakdown": {
    "profanity": 72,
    "harassment": 38,
    "spam": 17
  }
}
```

---

## 🧪 Testing

### Run Examples
```bash
python examples/abuse_detection_examples.py
```

### Test API Endpoints
```bash
python scripts/test_abuse_detection_api.py
```

### Quick Test
```bash
# Test abuse detection
curl -X POST "http://127.0.0.1:8000/abuse/detect?message=This%20is%20damn%20bad"

# Get user status
curl "http://127.0.0.1:8000/abuse/user/test_user/status"

# Get system report
curl "http://127.0.0.1:8000/abuse/system-report"
```

---

## 📈 Graph Integration

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

Detection outcomes:
- **NO ABUSE**: Continue to supervisor
- **LOW/MEDIUM**: Warning, continue to supervisor
- **HIGH**: Create ticket, escalate to END
- **CRITICAL**: Create ticket, terminate, escalate to END

---

## 🔐 Security & Privacy

### Logging
- Incidents stored in `./logs/abuse_incidents/`
- JSON Lines format for easy processing
- Message preview truncated to 200 chars
- User ID and thread ID tracked

### Blocking
- Automatic user blocking after threshold
- Session-level blocking
- Support for manual review

### Configuration
- All settings centralized in `config.py`
- Easy to adjust for different use cases
- Whitelist support for exceptions

---

## 🚀 Next Steps

1. **Monitor System**: Review reports regularly
   ```bash
   curl http://127.0.0.1:8000/abuse/system-report
   ```

2. **Adjust Configuration**: Fine-tune based on false positives
   ```python
   # Lower sensitivity to reduce false positives
   GuardrailConfig.PROFANITY_SENSITIVITY = 0.6
   ```

3. **Add Custom Patterns**: Add domain-specific patterns
   ```python
   GuardrailConfig.add_custom_bad_word("domain_specific_word")
   ```

4. **Integrate with Frontend**: Add real-time validation
   ```javascript
   // Check message before sending
   const response = await fetch('/abuse/detect?message=' + message);
   const result = await response.json();
   if (result.has_abuse && result.severity === 'critical') {
     preventSending();
   }
   ```

5. **Train Support Team**: Educate on handling escalations

---

## 📚 Documentation Files

- **GUARDRAILS.md** - Complete guardrails documentation
- **ABUSE_DETECTION_INTEGRATION.py** - Integration guide with examples
- **examples/abuse_detection_examples.py** - 9 working examples
- **scripts/test_abuse_detection_api.py** - API endpoint tests

---

## ✨ System Status

✅ All components implemented and tested
✅ API endpoints fully functional
✅ Graph integration complete
✅ Monitoring and logging operational
✅ Documentation comprehensive
✅ Examples and tests provided

**The abuse detection guardrails system is ready for production use!**
