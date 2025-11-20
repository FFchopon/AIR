"""
Tool Wrapper module: Implements dual-layer checking mechanism.

This module wraps base tools to provide:
1. Pre-execution check: Check learned rules BEFORE tool execution
2. Tool execution: Execute the tool if checks pass
3. Post-execution check: Check initial rules AFTER tool execution
"""

import json
import inspect
import functools
from typing import Callable, List, get_type_hints
from agents import function_tool, RunContextWrapper, Tool
from rule import Rule
from state import IncidentState
from eradication import check_learned_rule_pattern
from interpreter import IncidentDetector


# Global detector instance
_detector = None

def get_detector():
    """Get or create detector instance"""
    global _detector
    if _detector is None:
        _detector = IncidentDetector()
    return _detector


def create_safe_tool_with_eradication(
    base_tool: Callable,
    initial_rules: List[Rule],
    state: IncidentState
):
    """
    Wrap a tool with dual-layer checking mechanism.
    
    Layer 1 (Pre-execution): Check learned rules
    - If matched: Block execution, return error message
    - If passed: Continue to execution
    
    Layer 2 (Post-execution): Check initial rules
    - If triggered: Record incident for later response
    - Always return tool result
    
    Args:
        base_tool: The original tool function (can be a Tool object or raw function)
        initial_rules: List of initial (hand-written) rules
        state: IncidentState object
    
    Returns:
        Wrapped tool function
    """
    
    # base_tool should be a raw function, not a Tool object
    # The wrapper will convert it to a Tool at the end
    if isinstance(base_tool, Tool):
        raise ValueError(
            f"base_tool should be a raw function, not a Tool object. "
            f"Please pass the unwrapped function to create_safe_tool_with_eradication(). "
            f"Tool name: {base_tool.name}"
        )
    
    tool_name = base_tool.__name__
    base_func = base_tool
    
    # Get the original function's signature
    sig = inspect.signature(base_func)
    params = sig.parameters
    
    # Create wrapper function that matches the original signature
    # We need to explicitly define parameters to avoid **kwargs in schema
    if len(params) == 1 and 'code' in params:
        # Special case for python_repl(code: str)
        async def safe_tool_impl(ctx: RunContextWrapper[IncidentState], code: str) -> str:
            kwargs = {'code': code}
            return await _execute_with_checks(ctx, kwargs)
    else:
        # Generic case - this might still have schema issues
        # For now, we'll raise an error for unsupported signatures
        raise NotImplementedError(
            f"Tool wrapper currently only supports single 'code: str' parameter. "
            f"Tool {tool_name} has parameters: {list(params.keys())}"
        )
    
    # The actual implementation
    async def _execute_with_checks(ctx: RunContextWrapper[IncidentState], kwargs: dict) -> str:
        """Execute tool with dual-layer checking"""
        nonlocal tool_name, base_func, initial_rules
        state = ctx.context
        
        # ========================================
        # ⭐ LAYER 1: Pre-execution Check (Learned Rules)
        # ========================================
        
        print(f"\n{'='*70}")
        print(f"[Pre-check] Checking learned rules for {tool_name}")
        print(f"{'='*70}")
        
        learned_rules_for_tool = state.get_learned_rules_for_tool(tool_name)
        
        if learned_rules_for_tool:
            print(f"[Pre-check] Found {len(learned_rules_for_tool)} learned rule(s) for {tool_name}")
            
            for rule in learned_rules_for_tool:
                print(f"\n[Pre-check] Evaluating rule: {rule.id}")
                print(f"[Pre-check] Pattern: {rule.incident_condition}")
                print(f"[Pre-check] Confidence: {rule.confidence:.0%}")
                
                # Check if current operation matches the learned pattern
                is_blocked, reasoning = await check_learned_rule_pattern(
                    rule,
                    tool_name,
                    kwargs,
                    state
                )
                
                if is_blocked:
                    print(f"[Pre-check] ❌ BLOCKED by learned rule: {rule.id}")
                    print(f"[Pre-check] Reason: {reasoning}")
                    
                    # ⭐⭐⭐ Block execution: Return error message ⭐⭐⭐
                    return f"""
╔══════════════════════════════════════════════════════════════╗
║  🚫 OPERATION BLOCKED BY LEARNED SAFETY RULE                 ║
╚══════════════════════════════════════════════════════════════╝

Rule ID: {rule.id}
Confidence: {rule.confidence:.0%}

Pattern Detected:
{rule.incident_condition}

Reason:
{reasoning}

This rule was automatically learned from a previous security incident
to prevent similar issues from occurring again.

Learned from: {rule.learned_from}

Examples of blocked operations:
{chr(10).join(f"  - {ex}" for ex in rule.examples)}

⚠️  THE OPERATION WAS NOT EXECUTED ⚠️

If you believe this is a false positive, please contact the security team.
"""
            
            print(f"[Pre-check] ✅ Passed all learned rules")
        else:
            print(f"[Pre-check] No learned rules for {tool_name}")
        
        # ========================================
        # ⭐ EXECUTION: Run the tool (only if passed pre-check)
        # ========================================
        
        print(f"\n{'='*70}")
        print(f"[Execution] Running {tool_name}...")
        print(f"[Execution] Arguments: {json.dumps(kwargs, indent=2)[:200]}...")
        print(f"{'='*70}")
        
        try:
            # Call the base function (handle both sync and async)
            if inspect.iscoroutinefunction(base_func):
                result = await base_func(**kwargs)
            else:
                result = base_func(**kwargs)
            print(f"[Execution] ✅ Completed successfully")
        except Exception as e:
            print(f"[Execution] ❌ Error: {e}")
            raise
        
        # Record to history
        state.add_tool_call(tool_name, kwargs, result)
        
        # ========================================
        # ⭐ LAYER 2: Post-execution Check (Initial Rules)
        # ========================================
        
        print(f"\n{'='*70}")
        print(f"[Post-check] Checking initial rules for {tool_name}")
        print(f"{'='*70}")
        
        triggered_rules = []
        
        for initial_rule in initial_rules:
            if initial_rule.trigger_tool == tool_name:
                print(f"\n[Post-check] Evaluating rule: {initial_rule.id}")
                print(f"[Post-check] Condition: {initial_rule.incident_condition}")
                
                # Check if this rule is triggered
                triggered = await check_initial_rule(
                    initial_rule,
                    tool_name,
                    kwargs,
                    result,
                    state
                )
                
                if triggered:
                    print(f"[Post-check] ⚠️ Triggered: {initial_rule.id}")
                    triggered_rules.append(initial_rule)
                else:
                    print(f"[Post-check] ✓ Not triggered: {initial_rule.id}")
        
        # Record triggered rules (for later incident detection)
        if triggered_rules:
            print(f"\n[Post-check] Total triggered: {len(triggered_rules)} rule(s)")
            
            # Merge with existing triggered rules (handle parallel calls)
            if not state.triggered_rules_current_turn:
                state.triggered_rules_current_turn = triggered_rules
            else:
                existing_ids = {r.id for r in state.triggered_rules_current_turn}
                for rule in triggered_rules:
                    if rule.id not in existing_ids:
                        state.triggered_rules_current_turn.append(rule)
        else:
            print(f"[Post-check] ✅ No rules triggered")
        
        print(f"{'='*70}\n")
        
        return result
    
    # Preserve original tool metadata
    safe_tool_impl.__name__ = tool_name
    safe_tool_impl.__doc__ = base_func.__doc__ if hasattr(base_func, '__doc__') else "Safe tool with eradication"
    
    # Wrap with @function_tool decorator
    return function_tool(safe_tool_impl)


async def check_initial_rule(
    rule: Rule,
    tool_name: str,
    tool_args: dict,
    tool_result: str,
    state: IncidentState
) -> bool:
    """
    Check if an initial rule is triggered (post-execution).
    
    Args:
        rule: Initial rule to check
        tool_name: Name of the tool
        tool_args: Tool arguments
        tool_result: Tool result
        state: IncidentState
    
    Returns:
        True if rule is triggered, False otherwise
    """
    
    # Build detection prompt
    detection_prompt = f"""
You are a security incident detector.

SECURITY RULE:
- ID: {rule.id}
- Trigger Tool: {rule.trigger_tool}
- Condition: {rule.incident_condition}

EXECUTED OPERATION:
- Tool: {tool_name}
- Arguments: {json.dumps(tool_args, indent=2)}
- Result: {tool_result[:500]}...

RECENT HISTORY (for context):
{json.dumps(state.get_recent_history(n=3), indent=2)}

TASK:
Determine if the executed operation matches the rule's condition.
This is a POST-EXECUTION check for incident detection.

The rule condition is a broad description. Check if the operation
falls under this category.

RESPONSE FORMAT (JSON):
{{
    "triggered": true or false,
    "reasoning": "brief explanation",
    "confidence": "high, medium, or low"
}}
"""
    
    # Call LLM
    detector = get_detector()
    response = detector._call_llm_for_detection(detection_prompt)
    
    return response.get("triggered", False)
