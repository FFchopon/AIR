"""
OpenAI Agents SDK integration layer for ResponseSpec.
Implements hooks and dynamic instructions for incident response.
"""

from typing import Optional, Any
import time
from agents import AgentHooks, RunContextWrapper, Agent, Tool
from state import IncidentState
from interpreter import RuleInterpreter
import interpreter


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
        self._llm_call_idx = 0
        self._llm_call_start_ts: Optional[float] = None
    
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

        # If the operation was blocked before execution by a learned safety
        # rule (pre-check), do not enter detection mode for this turn.
        banner = "OPERATION BLOCKED BY LEARNED SAFETY RULE"
        if isinstance(result, str) and banner in result:
            # Record the tool call in history (arguments may be extracted from
            # session elsewhere). Clear turn-level state so it is not reused.
            state.add_tool_call(tool_name, {}, result)
            state.reset_turn_state()
            return
        
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
        state = context.context
        if state.is_timing_enabled():
            state.reset_timing_state()

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

        if state.is_timing_enabled():
            state.timing_task_end_ts = time.time()

            total_s = None
            if state.timing_task_start_ts is not None:
                total_s = (state.timing_task_end_ts - state.timing_task_start_ts)

            action_s = state.timing_action_total_s if state.timing_action_total_s else None
            pre_s = state.timing_precheck_total_s if state.timing_precheck_total_s else None
            post_s = state.timing_postcheck_total_s if state.timing_postcheck_total_s else None
            response_s = state.timing_response_s
            eradication_s = state.timing_eradication_s

            print("\n" + "=" * 80)
            print("[Timing] Task Summary")
            print("=" * 80)
            if total_s is not None:
                print(f"[Timing] Total: {total_s:.3f} s")
            if action_s is not None:
                print(f"[Timing] Agent Action: {action_s:.3f} s")
            if pre_s is not None:
                print(f"[Timing] Pre-check: {pre_s:.3f} s")
            if post_s is not None:
                print(f"[Timing] Post-check: {post_s:.3f} s")
            if response_s is not None:
                print(f"[Timing] Response: {response_s:.3f} s")
            if eradication_s is not None:
                print(f"[Timing] Eradication: {eradication_s:.3f} s")

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
        if state.is_timing_enabled() and state.timing_task_start_ts is None:
            state.timing_task_start_ts = time.time()

        if not interpreter.DEBUG_LLM_API:
            return

        self._llm_call_idx += 1
        self._llm_call_start_ts = time.time()

        stage = "agent"
        if agent.name == "Security Rule Generator":
            stage = "eradication"
        elif state.remediation_in_progress or (state.incident_detected and not state.remediation_completed):
            stage = "remediation"

        prompt_chars = len(system_prompt) if isinstance(system_prompt, str) else 0
        print(
            f"[LLM API START] kind=agent stage={stage} agent={agent.name} call={self._llm_call_idx} system_prompt_chars={prompt_chars}"
        )


    async def on_llm_end(
        self,
        context: RunContextWrapper[IncidentState],
        agent: Agent[IncidentState],
        output: Any
    ) -> None:
        """Called after an LLM invocation, if supported by the Agents SDK."""
        if not interpreter.DEBUG_LLM_API:
            return

        if self._llm_call_start_ts is None:
            print(f"[LLM API END] kind=agent agent={agent.name} call={self._llm_call_idx}")
            return

        duration_ms = int((time.time() - self._llm_call_start_ts) * 1000)
        print(
            f"[LLM API END] kind=agent agent={agent.name} call={self._llm_call_idx} duration_ms={duration_ms}"
        )
        self._llm_call_start_ts = None


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
