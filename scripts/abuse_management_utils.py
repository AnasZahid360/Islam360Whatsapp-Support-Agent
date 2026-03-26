#!/usr/bin/env python3
"""
Production Abuse Handling Guide & Utilities

Practical tools for managing abuse detection in a production environment.
"""

import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.guardrails.abuse_monitor import abuse_monitor
from src.guardrails.config import GuardrailConfig


class AbuseManagementUtilities:
    """Utilities for managing abuse in production."""
    
    @staticmethod
    def get_daily_summary(date: str = None) -> Dict[str, Any]:
        """
        Get daily abuse summary.
        
        Args:
            date: Date in format YYYY-MM-DD (defaults to today)
            
        Returns:
            Dictionary with daily statistics
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        log_file = Path(f"./logs/abuse_incidents/abuse_incidents_{date}.jsonl")
        
        if not log_file.exists():
            return {
                "date": date,
                "total_incidents": 0,
                "users": [],
                "types": {},
                "severities": {}
            }
        
        incidents = []
        with open(log_file) as f:
            for line in f:
                try:
                    incidents.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        
        users = set()
        types = {}
        severities = {}
        
        for incident in incidents:
            users.add(incident['user_id'])
            types[incident['abuse_type']] = types.get(incident['abuse_type'], 0) + 1
            severities[incident['severity']] = severities.get(incident['severity'], 0) + 1
        
        return {
            "date": date,
            "total_incidents": len(incidents),
            "unique_users": len(users),
            "type_breakdown": types,
            "severity_breakdown": severities,
            "high_severity_count": severities.get('high', 0) + severities.get('critical', 0),
            "incidents": incidents
        }
    
    @staticmethod
    def get_users_for_review(min_violations: int = 3) -> List[Dict[str, Any]]:
        """
        Get list of users that need review.
        
        Args:
            min_violations: Minimum number of violations to include
            
        Returns:
            List of users with violation summaries
        """
        users_to_review = []
        
        system_report = abuse_monitor.generate_system_report()
        
        for incident in system_report.get('incidents', []):
            user_id = incident.get('user_id')
            
            # Get user report
            user_report = abuse_monitor.generate_user_report(user_id)
            
            if user_report['total_violations'] >= min_violations:
                users_to_review.append({
                    "user_id": user_id,
                    "total_violations": user_report['total_violations'],
                    "should_block": user_report['should_block'],
                    "severity_breakdown": user_report['severity_breakdown'],
                    "type_breakdown": user_report['type_breakdown'],
                    "action": "BLOCK" if user_report['should_block'] else "MONITOR",
                })
        
        # Remove duplicates
        unique_users = {}
        for user_data in users_to_review:
            user_id = user_data['user_id']
            if user_id not in unique_users:
                unique_users[user_id] = user_data
        
        return sorted(
            unique_users.values(),
            key=lambda x: x['total_violations'],
            reverse=True
        )
    
    @staticmethod
    def export_report(output_file: str = None) -> str:
        """
        Export full abuse report to JSON file.
        
        Args:
            output_file: Output file path (defaults to timestamped file)
            
        Returns:
            Path to exported file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"./reports/abuse_report_{timestamp}.json"
        
        # Create reports directory
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Generate reports
        report = {
            "generated_at": datetime.now().isoformat(),
            "system_report": abuse_monitor.generate_system_report(),
            "daily_summary": AbuseManagementUtilities.get_daily_summary(),
            "users_for_review": AbuseManagementUtilities.get_users_for_review(min_violations=2),
        }
        
        # Write to file
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✓ Report exported to {output_file}")
        return output_file
    
    @staticmethod
    def print_dashboard():
        """Print a formatted dashboard of current abuse statistics."""
        report = abuse_monitor.generate_system_report()
        
        print("\n" + "="*70)
        print(" "*15 + "ABUSE DETECTION DASHBOARD")
        print("="*70)
        
        # Summary
        print(f"\n📊 SUMMARY")
        print(f"  Total Incidents: {report['total_incidents']}")
        print(f"  Unique Users: {report['unique_users']}")
        print(f"  Unique Sessions: {report['unique_sessions']}")
        
        # Severity
        print(f"\n🚨 SEVERITY BREAKDOWN")
        severities = report['severity_breakdown']
        total = sum(severities.values())
        for severity in ['critical', 'high', 'medium', 'low']:
            count = severities.get(severity, 0)
            percentage = (count / total * 100) if total > 0 else 0
            bar = "█" * int(percentage / 5)
            print(f"  {severity.upper():10} {count:3} incidents ({percentage:5.1f}%) {bar}")
        
        # Types
        print(f"\n🔍 TYPE BREAKDOWN")
        types = report['type_breakdown']
        for abuse_type in sorted(types.keys(), key=lambda x: types[x], reverse=True):
            count = types[abuse_type]
            percentage = (count / total * 100) if total > 0 else 0
            print(f"  {abuse_type.upper():15} {count:3} incidents ({percentage:5.1f}%)")
        
        # Users needing review
        print(f"\n👥 USERS NEEDING REVIEW")
        users_to_review = AbuseManagementUtilities.get_users_for_review(min_violations=2)
        if users_to_review:
            for i, user_data in enumerate(users_to_review[:10], 1):
                action = "🚫 BLOCK" if user_data['should_block'] else "⚠️  MONITOR"
                print(f"  {i:2}. {user_data['user_id']:20} {action:10} ({user_data['total_violations']} violations)")
        else:
            print("  No users requiring review")
        
        print("\n" + "="*70)
    
    @staticmethod
    def get_configuration_summary() -> Dict[str, Any]:
        """Get current configuration summary."""
        return {
            "abuse_detection_enabled": GuardrailConfig.ENABLE_ABUSE_DETECTION,
            "checks_enabled": {
                "profanity": GuardrailConfig.PROFANITY_ENABLED,
                "harassment": GuardrailConfig.HARASSMENT_ENABLED,
                "spam": GuardrailConfig.SPAM_ENABLED,
            },
            "sensitivity_levels": {
                "profanity": GuardrailConfig.PROFANITY_SENSITIVITY,
                "harassment": GuardrailConfig.HARASSMENT_SENSITIVITY,
                "spam": GuardrailConfig.SPAM_SENSITIVITY,
            },
            "violation_thresholds": {
                "low": GuardrailConfig.MAX_LOW_VIOLATIONS_PER_SESSION,
                "medium": GuardrailConfig.MAX_MEDIUM_VIOLATIONS_PER_SESSION,
                "high": GuardrailConfig.MAX_HIGH_VIOLATIONS_PER_SESSION,
                "critical": GuardrailConfig.MAX_CRITICAL_VIOLATIONS_PER_SESSION,
            },
            "escalation": {
                "auto_ticket_on_high": GuardrailConfig.AUTO_CREATE_TICKET_ON_HIGH,
                "auto_ticket_on_critical": GuardrailConfig.AUTO_CREATE_TICKET_ON_CRITICAL,
                "ticket_priority_high": GuardrailConfig.TICKET_PRIORITY_HIGH,
                "ticket_priority_critical": GuardrailConfig.TICKET_PRIORITY_CRITICAL,
            }
        }


# ============================================================================
# PRODUCTION WORKFLOWS
# ============================================================================

def workflow_daily_review():
    """Daily review workflow."""
    print("\n🔍 DAILY ABUSE REVIEW WORKFLOW\n")
    
    # Get daily summary
    daily = AbuseManagementUtilities.get_daily_summary()
    
    print(f"Date: {daily['date']}")
    print(f"Total Incidents: {daily['total_incidents']}")
    print(f"Unique Users: {daily['unique_users']}")
    print(f"High Severity: {daily['high_severity_count']}")
    
    if daily['total_incidents'] > 0:
        print("\nTop Abuse Types:")
        for abuse_type, count in sorted(daily['type_breakdown'].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {abuse_type}: {count}")
        
        print("\nSeverity Distribution:")
        for severity, count in daily['severity_breakdown'].items():
            print(f"  - {severity}: {count}")
    
    # Export report
    AbuseManagementUtilities.export_report()


def workflow_user_investigation(user_id: str):
    """Investigate a specific user."""
    print(f"\n🔎 INVESTIGATING USER: {user_id}\n")
    
    # Get user report
    report = abuse_monitor.generate_user_report(user_id)
    
    print(f"Total Violations: {report['total_violations']}")
    print(f"Should Block: {report['should_block']}")
    
    print("\nSeverity Breakdown:")
    for severity, count in report['severity_breakdown'].items():
        print(f"  - {severity}: {count}")
    
    print("\nType Breakdown:")
    for abuse_type, count in report['type_breakdown'].items():
        print(f"  - {abuse_type}: {count}")
    
    print("\nRecent Incidents:")
    for i, incident in enumerate(report['incidents'][-5:], 1):
        timestamp = incident.get('timestamp', 'N/A')
        severity = incident.get('severity', 'N/A')
        abuse_type = incident.get('abuse_type', 'N/A')
        preview = incident.get('message_preview', 'N/A')[:50]
        print(f"  {i}. [{severity.upper()}] {abuse_type}: {preview}...")
    
    # Recommendation
    if report['should_block']:
        print("\n⚠️  RECOMMENDATION: BLOCK USER")
    else:
        print(f"\n📌 RECOMMENDATION: MONITOR (Violations: {report['total_violations']})")


def workflow_adjust_sensitivity(new_profanity_sensitivity: float):
    """Adjust detection sensitivity."""
    print(f"\n⚙️  ADJUSTING SENSITIVITY\n")
    
    old_value = GuardrailConfig.PROFANITY_SENSITIVITY
    GuardrailConfig.PROFANITY_SENSITIVITY = new_profanity_sensitivity
    
    print(f"Profanity Sensitivity: {old_value} → {new_profanity_sensitivity}")
    print("✓ Configuration updated")


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Main CLI interface."""
    import sys
    
    if len(sys.argv) < 2:
        print("\n📋 ABUSE MANAGEMENT UTILITIES\n")
        print("Usage: python scripts/abuse_management_utils.py <command> [args]\n")
        print("Commands:")
        print("  dashboard              - Show abuse statistics dashboard")
        print("  daily-review           - Run daily review workflow")
        print("  investigate <user_id>  - Investigate specific user")
        print("  export [file]          - Export full report")
        print("  config                 - Show current configuration")
        print("  users-review           - List users needing review")
        return
    
    command = sys.argv[1]
    
    if command == "dashboard":
        AbuseManagementUtilities.print_dashboard()
    
    elif command == "daily-review":
        workflow_daily_review()
    
    elif command == "investigate":
        if len(sys.argv) < 3:
            print("Error: User ID required")
            return
        user_id = sys.argv[2]
        workflow_user_investigation(user_id)
    
    elif command == "export":
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        AbuseManagementUtilities.export_report(output_file)
    
    elif command == "config":
        config = AbuseManagementUtilities.get_configuration_summary()
        print(json.dumps(config, indent=2))
    
    elif command == "users-review":
        users = AbuseManagementUtilities.get_users_for_review()
        if users:
            print("\n👥 USERS NEEDING REVIEW:\n")
            for user in users:
                action = "🚫 BLOCK" if user['should_block'] else "⚠️  MONITOR"
                print(f"  {user['user_id']:20} {action:10} ({user['total_violations']} violations)")
        else:
            print("No users needing review")
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
