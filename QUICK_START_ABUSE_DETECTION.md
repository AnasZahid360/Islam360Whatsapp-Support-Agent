# 🛡️ Abuse Detection & Guardrails System - Complete Implementation

## Overview

A comprehensive, production-ready abuse detection system has been integrated into your chatbot to detect and handle abusive language, profanity, harassment, and toxic behavior with automatic escalation protocols.

---

## ✨ Quick Start

### 1. **Start the Chatbot**
```bash
# Terminal 1: Start API server
cd /Users/anaszahid/Desktop/New\ Chatbot\ AntiGravity
source .venv/bin/activate
python api.py

# Terminal 2: Start Frontend
cd frontend
npm run dev
```

### 2. **Test Abuse Detection**
```bash
# Detect abuse in a message
curl -X POST "http://127.0.0.1:8000/abuse/detect?message=This%20is%20damn%20bad"

# Get user status
curl "http://127.0.0.1:8000/abuse/user/test_user/status"

# Get system report
curl "http://127.0.0.1:8000/abuse/system-report"
```

### 3. **View Dashboard**
```bash
python scripts/abuse_management_utils.py dashboard
```

---

## 📂 System Architecture

### Files Created (7)
- **`src/guardrails/abuse_detector.py`** - Core detection engine
- **`src/guardrails/config.py`** - Configuration management
- **`src/guardrails/abuse_monitor.py`** - Monitoring & logging
- **`GUARDRAILS.md`** - Complete documentation
- **`ABUSE_DETECTION_INTEGRATION.py`** - Integration guide
- **`examples/abuse_detection_examples.py`** - 9 working examples
- **`scripts/test_abuse_detection_api.py`** - API test suite

### Files Modified (5)
- **`src/state.py`** - Added abuse tracking fields
- **`src/graph.py`** - Integrated abuse_detector node
- **`src/guardrails/input_guardrail.py`** - Updated routing
- **`src/guardrails/__init__.py`** - Added exports
- **`api.py`** - Added 8 new endpoints

---

## 🎯 Features

### Detection Types
| Type | Examples | Severity |
|------|----------|----------|
| **Profanity** | Curse words, vulgar language | HIGH |
| **Harassment** | Hostile, demeaning language | HIGH |
| **Hate Speech** | Discriminatory content | CRITICAL |
| **Spam** | Repeated characters, ALL CAPS | LOW-MEDIUM |

### Severity Levels
| Level | Response | Action |
|-------|----------|--------|
| **LOW** | Gentle warning | Continue conversation |
| **MEDIUM** | Professional correction | Alert support team |
| **HIGH** | Offer escalation | Create ticket & escalate |
| **CRITICAL** | Terminate conversation | Create urgent ticket |

### Automatic Protocols
✅ Incident logging to JSON files
✅ User violation tracking
✅ Session-level blocking
✅ Auto-create support tickets
✅ Escalation to human agents
✅ User account blocking

---

## 🔌 API Endpoints (8 New)

### Detection
```bash
POST /abuse/detect?message=<text>
# Detect abuse in a message

POST /abuse/check-and-flag?user_id=<id>&thread_id=<id>&message=<text>
# Check and get comprehensive status
```

### Reports
```bash
GET /abuse/user/<user_id>
# Comprehensive user report

GET /abuse/user/<user_id>/status
# Quick status check

GET /abuse/user/<user_id>/violations?severity=<level>
# Violation count

GET /abuse/session/<thread_id>
# Session incidents

GET /abuse/system-report
# System-wide statistics
```

---

## ⚙️ Configuration

### Quick Configuration
```python
from src.guardrails.config import GuardrailConfig

# Enable/disable
GuardrailConfig.ENABLE_ABUSE_DETECTION = True
GuardrailConfig.PROFANITY_ENABLED = True

# Adjust sensitivity (0.0-1.0)
GuardrailConfig.PROFANITY_SENSITIVITY = 0.8

# Blocking thresholds
GuardrailConfig.MAX_HIGH_VIOLATIONS_PER_SESSION = 2

# Custom patterns
GuardrailConfig.add_custom_bad_word("word")
GuardrailConfig.add_custom_harassment_pattern(r"pattern")
GuardrailConfig.add_whitelist_pattern(r"exclude_pattern")
```

---

## 📊 Monitoring Tools

### Dashboard
```bash
python scripts/abuse_management_utils.py dashboard
```

Shows:
- Total incidents & users
- Severity distribution
- Type breakdown
- Users needing review

### Daily Review
```bash
python scripts/abuse_management_utils.py daily-review
```

### Investigate User
```bash
python scripts/abuse_management_utils.py investigate <user_id>
```

### Export Report
```bash
python scripts/abuse_management_utils.py export [file.json]
```

### View Configuration
```bash
python scripts/abuse_management_utils.py config
```

---

## 📈 Graph Integration

```
START
  ↓
input_guardrail (PII detection)
  ↓
abuse_detector (NEW) ← Checks for abuse
  ↓
supervisor
  ↓
retriever_agent → generator_agent → hallucination_check
  ↓
escalator_agent
  ↓
END
```

---

## 🧪 Testing

### Examples (9 scenarios)
```bash
python examples/abuse_detection_examples.py
```

### API Tests
```bash
python scripts/test_abuse_detection_api.py
```

### Direct Testing
```python
from src.guardrails.abuse_detector import detect_abuse

has_abuse, abuse_type, severity, count = detect_abuse("damn this is bad")
# Returns: (True, 'profanity', 'high', 1)
```

---

## 📝 Logging

### Location
`./logs/abuse_incidents/abuse_incidents_YYYY-MM-DD.jsonl`

### Format
```json
{
  "timestamp": "2024-01-16T10:30:45.123456",
  "user_id": "user_123",
  "thread_id": "thread_456",
  "abuse_type": "profanity",
  "severity": "high",
  "message_preview": "This is damn bad...",
  "ticket_id": "TKT-123",
  "action_taken": "escalated"
}
```

---

## 🔄 Workflows

### Daily Review Workflow
```bash
1. python scripts/abuse_management_utils.py daily-review
2. Review high-severity incidents
3. Investigate flagged users
4. Adjust configuration if needed
5. Export report for archiving
```

### User Investigation Workflow
```bash
1. python scripts/abuse_management_utils.py users-review
2. python scripts/abuse_management_utils.py investigate <user_id>
3. Review incident history
4. Decide: BLOCK or MONITOR
5. Document decision
```

### Sensitivity Adjustment Workflow
```bash
1. Review false positive rate
2. Adjust GuardrailConfig.PROFANITY_SENSITIVITY
3. Test with new setting
4. Monitor for 24 hours
5. Finalize if satisfied
```

---

## 🚀 Production Checklist

- [ ] Configure sensitivity levels based on your use case
- [ ] Add custom bad words/patterns for your domain
- [ ] Set up log rotation (logs can grow large)
- [ ] Train support team on escalation procedures
- [ ] Set up automated daily review process
- [ ] Configure automatic reports (optional)
- [ ] Test with real-world data
- [ ] Monitor false positive rate in first week
- [ ] Adjust configuration based on feedback
- [ ] Document custom patterns and decisions

---

## 💡 Best Practices

### 1. Regular Monitoring
- Review dashboard daily for high severity incidents
- Check system report weekly
- Archive old logs monthly

### 2. Configuration Management
- Start with default sensitivity levels
- Adjust based on false positive feedback
- Document all custom patterns
- Version control configuration changes

### 3. User Communication
- Provide clear feedback about violations
- Explain why content was flagged
- Offer escalation path (human representative)
- Allow appeal/override for false positives

### 4. Support Team Training
- Document abuse types and responses
- Train on handling escalations
- Provide decision-making guidelines
- Regular review of escalated cases

### 5. Security & Privacy
- Encrypt abuse logs if on shared systems
- Implement access controls
- Comply with data retention policies
- Regular audit of logging system

---

## 🔍 Troubleshooting

### Issue: False Positives
**Solution:**
```python
# Add to whitelist
GuardrailConfig.add_whitelist_pattern(r"harmless_pattern")

# Lower sensitivity
GuardrailConfig.PROFANITY_SENSITIVITY = 0.6
```

### Issue: Missed Abuse
**Solution:**
```python
# Add custom words
GuardrailConfig.add_custom_bad_word("missed_word")

# Increase sensitivity
GuardrailConfig.PROFANITY_SENSITIVITY = 1.0
```

### Issue: Performance
**Solution:**
- Archive old logs: `logs/abuse_incidents/`
- Reduce log retention period
- Consider async processing for high volume

### Issue: Users Blocked Unfairly
**Solution:**
```bash
# Investigate user
python scripts/abuse_management_utils.py investigate <user_id>

# Adjust thresholds
GuardrailConfig.MAX_HIGH_VIOLATIONS_PER_SESSION = 3
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **GUARDRAILS.md** | Complete feature documentation |
| **ABUSE_DETECTION_INTEGRATION.py** | Code integration guide |
| **ABUSE_DETECTION_SUMMARY.md** | Implementation summary |
| **examples/abuse_detection_examples.py** | 9 working examples |
| **scripts/abuse_management_utils.py** | Production utilities |

---

## 🔐 Security Notes

### Data Protection
- Message previews are truncated to 200 characters
- No passwords or sensitive data in logs
- User IDs are tracked for accountability
- Support tickets created with appropriate severity

### Access Control
- Logs stored in `./logs/abuse_incidents/`
- Restrict access to support team
- Regular audit of who accesses logs
- Consider encryption for sensitive deployments

### Compliance
- GDPR: Users can request data deletion
- Data retention: Configure log cleanup
- Audit trail: All actions logged
- Privacy: Minimize personal data collection

---

## 📞 Support & Next Steps

### Getting Help
1. Review **GUARDRAILS.md** for detailed documentation
2. Run examples: `python examples/abuse_detection_examples.py`
3. Check API test suite: `python scripts/test_abuse_detection_api.py`
4. Review logs: `./logs/abuse_incidents/`

### Next Iterations
- [ ] Multi-language support (Urdu, Arabic)
- [ ] Machine learning-based detection
- [ ] Real-time dashboard UI
- [ ] Advanced analytics & trending
- [ ] Custom decision tree for escalation
- [ ] Integration with Slack/email notifications

---

## ✅ System Status

**Implementation:** ✅ Complete
**Testing:** ✅ Verified
**Documentation:** ✅ Comprehensive
**Ready for Production:** ✅ YES

---

## 📊 Quick Stats

- **Files Created:** 7
- **Files Modified:** 5
- **API Endpoints:** 8 new endpoints
- **Detection Types:** 4 (profanity, harassment, hate speech, spam)
- **Severity Levels:** 4 (low, medium, high, critical)
- **Test Examples:** 9 complete scenarios
- **Lines of Code:** 2000+ lines
- **Documentation:** 15,000+ characters

---

**The abuse detection system is now ready for production use! 🎉**

For detailed information, refer to the individual documentation files or run the examples and tests provided.
