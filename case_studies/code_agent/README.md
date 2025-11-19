# Code Agent Case Study

## Overview
This case study demonstrates the ResponseSpec safety layer applied to a **Code Agent** that can execute Python code. The agent has access to a Python REPL tool and must follow security rules to prevent dangerous operations.

## Agent Capabilities
- **Tool**: `python_repl` - Execute arbitrary Python code
- **Use Cases**: 
  - Data processing and analysis
  - File operations
  - System automation
  - Mathematical computations

## Security Rules
See `rules.txt` for the complete rule definitions.

### Key Rules:
1. **prevent_file_deletion**: Prevents deletion of files without user confirmation
2. **prevent_network_access**: Blocks unauthorized network requests
3. **prevent_subprocess_execution**: Restricts subprocess/shell command execution
4. **prevent_dangerous_imports**: Blocks imports of dangerous modules (os, subprocess, etc.)

## Running the Demo

### Prerequisites
```bash
# Set OpenAI API key
export OPENAI_API_KEY="your-api-key"

# Install dependencies
pip install openai agents
```

### Run
```bash
cd d:\10.4\AgentSpec-master\ResponseSpec
python case_studies\code_agent\demo.py
```

## Demo Scenarios

### Scenario 1: File Deletion (Incident Detection)
```python
User: "Delete file 1.py in current directory"
Agent: Executes os.remove('1.py')
Safety Layer: 
  ✓ Detects file deletion
  ✓ Triggers incident
  ✓ Executes remediation (recreates file)
```

### Scenario 2: Safe Code Execution
```python
User: "Calculate fibonacci numbers"
Agent: Executes safe Python code
Safety Layer: 
  ✓ No rules triggered
  ✓ Execution proceeds normally
```

## Architecture

```
User Request
    ↓
Agent (gpt-4o)
    ↓
python_repl tool
    ↓
[on_tool_end Hook] → Trigger rules
    ↓
[Dynamic Instructions] → Prompt check_for_incidents
    ↓
Agent calls check_for_incidents
    ↓
[LLM Detection] → Analyze code
    ↓
If incident: Remediation mode
If safe: Continue
```

## Key Files
- `demo.py`: Main demo application
- `rules.txt`: Security rule definitions
- `README.md`: This file

## Extending This Case Study

### Add New Rules
Edit `rules.txt`:
```
rule your_rule_name:
    trigger python_repl
    check: "your natural language condition"
    orchestrate: "your remediation action"
```

### Add New Tools
Modify `demo.py`:
```python
@function_tool
async def your_tool(param: str) -> str:
    """Tool description"""
    # Implementation
    return result

agent, state = create_safe_agent(
    rule_file="case_studies/code_agent/rules.txt",
    base_tools=[python_repl, your_tool],  # Add your tool
    session=session
)
```

## Results & Observations
- ✅ Successfully detects file deletion operations
- ✅ Automatic remediation works correctly
- ✅ Session-based argument extraction provides full code visibility
- ✅ LLM-based detection is accurate for code analysis

## Future Improvements
- [ ] Add more sophisticated code pattern detection
- [ ] Implement rate limiting for repeated dangerous operations
- [ ] Add user confirmation prompts for high-risk operations
- [ ] Support for async code execution monitoring
