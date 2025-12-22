This document provides a minimal quick start for the Computer Use agent case study.

## Computer Use Agent

This case study demonstrates ResponseSpec-style incident handling for an agent that operates a real browser using the OpenAI Agents SDK Computer Use tool.

Prerequisites:

- `OPENAI_API_KEY` set in your environment
- Access to a Computer Use capable model (default: `computer-use-preview`)

### Configure an Initial Rule

Edit `case_studies/computer_use_agent/rules.txt` and add or update a rule. The trigger tool for this case study is `"computer"`.

Example:

```text
rule @search_dangerous_keywords
trigger
    "computer"
check
    "Search for the sensitive word 'September 11 attacks' on Google."
orchestrate
    "clear the search bar"
end
```

### Learned Rules (Pre-check)

This demo maintains a `learned_rules.txt` file in the same folder. Learned rules are checked before critical actions.

If `learned_rules.txt` is missing, it will be created automatically when an incident occurs and the eradication step generates a new learned rule.

### Run the Demo

From the project root:

```bash
cd case_studies/computer_use_agent
python computer_use_agent_demo.py
```

In the interactive prompt, try an instruction such as:

```text
open google and search 'September 11 attacks'
```