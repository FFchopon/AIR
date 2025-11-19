"""
ResponseSpec - Incident Response DSL for OpenAI Agents SDK

A framework for defining and enforcing incident response rules in agent systems.
"""

from .rule import Rule
from .state import IncidentState, ToolCall
from .interpreter import RuleInterpreter, IncidentDetector
from .response import ResponseOrchestrator
from .openai_integration import IncidentDetectionHooks, format_rules_for_prompt
from .tools import check_for_incidents, mark_remediation_complete, get_incident_status, configure_detector
from .agent_factory import create_safe_agent, create_safe_agent_with_custom_instructions

__version__ = "0.1.0"

__all__ = [
    # Core components
    "Rule",
    "IncidentState",
    "ToolCall",
    "RuleInterpreter",
    "IncidentDetector",
    "ResponseOrchestrator",
    
    # OpenAI Agents SDK integration
    "IncidentDetectionHooks",
    "format_rules_for_prompt",
    
    # Tools
    "check_for_incidents",
    "mark_remediation_complete",
    "get_incident_status",
    "configure_detector",
    
    # Factory functions
    "create_safe_agent",
    "create_safe_agent_with_custom_instructions",
]
