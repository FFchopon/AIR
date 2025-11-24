"""
OpenAI Agents SDK integration layer for ResponseSpec.
Implements hooks and dynamic instructions for incident response.
"""

from typing import Optional, Any
from agents import AgentHooks, RunContextWrapper, Agent, Tool
from state import IncidentState
from interpreter import RuleInterpreter


class IncidentDetectionHooks(AgentHooks[IncidentState]):
    """
    Lifecycle hooks for incident detection.
    Captures tool execution events and triggers rule filtering.
    """
    
    def __init__(self, interpreter: Optional[RuleInterpreter] = None):
        """
        Initialize hooks with optional interpreter.
        
        Args:
            interpreter: RuleInterpreter instance for processing tool calls
        """
        self.interpreter = interpreter
    
    async def on_tool_end(
        self, 
        context: RunContextWrapper[IncidentState], 
        agent: Agent[IncidentState], 
        tool: Tool, 
        result: str
    ) -> None:
        """
        Called immediately after a tool is executed.
        Filters rules triggered by the tool and updates context.
        
        Args:
            context: Run context wrapper containing IncidentState
            agent: The agent that executed the tool
            tool: The tool that was executed
            result: The result returned by the tool
        """
        tool_name = tool.name
        state = context.context
        
        # Get rules triggered by this tool
        triggered_rules = state.get_triggered_rules_for_tool(tool_name)
        
        # Merge with existing triggered rules (for parallel tool calls)
        # Use set to avoid duplicates based on rule.id
        if not state.triggered_rules_current_turn:
            state.triggered_rules_current_turn = triggered_rules
        else:
            existing_ids = {r.id for r in state.triggered_rules_current_turn}
            for rule in triggered_rules:
                if rule.id not in existing_ids:
                    state.triggered_rules_current_turn.append(rule)
        
        # Record the tool call in history
        # Note: Arguments will be extracted from session in check_for_incidents
        # For now, we just record the tool name and result
        state.add_tool_call(tool_name, {}, result)
        
        # Log for debugging (disabled in embodied_agent integration to
        # avoid noisy output; logic is preserved without console prints.)
        # if triggered_rules:
        #     print(f"[IncidentDetection] Tool '{tool_name}' triggered {len(triggered_rules)} rule(s):")
        #     for rule in triggered_rules:
        #         print(f"  - {rule.id}")
        # else:
        #     print(f"[IncidentDetection] Tool '{tool_name}' triggered no rules")
    
    async def on_agent_start(
        self,
        context: RunContextWrapper[IncidentState],
        agent: Agent[IncidentState]
    ) -> None:
        """
        Called when the agent starts.
        Can be used for initialization or logging.
        """
        # Logging disabled to reduce noise in embodied_agent experiments.
        # print(f"[IncidentDetection] Agent '{agent.name}' started")
    
    async def on_agent_end(
        self,
        context: RunContextWrapper[IncidentState],
        agent: Agent[IncidentState],
        output: Any
    ) -> None:
        """
        Called when the agent produces final output.
        Can be used for final incident reporting.
        """
        state = context.context
        # Logging disabled to reduce noise in embodied_agent experiments.
        # if state.incident_detected and not state.remediation_completed:
        #     print(f"[IncidentDetection] WARNING: Agent ended with unresolved incident: {state.triggered_rule_id}")
        # else:
        #     print(f"[IncidentDetection] Agent '{agent.name}' completed successfully")
    
    async def on_llm_start(
        self,
        context: RunContextWrapper[IncidentState],
        agent: Agent[IncidentState],
        system_prompt: Optional[str],
        input_items: list
    ) -> None:
        """
        Called before LLM invocation.
        Log the current detection/remediation mode.
        """
        state = context.context
        
        # Log mode (disabled to avoid extra console noise)
        # if state.incident_detected:
        #     print(f"[IncidentDetection] LLM called in REMEDIATION mode")
        # elif state.triggered_rules_current_turn:
        #     print(f"[IncidentDetection] LLM called in DETECTION mode")


def format_rules_for_prompt(rules: list) -> str:
    """
    Format rules for inclusion in prompts.
    
    Args:
        rules: List of Rule objects
        
    Returns:
        Formatted string representation of rules
    """
    if not rules:
        return "No rules triggered."
    
    formatted = []
    for rule in rules:
        formatted.append(f"- **Rule {rule.id}**")
        formatted.append(f"  Condition: {rule.incident_condition}")
        formatted.append(f"  Remediation: {rule.remediation_action}")
    
    return "\n".join(formatted)
