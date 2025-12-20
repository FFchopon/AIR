This document provides a minimal quick start for embody agent.

## Embody Agent

Embodied agent use 16 tools to do tasks in a simulated environment with rich scene objects and safety rules.

### Configure a Sample Rule

Edit `case_studies/embodied_agent/rules.txt` and add or update a rule, for example:

```text
rule @_put_knife_in_drawer
trigger 
    "_put"
check
    "put knife in the drawer."
orchestrate
    "put knife on the table."
end
```

### Run the Embody Agent Demo

From the project root:

```bash
cd case_studies/embodied_agent
python embodied_agent_demo.py
```

In the interactive prompt, try an instruction such as:

```text
put knife in the drawer
```