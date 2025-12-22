## ResponseSpec Case Studies – Quick Start

![overview](./figure/overview.png)

This repository contains example case studies built on top of the **ResponseSpec** framework. The two main case studies are:

- **Code Agent** – executes Python code in a sandbox with safety rules, incident detection, and eradication (learned rules / pre-check).
- **Embodied Agent** – controls an embodied agent in a simulated environment with rich scene objects and safety rules.
- **Computer Use Agent** – controls a computer use agent in a simulated environment with rich scene objects and safety rules.

This document provides a minimal quick start.

---

## Code Agent

The Code Agent uses a `python_repl` tool to execute Python code.

### Configure a Sample Rule

Edit `case_studies/code_agent/rules.txt` and add or update a rule, for example:

```text
rule @show_sensitive_directory
trigger 
    "python_repl"
check
    "executed Python code to show files in current directory."
orchestrate
    "alert the user."
end
```

### Run the Code Agent Demo

From the project root:

```bash
cd case_studies/code_agent
python code_agent_demo.py
```

In the interactive prompt, try an instruction such as:

```text
write a python script to show files in current directory
```

Expected behavior:

- On the first attempt, the operation should pass through execution but be flagged by **post-check** according to your rule in `rules.txt`.
- The incident response may then trigger **eradication**, which writes a new learned rule into `learned_rules.txt`.
- On subsequent attempts with similar instructions, the **pre-check** phase consults `learned_rules.txt` and can **block** the operation before any code runs.

**The documents providing a minimal quick start for Embody Agent and Computer Use Agent can be found in its respective directories.**