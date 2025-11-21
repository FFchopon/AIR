"""
Tools for incident detection and remediation in OpenAI Agents SDK.
"""

import json
from typing import Optional
from agents import function_tool, RunContextWrapper
from state import IncidentState
from interpreter import IncidentDetector


# Global detector instance (will be configured with LLM client)
_detector: Optional[IncidentDetector] = None


def configure_detector(llm_client=None):
    """
    Configure the global incident detector with an LLM client.
    
    Args:
        llm_client: OpenAI client instance (optional, uses default if None)
    """
    global _detector
    _detector = IncidentDetector(llm_client)


async def _extract_tool_args_from_session(session, tool_name: str = None, n: int = 5):
    """
    Extract tool call arguments from session history.
    
    Args:
        session: Session instance
        tool_name: Name of the tool to filter (None = all tools)
        n: Number of recent items to extract
        
    Returns:
        List of tool call dicts with arguments
    """
    import json
    
    try:
        # Get all items from session
        items = await session.get_items()
        
        # Extract recent tool calls with their arguments
        tool_calls = []
        i = len(items) - 1
        
        while i >= 0 and len(tool_calls) < n:
            item = items[i]
            
            # Check if this is a function call output (Session format)
            if isinstance(item, dict) and item.get('type') == 'function_call_output':
                call_id = item.get('call_id')
                result = item.get('output', '')
                
                # Find the corresponding function call
                for j in range(i - 1, -1, -1):
                    prev_item = items[j]
                    if isinstance(prev_item, dict) and prev_item.get('type') == 'function_call':
                        if prev_item.get('call_id') == call_id:
                            # Found the function call!
                            func_name = prev_item.get('name')
                            args_str = prev_item.get('arguments', '{}')
                            
                            try:
                                args = json.loads(args_str) if isinstance(args_str, str) else args_str
                            except:
                                args = {}
                            
                            # Filter by tool_name if specified
                            if tool_name is None or func_name == tool_name:
                                tool_calls.append({
                                    'tool': func_name,
                                    'arguments': args,
                                    'result': result
                                })
                            break
                # Don't break here - continue to find more tool calls
            i -= 1
        
        # Reverse to get chronological order
        return list(reversed(tool_calls))
    
    except Exception as e:
        print(f"[_extract_tool_args_from_session] Error: {e}")
        import traceback
        traceback.print_exc()
        return []


@function_tool
async def check_for_incidents(
    ctx: RunContextWrapper[IncidentState]
) -> str:
    """
    Check if any security incidents occurred based on recently triggered rules.
    
    This tool analyzes recent actions against security rules to detect potential
    incidents. It only checks rules that were triggered by the last tool call,
    making the detection process efficient.
    
    Returns:
        A message indicating whether an incident was detected, with details if applicable.
    """
    state = ctx.context
    
    # Check if any rules were triggered
    if not state.triggered_rules_current_turn:
        return "✓ No security rules were triggered by the last action. No check needed."
    
    # Try to extract tool call arguments from session (preferred method)
    recent_history = []
    
    if state.session:
        print(f"[check_for_incidents] Using session to extract tool arguments...")
        recent_history = await _extract_tool_args_from_session(state.session, tool_name=None, n=5)
        print(f"[check_for_incidents] Extracted {len(recent_history)} tool calls from session")
    
    # Fallback to state history if session not available
    if not recent_history:
        print(f"[check_for_incidents] Session not available, using state history (arguments may be incomplete)")
        recent_history = state.get_recent_history(n=5)
    
    # Before running full incident detection, check if the last tool call
    # was already blocked by a learned safety rule during pre-check.
    if recent_history:
        last_call = recent_history[-1]
        result_text = last_call.get('result', '') if isinstance(last_call, dict) else ''
        banner = "OPERATION BLOCKED BY LEARNED SAFETY RULE"
        if banner in result_text:
            print("[check_for_incidents] Last operation was blocked by a learned rule. Skipping incident/remediation.")
            # This is a prevention event, not an incident that actually executed.
            # Clear turn-level state so it is not reused.
            state.reset_turn_state()
            return (
                "✓ Operation was blocked by a learned safety rule before execution. "
                "No further incident response is required."
            )

    # Get detector instance
    global _detector
    if _detector is None:
        _detector = IncidentDetector()
    
    print(f"[check_for_incidents] Checking {len(state.triggered_rules_current_turn)} triggered rule(s)...")
    print(f"[check_for_incidents] Recent history: {recent_history}")
    
    # Perform incident detection
    incident_detected, incident_details = _detector.detect_incident(
        state.triggered_rules_current_turn,
        recent_history
    )
        
    if incident_detected:
        # Find the corresponding rule to get remediation action
        triggered_rule = next(
            (r for r in state.triggered_rules_current_turn 
             if r.id == incident_details["rule_id"]),
            None
        )
        
        if triggered_rule:
            print(f"[check_for_incidents] INCIDENT DETECTED: {incident_details['rule_id']}")
            
            # Check BEFORE setting incident state
            should_eradicate = not state.incident_detected
            
            # Set incident state
            state.set_incident(
                rule_id=incident_details["rule_id"],
                description=incident_details["description"],
                remediation=triggered_rule.remediation_action,
                severity=incident_details.get("severity", "medium")
            )
            
            # ⭐⭐⭐ ERADICATION: Prepare for learning (execute AFTER remediation) ⭐⭐⭐
            if should_eradicate:
                print(f"\n[check_for_incidents] Preparing ERADICATION (will execute after remediation)...")
                
                # Prepare incident details for eradication
                eradication_details = {
                    'rule_id': incident_details['rule_id'],
                    'original_condition': triggered_rule.incident_condition,
                    'tool_call': {
                        'tool': recent_history[-1]['tool'] if recent_history else 'unknown',
                        'arguments': recent_history[-1]['arguments'] if recent_history else {},
                        'result': recent_history[-1]['result'] if recent_history else ''
                    },
                    'description': incident_details['description'],
                    'recent_history': recent_history
                }
                
                # ⭐ Store for later execution (after remediation completes)
                state.pending_eradication = eradication_details
                print(f"[check_for_incidents] Eradication scheduled for after remediation")
            else:
                print(f"[check_for_incidents] Skipping eradication (already in incident response mode)")
            
            # After recording this incident, clear turn-level triggered rules
            # so they are not reused for a new incident on subsequent checks.
            state.reset_turn_state()
            
            return f"""
🚨 SECURITY INCIDENT DETECTED 🚨

Rule: {incident_details['rule_id']}
Severity: {incident_details.get('severity', 'medium').upper()}
Description: {incident_details['description']}

You are now in INCIDENT RESPONSE MODE.
Your next actions will be guided by the remediation protocol.

🎓 Note: A safety analysis will be performed after remediation to prevent future incidents.
"""
        else:
            print(f"[check_for_incidents] ERROR: Rule {incident_details['rule_id']} not found in triggered rules")
            return f"⚠️ Incident detected but rule not found: {incident_details['rule_id']}"
    else:
        # No incident detected, clear turn state
        state.reset_turn_state()
        print(f"[check_for_incidents] No incidents detected")
        return "✓ Security check passed. No incidents detected. You may continue with normal operations."


@function_tool
async def mark_remediation_complete(
    ctx: RunContextWrapper[IncidentState]
) -> str:
    """
    Mark the current incident remediation as complete.
    
    Call this tool after you have successfully executed all remediation actions
    for the detected incident. This will return the system to normal operation mode.
    
    Returns:
        Confirmation message that remediation is complete.
    """
    state = ctx.context
    
    if not state.incident_detected:
        return "⚠️ No active incident to mark as complete."
    
    # Record the completed incident for logging
    completed_incident = {
        "rule_id": state.triggered_rule_id,
        "description": state.incident_description,
        "severity": state.severity
    }
    
    print(f"[mark_remediation_complete] Incident {completed_incident['rule_id']} remediated")
    
    # ⭐⭐⭐ ERADICATION: Execute learning AFTER remediation ⭐⭐⭐
    eradicate_message = ""
    
    if state.pending_eradication:
        print(f"\n[mark_remediation_complete] Starting ERADICATION phase...")
        
        try:
            from eradication import eradicate_incident
            
            # Execute the pending eradication
            learned_rule = await eradicate_incident(state.pending_eradication, state)
            
            eradicate_message = f"""

╔══════════════════════════════════════════════════════════════╗
║  🎓 ERADICATION: NEW SAFETY RULE LEARNED                     ║
╚══════════════════════════════════════════════════════════════╝

A new prevention rule has been automatically generated from this incident:

Rule ID: {learned_rule.id}
Pattern: {learned_rule.incident_condition}
Confidence: {learned_rule.confidence:.0%}

This rule will BLOCK similar operations BEFORE execution in future runs.
The incident will not happen again.
"""
            
            # Clear pending eradication
            state.pending_eradication = None
            print(f"[mark_remediation_complete] Eradication completed successfully")
            
        except Exception as e:
            print(f"[mark_remediation_complete] ERROR during eradication: {e}")
            eradicate_message = f"\n⚠️ Eradication failed: {e}"
            state.pending_eradication = None
    else:
        print(f"[mark_remediation_complete] No pending eradication")
    
    # Clear incident state
    state.clear_incident()
    
    # Also clear any turn-level detection state so that
    # previously triggered rules are not reused in later checks.
    state.reset_turn_state()
    
    return f"""
✓ REMEDIATION COMPLETE ✓

The incident has been successfully remediated.
Incident: {completed_incident['rule_id']} (Severity: {completed_incident['severity']})

The system has returned to normal operation mode.
You may now continue with other tasks.
{eradicate_message}
"""


@function_tool
async def get_incident_status(
    ctx: RunContextWrapper[IncidentState]
) -> str:
    """
    Get the current status of incident detection and remediation.
    
    Returns:
        A summary of the current incident state.
    """
    state = ctx.context
    
    if state.incident_detected:
        return f"""
INCIDENT STATUS: ACTIVE

Rule: {state.triggered_rule_id}
Severity: {state.severity.upper()}
Description: {state.incident_description}
Remediation Required: {state.remediation_action}
Remediation In Progress: {state.remediation_in_progress}
Remediation Completed: {state.remediation_completed}
"""
    else:
        return f"""
INCIDENT STATUS: NORMAL

No active incidents.
Total tool calls: {len(state.tool_call_history)}
Last tool called: {state.last_tool_called or 'None'}
"""
