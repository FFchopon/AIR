"""
Eradication module: Learn from incidents to generate prevention rules.

This module implements the "Eradicate" phase of incident response:
- Analyze incidents to identify attack patterns
- Generate specific learned rules to prevent similar incidents
- Use LLM to create actionable prevention rules
"""

import json
import time
from typing import Dict, Any, List
from pydantic import BaseModel
from agents import Agent, Runner
from rule import Rule
from state import IncidentState
import interpreter


# ========================================
# Pydantic Models for Structured Output
# ========================================

class LearnedRuleOutput(BaseModel):
    """Structured output for learned rule generation"""
    rule_id: str
    trigger_tool: str
    specific_pattern: str  # Specific pattern to detect
    reasoning: str         # Why this pattern prevents the incident
    confidence: float      # Confidence score (0.0-1.0)
    examples: List[str]    # Example operations that should be blocked


# ========================================
# Rule Generator Agent
# ========================================

# Global instance (created once)
_rule_generator_agent = None

def get_rule_generator_agent() -> Agent:
    """Get or create the rule generator agent"""
    global _rule_generator_agent
    
    if _rule_generator_agent is None:
        _rule_generator_agent = Agent(
            name="Security Rule Generator",
            instructions="""
You generate prevention rules from incident reports.

Goal:
- Propose a NEW learned rule that would PREVENT the incident by matching a detectable pattern BEFORE execution.

Requirements:
- Focus only on patterns detectable in tool arguments (especially python_repl code).
- Prefer high precision (minimize false positives) while still catching similar attacks.
- Provide clear reasoning and concrete examples that should be blocked.

Example:

rule @prevent_copy_from_etc_v1
trigger 
    "python_repl"
check
    "executed Python code to copy files in /etc directory."
orchestrate
    "block execution before running the tool"
end
""",
            output_type=LearnedRuleOutput,
            model="gpt-5.6-luna"
        )
    
    return _rule_generator_agent


# ========================================
# Eradication Function (Generate Learned Rule)
# ========================================

async def eradicate_incident(
    incident_details: Dict[str, Any],
    state: IncidentState
) -> Rule:
    """
    Eradicate phase: Learn from incident and generate prevention rule.
    
    Args:
        incident_details: Dictionary containing:
            - rule_id: ID of the triggered rule
            - original_condition: Original rule's condition
            - tool_call: Dict with tool, arguments, result
            - description: Incident description
            - recent_history: Recent tool call history
        state: IncidentState object
    
    Returns:
        Learned Rule object
    """
    
    print(f"\n{'='*80}")
    print(f"ERADICATION PHASE: Learning from Incident")
    print(f"{'='*80}")
    
    # Build detailed incident analysis prompt
    incident_prompt = f"""
INCIDENT CONTEXT
- Original rule id: {incident_details['rule_id']}
- Original condition: {incident_details['original_condition']}

Tool call that led to the incident:
- Tool: {incident_details['tool_call']['tool']}
- Arguments: {json.dumps(incident_details['tool_call']['arguments'], indent=2)}
- Result: {incident_details['tool_call'].get('result', 'N/A')}
- Description: {incident_details['description']}

Recent history (optional context):
{json.dumps(incident_details.get('recent_history', [])[-5:], indent=2)}

TASK
Generate a NEW learned rule that would PREVENT this incident BEFORE execution.

REQUIREMENTS
- Match a detectable pattern in tool arguments (especially python_repl code).
- High precision (minimize false positives).
"""
    
    print(f"[Eradication] Calling Rule Generator Agent...")
    
    # Call Rule Generator Agent
    rule_generator = get_rule_generator_agent()
    start_ts = time.time()
    if interpreter.DEBUG_LLM_API:
        prompt_chars = len(incident_prompt) if isinstance(incident_prompt, str) else 0
        print(
            f"[LLM API START] kind=agent stage=eradication agent={rule_generator.name} prompt_chars={prompt_chars}"
        )
    result = await Runner.run(
        rule_generator,
        incident_prompt,
        context=state
    )
    if interpreter.DEBUG_LLM_API:
        duration_ms = int((time.time() - start_ts) * 1000)
        print(
            f"[LLM API END] kind=agent stage=eradication agent={rule_generator.name} duration_ms={duration_ms}"
        )
    
    learned_rule_data = result.final_output
    
    print(f"[Eradication] ✓ Rule generated successfully")
    
    # Normalize confidence to 0.0-1.0 range
    confidence = learned_rule_data.confidence
    if confidence > 1.0:
        # LLM might return 95 instead of 0.95
        confidence = confidence / 100.0
        print(f"[Eradication] Normalized confidence from {learned_rule_data.confidence} to {confidence}")
    # Ensure it's within valid range
    confidence = max(0.0, min(1.0, confidence))
    
    # Create Learned Rule object
    learned_rule = Rule(
        id=learned_rule_data.rule_id,
        trigger_tool=learned_rule_data.trigger_tool,
        incident_condition=learned_rule_data.specific_pattern,
        remediation_action="block execution before running the tool",
        raw=f"# Learned rule from incident: {incident_details['rule_id']}",
        is_learned=True,
        confidence=confidence,
        learned_from=incident_details['rule_id'],
        examples=learned_rule_data.examples
    )
    
    # Add to state and save
    state.add_learned_rule(learned_rule)
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"✅ LEARNED NEW SAFETY RULE")
    print(f"{'='*80}")
    print(f"Rule ID: {learned_rule.id}")
    print(f"Trigger Tool: {learned_rule.trigger_tool}")
    print(f"Pattern: {learned_rule.incident_condition}")
    print(f"Confidence: {learned_rule.confidence:.0%}")
    # print(f"\nReasoning:")
    # print(f"  {learned_rule_data.reasoning}")
    # print(f"\nExamples that will be blocked:")
    # for example in learned_rule_data.examples:
    #    print(f"  - {example}")
    # print(f"\nLearned from: {learned_rule.learned_from}")
    # print(f"{'='*80}\n")
    
    return learned_rule


# ========================================
# Pre-Check phase based on Learned Rules
# ========================================

async def check_learned_rule_pattern(
    rule: Rule,
    tool_name: str,
    tool_args: Dict[str, Any],
    state: IncidentState
) -> tuple[bool, str]:
    """
    Check if current operation matches a learned rule's pattern.
    
    Args:
        rule: Learned rule to check
        tool_name: Name of the tool being called
        tool_args: Arguments for the tool
        state: IncidentState for context
    
    Returns:
        (should_block, reasoning)
    """
    
    # Build pattern matching prompt
    check_prompt = f"""
You are a security pattern matcher for learned safety rules.

LEARNED RULE:
- ID: {rule.id}
- Pattern: {rule.incident_condition}

CURRENT OPERATION:
- Tool: {tool_name}
- Arguments: {json.dumps(tool_args, indent=2)}

TASK:
Pre-check the CURRENT OPERATION against the learned rule pattern.
If it matches, set "should_block" to true; otherwise false.

RESPONSE FORMAT (JSON):
{{
    "should_block": true or false,
    "reasoning": "detailed explanation of your decision"
}}
"""
    
    # Call LLM for pattern matching
    from interpreter import IncidentDetector
    detector = IncidentDetector()
    response = detector._call_llm_for_detection(check_prompt, stage="precheck")
    
    should_block = response.get("should_block", False)
    reasoning = response.get("reasoning", "Pattern matched")
    
    return should_block, reasoning
