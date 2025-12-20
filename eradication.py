"""
Eradication module: Learn from incidents to generate prevention rules.

This module implements the "Eradicate" phase of incident response:
- Analyze incidents to identify attack patterns
- Generate specific learned rules to prevent similar incidents
- Use LLM to create actionable prevention rules
"""

import json
from typing import Dict, Any, List
from pydantic import BaseModel
from agents import Agent, Runner
from rule import Rule
from state import IncidentState


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
You are a security expert specializing in learning from incidents to generate prevention rules.

Your task:
1. Analyze the incident details carefully
2. Identify the SPECIFIC pattern that caused the incident
3. Generate a rule that is:
   - Specific enough to catch similar attacks
   - General enough to not block legitimate operations
   - Actionable (can be checked before execution)

Focus on detectable patterns:
- Function calls (e.g., "os.remove(", "shutil.rmtree(", "subprocess.run(")
- Import statements (e.g., "import requests", "import socket")
- Dangerous patterns (e.g., "eval(", "exec(", "__import__")
- File paths (e.g., system directories like "/etc", "/sys")
- Network endpoints (e.g., external URLs, IP addresses)
- Code structure (e.g., loops with file operations)

IMPORTANT:
- The learned rule should be MORE SPECIFIC than the original rule
- Focus on patterns that can be detected in tool arguments (especially code for python_repl)
- Provide concrete examples of what should be blocked
- Explain your reasoning clearly

Example:
Original rule: "executed Python code to delete files"
Learned rule: "code contains 'os.remove(' or 'os.unlink(' or 'shutil.rmtree(' function calls"
Reasoning: "These specific function calls are the direct cause of file deletion"
Examples: ["os.remove('file.txt')", "shutil.rmtree('/tmp/data')"]
""",
            output_type=LearnedRuleOutput,
            model="gpt-4o"
        )
    
    return _rule_generator_agent


# ========================================
# Eradication Function
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
INCIDENT ANALYSIS REQUEST

ORIGINAL RULE THAT WAS TRIGGERED:
- Rule ID: {incident_details['rule_id']}
- Condition: {incident_details['original_condition']}
- Note: This rule detected the incident AFTER execution

INCIDENT DETAILS:
- Tool: {incident_details['tool_call']['tool']}
- Arguments: {json.dumps(incident_details['tool_call']['arguments'], indent=2)}
- Result: {incident_details['tool_call'].get('result', 'N/A')}
- Description: {incident_details['description']}

RECENT HISTORY (for context):
{json.dumps(incident_details.get('recent_history', [])[-5:], indent=2)}

YOUR TASK:
Generate a NEW learned rule that would PREVENT this incident by detecting it BEFORE execution.

The learned rule should:
1. Be MORE SPECIFIC than the original rule
2. Focus on detectable patterns in the tool arguments
3. Have HIGH PRECISION (minimize false positives)
4. Be ACTIONABLE (can be checked before tool execution)

EXAMPLE:
If the incident involved:
- Tool: python_repl
- Code: "import os; os.remove('important_file.txt')"
- Original rule: "executed Python code to delete files"

Then generate:
- Specific pattern: "code contains 'os.remove(' or 'os.unlink(' function calls"
- Reasoning: "These function calls directly cause file deletion and can be detected via static analysis"
- Examples: ["os.remove('file.txt')", "os.unlink('/path/to/file')"]

Generate the learned rule now.
"""
    
    print(f"[Eradication] Calling Rule Generator Agent...")
    
    # Call Rule Generator Agent
    rule_generator = get_rule_generator_agent()
    result = await Runner.run(
        rule_generator,
        incident_prompt,
        context=state
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
# Pattern Matching for Learned Rules
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
- Confidence: {rule.confidence:.0%}
- Learned from incident: {rule.learned_from}

EXAMPLES OF OPERATIONS THIS RULE SHOULD BLOCK:
{chr(10).join(f"- {ex}" for ex in rule.examples)}

CURRENT OPERATION:
- Tool: {tool_name}
- Arguments: {json.dumps(tool_args, indent=2)}

TASK:
Determine if the current operation matches the learned pattern.
This is a PRE-EXECUTION check, so be precise but cautious.

Consider:
1. Does the operation contain the specific pattern described in the rule?
2. Is this a legitimate use case or a potential security issue?
3. Compare with the examples - is this similar to what should be blocked?
4. What is the risk if we allow this operation?

RESPONSE FORMAT (JSON):
{{
    "should_block": true or false,
    "confidence": "high, medium, or low",
    "reasoning": "detailed explanation of your decision",
    "risk_level": "critical, high, medium, or low"
}}

Be conservative: if the pattern matches and there's risk, lean towards blocking.
"""
    
    # Call LLM for pattern matching
    from interpreter import IncidentDetector
    detector = IncidentDetector()
    response = detector._call_llm_for_detection(check_prompt)
    
    should_block = response.get("should_block", False)
    reasoning = response.get("reasoning", "Pattern matched")
    
    return should_block, reasoning
