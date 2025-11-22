"""
State management for incident response system.
Tracks conversation history, triggered rules, and incident status.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os
from rule import Rule


@dataclass
class ToolCall:
    """Represents a single tool call in the conversation history"""
    tool_name: str
    arguments: Dict[str, Any]
    result: str
    timestamp: Optional[str] = None


@dataclass
class IncidentState:
    """
    Maintains state for the incident response system.
    
    This is used as the Context type for OpenAI Agents SDK.
    """
    # Rule configuration
    all_rules: List[Rule] = field(default_factory=list)
    
    # ⭐ Eradication: Learned rules from past incidents
    learned_rules: List[Rule] = field(default_factory=list)
    # Store learned rules in ResponseSpec DSL format, similar to rules.txt
    learned_rules_db_path: str = "learned_rules.txt"
    
    # Conversation tracking
    tool_call_history: List[ToolCall] = field(default_factory=list)
    last_tool_called: Optional[str] = None
    
    # Turn-level state (reset after each turn)
    triggered_rules_current_turn: List[Rule] = field(default_factory=list)
    detection_done_for_current_turn: bool = False
    
    # Temporary storage for current tool call arguments
    current_tool_arguments: Dict[str, Any] = field(default_factory=dict)
    
    # Session reference for accessing conversation history
    session: Optional[Any] = None
    
    # Incident detection
    incident_detected: bool = False
    incident_occurred: bool = False
    incident_description: str = ""
    triggered_rule_id: str = ""
    severity: str = ""  # low, medium, high, critical
    
    # Remediation
    remediation_action: str = ""
    remediation_in_progress: bool = False
    remediation_completed: bool = False
    remediation_steps_completed: List[str] = field(default_factory=list)
    incident_history_length_at_detection: int = 0
    
    # ⭐ Eradication: Pending eradication details (to be executed after remediation)
    pending_eradication: Optional[Dict[str, Any]] = None
    
    # Detection state
    detection_done_for_current_turn: bool = False
    
    def add_tool_call(self, tool_name: str, arguments: Dict[str, Any], result: str):
        """Record a tool call in the history"""
        self.tool_call_history.append(
            ToolCall(
                tool_name=tool_name,
                arguments=arguments,
                result=result
            )
        )
        self.last_tool_called = tool_name
    
    def get_triggered_rules_for_tool(self, tool_name: str) -> List[Rule]:
        """Get all rules triggered by a specific tool"""
        return [
            rule for rule in self.all_rules 
            if rule.triggered_by_tool(tool_name)
        ]
    
    def set_incident(
        self, 
        rule_id: str, 
        description: str, 
        remediation: str,
        severity: str = "medium"
    ):
        """Mark an incident as detected"""
        self.incident_detected = True
        self.incident_occurred = True
        self.triggered_rule_id = rule_id
        self.incident_description = description
        self.remediation_action = remediation
        self.severity = severity
        self.remediation_in_progress = True
        self.incident_history_length_at_detection = len(self.tool_call_history)
    
    def clear_incident(self):
        """Clear incident state after remediation"""
        self.incident_detected = False
        self.incident_description = ""
        self.triggered_rule_id = ""
        self.remediation_action = ""
        self.remediation_in_progress = False
        self.remediation_completed = False
        self.remediation_steps_completed = []
        self.incident_history_length_at_detection = 0
    
    def reset_turn_state(self):
        """Reset state for a new turn"""
        self.triggered_rules_current_turn = []
        self.detection_done_for_current_turn = False
    
    def get_recent_history(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get the last n tool calls as a list of dicts"""
        recent = self.tool_call_history[-n:] if len(self.tool_call_history) > n else self.tool_call_history
        return [
            {
                "tool": call.tool_name,
                "arguments": call.arguments,
                "result": call.result
            }
            for call in recent
        ]
    
    def get_history_by_tool(self, tool_name: str, n: int = 10) -> List[Dict[str, Any]]:
        """
        Get the last n calls of a specific tool.
        Useful for detecting patterns in repeated tool usage.
        
        Note: Currently not used by the framework, but available for custom detection logic.
        
        Args:
            tool_name: Name of the tool to filter
            n: Maximum number of calls to return
            
        Returns:
            List of tool call dicts for the specified tool
        """
        filtered = [
            {
                "tool": call.tool_name,
                "arguments": call.arguments,
                "result": call.result
            }
            for call in self.tool_call_history
            if call.tool_name == tool_name
        ]
        return filtered[-n:] if len(filtered) > n else filtered
    
    def get_extended_history(self, n: int = 20) -> List[Dict[str, Any]]:
        """
        Get extended history for long-chain operation detection.
        
        Note: Currently not used by the framework, but available for custom detection logic.
        
        Args:
            n: Number of recent tool calls (default: 20 for long chains)
            
        Returns:
            List of tool call dicts
        """
        recent = self.tool_call_history[-n:] if len(self.tool_call_history) > n else self.tool_call_history
        return [
            {
                "tool": call.tool_name,
                "arguments": call.arguments,
                "result": call.result
            }
            for call in recent
        ]
    
    # ========================================
    # ⭐ Eradication: Learned Rules Management
    # ========================================
    
    def load_learned_rules(self):
        """Load learned rules from persistent storage (DSL file)."""
        if os.path.exists(self.learned_rules_db_path):
            try:
                # Reuse the same parser as rules.txt
                rules = Rule.from_file(self.learned_rules_db_path)
                # Mark them as learned rules (for logging / UI semantics)
                for r in rules:
                    r.is_learned = True
                self.learned_rules.extend(rules)
                print(
                    f"[Eradication] Loaded {len(self.learned_rules)} learned rules "
                    f"from {self.learned_rules_db_path}"
                )
            except Exception as e:
                print(f"[Eradication] Error loading learned rules from DSL: {e}")
        else:
            print(f"[Eradication] No learned rules file found at {self.learned_rules_db_path}")
    
    def save_learned_rule(self, rule: Rule):
        """Save a single learned rule to persistent storage (DSL file)."""
        # Append a DSL-style rule to learned_rules.txt using rules.txt format.
        # The file path is learned_rules_db_path.
        try:
            with open(self.learned_rules_db_path, 'a', encoding='utf-8') as f_txt:
                f_txt.write(
                    f"rule @{rule.id}\n"
                    f"trigger \n"
                    f"    \"{rule.trigger_tool}\"\n"
                    f"check\n"
                    f"    \"{rule.incident_condition}\"\n"
                    f"orchestrate\n"
                    f"    \"{rule.remediation_action}\"\n"
                    f"end\n\n\n"
                )
            print(f"[Eradication] Saved learned rule (DSL): {rule.id}")
        except Exception as e:
            print(f"[Eradication] Warning: failed to write {self.learned_rules_db_path} for {rule.id}: {e}")
    
    def add_learned_rule(self, rule: Rule):
        """Add a learned rule to the state and save it"""
        self.learned_rules.append(rule)
        self.save_learned_rule(rule)
    
    def get_learned_rules_for_tool(self, tool_name: str) -> List[Rule]:
        """Get all learned rules for a specific tool"""
        return [r for r in self.learned_rules if r.trigger_tool == tool_name]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization"""
        return {
            "incident_detected": self.incident_detected,
            "incident_description": self.incident_description,
            "triggered_rule_id": self.triggered_rule_id,
            "severity": self.severity,
            "remediation_action": self.remediation_action,
            "remediation_completed": self.remediation_completed,
            "tool_call_count": len(self.tool_call_history),
            "last_tool": self.last_tool_called
        }
