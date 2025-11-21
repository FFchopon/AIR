"""
Factory for creating safe agents with incident response capabilities.
"""

from typing import List, Callable, Optional
from agents import Agent, Tool
from rule import Rule
from state import IncidentState
from interpreter import RuleInterpreter
from openai_integration import IncidentDetectionHooks
from response import ResponseOrchestrator
from tools import check_for_incidents, mark_remediation_complete, get_incident_status, configure_detector
from tool_wrapper import create_safe_tool_with_eradication


def create_safe_agent(
    rule_file: str,
    base_tools: List[Tool],
    agent_name: str = "Safe Agent",
    model: str = "gpt-4o",
    llm_client=None,
    session=None,
    use_learned_rules: bool = True
) -> tuple[Agent[IncidentState], IncidentState]:
    """
    Create an agent with incident response safety layer.
    
    This factory function sets up a complete agent with:
    - Rule-based incident detection
    - Automatic remediation orchestration
    - Tool execution monitoring
    - Dynamic instruction generation
    
    Args:
        rule_file: Path to the ResponseSpec rule file
        base_tools: List of tools the agent can use (e.g., delete_file, copy_file)
        agent_name: Name for the agent
        model: OpenAI model to use (default: gpt-4o)
        llm_client: Optional OpenAI client for incident detection
        session: Optional Session instance for conversation history (enables full argument tracking)
    
    Returns:
        Tuple of (agent, incident_state)
        - agent: Configured Agent instance with safety layer
        - incident_state: IncidentState context object
    
    Example:
        ```python
        from agents import function_tool
        
        @function_tool
        async def delete_file(path: str) -> str:
            # Implementation
            return f"Deleted {path}"
        
        agent, state = create_safe_agent(
            rule_file="rules/security_rules.txt",
            base_tools=[delete_file],
            agent_name="File Manager"
        )
        
        result = await Runner.run(agent, "Delete /tmp/test.txt", context=state)
        ```
    """
    # 1. Load rules from file
    print(f"[create_safe_agent] Loading rules from {rule_file}...")
    rules = Rule.from_file(rule_file)
    print(f"[create_safe_agent] Loaded {len(rules)} rule(s)")
    
    # 2. Create incident state (context)
    state = IncidentState(all_rules=rules, session=session)
    
    # ⭐ 2.1. Load learned rules from previous runs (optional)
    if use_learned_rules:
        print(f"[create_safe_agent] Loading learned rules...")
        state.load_learned_rules()
        print(f"[create_safe_agent] Loaded {len(state.learned_rules)} learned rule(s)")
    else:
        print(f"[create_safe_agent] Skipping learned rules (use_learned_rules=False)")
        state.learned_rules = []  # Ensure empty list
    
    # 3. Create rule interpreter
    interpreter = RuleInterpreter(rules, llm_client)
    
    # 4. Configure detector with LLM client
    configure_detector(llm_client)
    
    # 5. Create hooks for lifecycle events
    hooks = IncidentDetectionHooks(interpreter)
    
    # 6. Create dynamic instructions function
    def dynamic_instructions(
        context, 
        agent
    ) -> str:
        """Generate dynamic instructions based on incident state"""
        return ResponseOrchestrator.generate_dynamic_instructions(context.context)
    
    # ⭐ 7. Wrap base tools with eradication (dual-layer checking)
    print(f"[create_safe_agent] Wrapping {len(base_tools)} base tool(s) with eradication...")
    wrapped_tools = [
        create_safe_tool_with_eradication(tool, rules, state)
        for tool in base_tools
    ]
    
    # 8. Combine safety tools with wrapped base tools
    all_tools = [
        check_for_incidents,
        mark_remediation_complete,
        get_incident_status,
        *wrapped_tools  # ⭐ Use wrapped tools instead of base tools
    ]
    
    # 8. Create the agent
    agent = Agent[IncidentState](
        name=agent_name,
        instructions=dynamic_instructions,
        hooks=hooks,
        tools=all_tools,
        model=model
    )
    
    print(f"[create_safe_agent] Agent '{agent_name}' created with {len(all_tools)} tools")
    print(f"[create_safe_agent] Safety tools: check_for_incidents, mark_remediation_complete, get_incident_status")
    # base_tools are now raw functions, not Tool objects
    base_tool_names = [t.__name__ if hasattr(t, '__name__') else str(t) for t in base_tools]
    print(f"[create_safe_agent] Base tools: {', '.join(base_tool_names)}")
    
    return agent, state


def create_safe_agent_with_custom_instructions(
    rule_file: str,
    base_tools: List[Tool],
    base_instructions: str,
    agent_name: str = "Safe Agent",
    model: str = "gpt-4o",
    llm_client=None,
    session=None
) -> tuple[Agent[IncidentState], IncidentState]:
    """
    Create a safe agent with custom base instructions.
    
    This variant allows you to provide custom base instructions that will be
    combined with the incident response instructions.
    
    Args:
        rule_file: Path to the ResponseSpec rule file
        base_tools: List of tools the agent can use
        base_instructions: Custom instructions for the agent's normal behavior
        agent_name: Name for the agent
        model: OpenAI model to use
        llm_client: Optional OpenAI client for incident detection
    
    Returns:
        Tuple of (agent, incident_state)
    """
    # Load rules and create state
    rules = Rule.from_file(rule_file)
    state = IncidentState(all_rules=rules, session=session)
    
    # ⭐ Load learned rules
    state.load_learned_rules()
    
    interpreter = RuleInterpreter(rules, llm_client)
    configure_detector(llm_client)
    hooks = IncidentDetectionHooks(interpreter)
    
    # Create custom dynamic instructions
    def dynamic_instructions(context, agent) -> str:
        """Combine base instructions with incident response instructions"""
        incident_instructions = ResponseOrchestrator.generate_dynamic_instructions(context.context)
        
        # If in incident mode, incident instructions take priority
        if context.context.incident_detected:
            return incident_instructions
        
        # Otherwise, combine base with safety protocol
        return f"""{base_instructions}

{incident_instructions}
"""
    
    # ⭐ Wrap base tools with eradication
    wrapped_tools = [
        create_safe_tool_with_eradication(tool, rules, state)
        for tool in base_tools
    ]
    
    # Combine tools
    all_tools = [
        check_for_incidents,
        mark_remediation_complete,
        get_incident_status,
        *wrapped_tools  # ⭐ Use wrapped tools
    ]
    
    # Create agent
    agent = Agent[IncidentState](
        name=agent_name,
        instructions=dynamic_instructions,
        hooks=hooks,
        tools=all_tools,
        model=model
    )
    
    return agent, state
