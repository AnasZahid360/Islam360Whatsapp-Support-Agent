"""
Abuse incident monitoring and logging.

This module tracks and logs abuse incidents, maintains user violation history,
and provides analytics on abuse patterns.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class AbuseIncident:
    """Represents a single abuse incident."""
    timestamp: str
    user_id: str
    thread_id: str
    abuse_type: str
    severity: str
    message_preview: str
    ticket_id: Optional[str] = None
    action_taken: str = "logged"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class AbuseMonitor:
    """
    Monitors and tracks abuse incidents across conversations.
    """
    
    def __init__(self, log_dir: str = "./logs/abuse_incidents"):
        """
        Initialize the abuse monitor.
        
        Args:
            log_dir: Directory to store abuse incident logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory tracking of user violations
        self.user_violations: Dict[str, List[AbuseIncident]] = {}
        self.session_violations: Dict[str, List[AbuseIncident]] = {}
        
        # Load existing logs
        self._load_existing_logs()
    
    def log_incident(self, incident: AbuseIncident) -> None:
        """
        Log an abuse incident.
        
        Args:
            incident: The abuse incident to log
        """
        # Add to in-memory tracking
        if incident.user_id not in self.user_violations:
            self.user_violations[incident.user_id] = []
        self.user_violations[incident.user_id].append(incident)
        
        if incident.thread_id not in self.session_violations:
            self.session_violations[incident.thread_id] = []
        self.session_violations[incident.thread_id].append(incident)
        
        # Write to file
        self._write_incident_to_log(incident)
        
        print(f"📋 Abuse incident logged: {incident.abuse_type} ({incident.severity})")
    
    def get_user_violation_count(self, user_id: str, severity: Optional[str] = None) -> int:
        """
        Get the count of violations for a user.
        
        Args:
            user_id: The user ID
            severity: Optional severity filter
            
        Returns:
            Number of violations
        """
        if user_id not in self.user_violations:
            return 0
        
        violations = self.user_violations[user_id]
        
        if severity:
            violations = [v for v in violations if v.severity == severity]
        
        return len(violations)
    
    def get_session_violation_count(self, thread_id: str, severity: Optional[str] = None) -> int:
        """
        Get the count of violations in a session.
        
        Args:
            thread_id: The thread ID
            severity: Optional severity filter
            
        Returns:
            Number of violations
        """
        if thread_id not in self.session_violations:
            return 0
        
        violations = self.session_violations[thread_id]
        
        if severity:
            violations = [v for v in violations if v.severity == severity]
        
        return len(violations)
    
    def get_user_violations(self, user_id: str) -> List[AbuseIncident]:
        """
        Get all violations for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            List of abuse incidents
        """
        return self.user_violations.get(user_id, [])
    
    def get_session_violations(self, thread_id: str) -> List[AbuseIncident]:
        """
        Get all violations in a session.
        
        Args:
            thread_id: The thread ID
            
        Returns:
            List of abuse incidents
        """
        return self.session_violations.get(thread_id, [])
    
    def should_block_user(self, user_id: str, max_violations: int = 5) -> bool:
        """
        Check if a user should be blocked from further interactions.
        
        Args:
            user_id: The user ID
            max_violations: Maximum allowed violations before blocking
            
        Returns:
            True if user should be blocked
        """
        violation_count = self.get_user_violation_count(user_id)
        return violation_count >= max_violations
    
    def should_escalate_to_human(self, thread_id: str) -> bool:
        """
        Check if a thread should be escalated to human due to repeated abuse.
        
        Args:
            thread_id: The thread ID
            
        Returns:
            True if escalation is warranted
        """
        violations = self.get_session_violations(thread_id)
        
        # Escalate if more than 2 violations in same session
        if len(violations) > 2:
            return True
        
        # Escalate if any critical violations
        critical_count = sum(1 for v in violations if v.severity == "critical")
        if critical_count > 0:
            return True
        
        return False
    
    def generate_user_report(self, user_id: str) -> Dict:
        """
        Generate a report for a user's abuse history.
        
        Args:
            user_id: The user ID
            
        Returns:
            Dictionary containing user report
        """
        violations = self.get_user_violations(user_id)
        
        severity_counts = {
            "low": sum(1 for v in violations if v.severity == "low"),
            "medium": sum(1 for v in violations if v.severity == "medium"),
            "high": sum(1 for v in violations if v.severity == "high"),
            "critical": sum(1 for v in violations if v.severity == "critical"),
        }
        
        type_counts = {}
        for v in violations:
            type_counts[v.abuse_type] = type_counts.get(v.abuse_type, 0) + 1
        
        return {
            "user_id": user_id,
            "total_violations": len(violations),
            "severity_breakdown": severity_counts,
            "type_breakdown": type_counts,
            "incidents": [v.to_dict() for v in violations],
            "should_block": self.should_block_user(user_id),
        }
    
    def generate_system_report(self) -> Dict:
        """
        Generate a system-wide report of abuse incidents.
        
        Returns:
            Dictionary containing system report
        """
        all_incidents = []
        for incidents in self.user_violations.values():
            all_incidents.extend(incidents)
        
        severity_counts = {
            "low": sum(1 for v in all_incidents if v.severity == "low"),
            "medium": sum(1 for v in all_incidents if v.severity == "medium"),
            "high": sum(1 for v in all_incidents if v.severity == "high"),
            "critical": sum(1 for v in all_incidents if v.severity == "critical"),
        }
        
        type_counts = {}
        for v in all_incidents:
            type_counts[v.abuse_type] = type_counts.get(v.abuse_type, 0) + 1
        
        return {
            "total_incidents": len(all_incidents),
            "unique_users": len(self.user_violations),
            "unique_sessions": len(self.session_violations),
            "severity_breakdown": severity_counts,
            "type_breakdown": type_counts,
            "incidents": [v.to_dict() for v in all_incidents[-100:]],  # Last 100
        }
    
    def _write_incident_to_log(self, incident: AbuseIncident) -> None:
        """Write an incident to log file."""
        log_file = self.log_dir / f"abuse_incidents_{incident.timestamp.split('T')[0]}.jsonl"
        
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(incident.to_dict()) + "\n")
        except Exception as e:
            print(f"⚠️  Failed to write abuse log: {e}")
    
    def _load_existing_logs(self) -> None:
        """Load existing abuse logs from disk."""
        try:
            for log_file in self.log_dir.glob("abuse_incidents_*.jsonl"):
                with open(log_file, "r") as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            incident = AbuseIncident(**data)
                            
                            if incident.user_id not in self.user_violations:
                                self.user_violations[incident.user_id] = []
                            self.user_violations[incident.user_id].append(incident)
                            
                            if incident.thread_id not in self.session_violations:
                                self.session_violations[incident.thread_id] = []
                            self.session_violations[incident.thread_id].append(incident)
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            print(f"⚠️  Error loading abuse logs: {e}")


# Global abuse monitor instance
abuse_monitor = AbuseMonitor()
