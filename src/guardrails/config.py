"""
Guardrails configuration and settings.

This module contains configuration for all guardrail systems including
PII detection, abuse detection, hallucination checking, etc.
"""

from enum import Enum
from typing import Set, Dict, List


class AbuseLevel(Enum):
    """Enumeration of abuse severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GuardrailConfig:
    """
    Central configuration for all guardrails.
    """
    
    # Enable/disable specific guardrails
    ENABLE_PII_DETECTION = True
    ENABLE_ABUSE_DETECTION = True
    ENABLE_INJECTION_DETECTION = True
    ENABLE_HALLUCINATION_CHECK = True
    ENABLE_SPAM_DETECTION = True
    
    # Abuse detection settings
    ABUSE_DETECTION_ENABLED = True
    PROFANITY_ENABLED = True
    HARASSMENT_ENABLED = True
    SPAM_ENABLED = True
    
    # Sensitivity levels (0.0 to 1.0)
    PROFANITY_SENSITIVITY = 0.8  # High sensitivity
    HARASSMENT_SENSITIVITY = 0.7  # Medium-high sensitivity
    SPAM_SENSITIVITY = 0.6  # Medium sensitivity
    
    # Severity thresholds
    # Number of violations before escalating to next level
    LOW_TO_MEDIUM_THRESHOLD = 2
    MEDIUM_TO_HIGH_THRESHOLD = 1
    HIGH_TO_CRITICAL_THRESHOLD = 0  # Immediate critical on high
    
    # Response templates
    LOW_SEVERITY_WARNING = (
        "I appreciate your question, but I'd like to keep our conversation respectful. "
        "Let's focus on how I can help you with your support needs. How can I assist you today?"
    )
    
    MEDIUM_SEVERITY_WARNING = (
        "I understand you may be frustrated, but I need to ask that we keep our conversation professional. "
        "I'm here to help resolve your issue. Please rephrase your question and I'll do my best to assist."
    )
    
    HIGH_SEVERITY_ESCALATION = (
        "I'm concerned about the language in your message. "
        "I'm here to help you professionally, but I need us to communicate respectfully. "
        "A support ticket has been created so our team can assist you further. "
        "Would you like to connect with a human representative?"
    )
    
    CRITICAL_SEVERITY_TERMINATION = (
        "I'm unable to continue this conversation due to abusive language. "
        "Our support team has been notified and will contact you. "
        "If you'd like to continue, please ensure your communication is respectful."
    )
    
    # Tracking and logging
    LOG_VIOLATIONS = True
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
    
    # Escalation protocol
    AUTO_CREATE_TICKET_ON_HIGH = True
    AUTO_CREATE_TICKET_ON_CRITICAL = True
    TICKET_PRIORITY_HIGH = "HIGH"
    TICKET_PRIORITY_CRITICAL = "URGENT"
    
    # Rate limiting for same user
    TRACK_USER_VIOLATIONS = True
    MAX_LOW_VIOLATIONS_PER_SESSION = 5
    MAX_MEDIUM_VIOLATIONS_PER_SESSION = 3
    MAX_HIGH_VIOLATIONS_PER_SESSION = 2
    MAX_CRITICAL_VIOLATIONS_PER_SESSION = 1
    
    # Whitelist patterns (if a message matches, skip abuse detection)
    WHITELIST_PATTERNS: Set[str] = set()
    
    # Custom bad words (in addition to built-in list)
    CUSTOM_BAD_WORDS: Set[str] = set()
    
    # Custom harassment patterns
    CUSTOM_HARASSMENT_PATTERNS: Set[str] = set()
    
    @classmethod
    def add_custom_bad_word(cls, word: str):
        """Add a custom bad word to the detection list."""
        cls.CUSTOM_BAD_WORDS.add(word.lower())
    
    @classmethod
    def add_custom_harassment_pattern(cls, pattern: str):
        """Add a custom harassment pattern."""
        cls.CUSTOM_HARASSMENT_PATTERNS.add(pattern)
    
    @classmethod
    def add_whitelist_pattern(cls, pattern: str):
        """Add a pattern to whitelist (skip detection)."""
        cls.WHITELIST_PATTERNS.add(pattern)
    
    @classmethod
    def get_severity_action(cls, severity: str) -> str:
        """Get the action to take for a given severity level."""
        actions = {
            "low": "warning",
            "medium": "warning_with_note",
            "high": "escalate_immediately",
            "critical": "escalate_immediately_terminate",
        }
        return actions.get(severity, "warning")
    
    @classmethod
    def get_response_for_severity(cls, severity: str) -> str:
        """Get the response message for a given severity level."""
        responses = {
            "low": cls.LOW_SEVERITY_WARNING,
            "medium": cls.MEDIUM_SEVERITY_WARNING,
            "high": cls.HIGH_SEVERITY_ESCALATION,
            "critical": cls.CRITICAL_SEVERITY_TERMINATION,
        }
        return responses.get(severity, cls.LOW_SEVERITY_WARNING)


class ABUSEDetectionConfig:
    """Configuration specific to abuse detection."""
    
    # Built-in patterns
    PROFANITY_PATTERNS = [
        r'\b(damn|dammit|hell|crap|ass|asshole|bitch|bastard|shit|piss|fuck|f\*ck|f\*\*k)\b',
        r'\b(arse|arsehole|bollocks|bugger|cock|dickhead|git|pillock|twat|wanker|tit|tosser)\b',
    ]
    
    HARASSMENT_PATTERNS = [
        r'(you\s+suck|you\s+are\s+terrible|i\s+hate\s+you)',
        r'(get\s+fucked|fuck\s+off|fuck\s+you|go\s+fuck)',
        r'(loser|pathetic|worthless|scum)',
        r'(racist|sexist|homophobic|islamophobic|antisemitic)',
    ]
    
    HATE_SPEECH_PATTERNS = [
        r'\b(retard|retarded|idiot|stupid|dumb|moron|imbecile)\b',
        r'(kill\s+(yourself|you|me)|kys|go\s+die|hope\s+you\s+die)',
        r'(beat\s+you|punch\s+you|stab|shoot\s+you|rape)',
    ]
    
    SPAM_PATTERNS = [
        r'(.)\1{5,}',  # Repeated characters
        r'([A-Z]){4,}\s+([A-Z]){4,}',  # ALL CAPS
    ]
    
    # Severity mapping
    SEVERITY_MAP = {
        "profanity": "high",
        "harassment": "high",
        "hate_speech": "critical",
        "spam": "low",
    }
    
    # Languages to support (for future expansion)
    SUPPORTED_LANGUAGES = ["en", "ur", "ar"]  # English, Urdu, Arabic


# Global guardrails configuration instance
guardrails_config = GuardrailConfig()
abuse_config = ABUSEDetectionConfig()
