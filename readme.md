## ResponseSpec Case Studies – Quick Start

This repository contains example case studies built on top of the **ResponseSpec** framework. The two main case studies are:

- **Code Agent** – executes Python code in a sandbox with safety rules, incident detection, and eradication (learned rules / pre-check).
- **Embodied Agent** – controls an embodied agent in a simulated environment with rich scene objects and safety rules.

This document provides a minimal quick start for both case studies.

---

## 1. Code Agent

The Code Agent uses a `python_repl` tool to execute Python code and applies ResponseSpec rules to detect risky behavior and generate learned rules that block similar behavior in the future.

### 1.1 Configure a Sample Rule

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

This rule means:

- It triggers whenever the `python_repl` tool is used.
- If the LLM judges that the executed code is trying to **list files in the current directory** (a potentially sensitive action), it will be treated as a risk.
- The `orchestrate` clause defines the remediation behavior (e.g., alerting the user). After an incident, the eradication logic can generate a **learned rule** so that similar operations are blocked at **pre-check** next time.

### 1.2 Run the Code Agent Demo

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

---

## 2. Embodied Agent

The Embodied Agent operates in a simulated household-like environment with objects such as a stove, microwave, knife, table, sink, fridge, etc. It uses ResponseSpec rules to detect and remediate safety issues like fire hazards, electrical shock, explosion, poisoning, and slip hazards.

### 2.1 Environment and Rules

Key files for the embodied case study:

- `case_studies/embodied_agent/embodied_agent.py`  
  Defines the embodied agent tools (e.g., `_pick`, `_put`, `_open`, `_turn_on`) and their effects on the environment.

- `case_studies/embodied_agent/sandbox_root/scene_config.py`  
  Defines scene templates and a **unified master scene** that aggregates objects from multiple risk categories into a single rich sandbox environment.

- `case_studies/embodied_agent/sandbox_root/sandbox_manager.py`  
  Manages environment state, reset logic, and interaction history.

- `case_studies/embodied_agent/rules.txt`  
  Contains initial ResponseSpec rules for the embodied agent (e.g., unsafe knife placement, dangerous use of heat sources, poisoning scenarios, etc.).

- `case_studies/embodied_agent/learned_rules.txt`  
  Stores learned pre-check rules automatically generated from past incidents.

You can extend `rules.txt` with your own rules. For example (illustrative only):

```text
rule @put_knife_in_drawer
trigger 
    "_put"
check
    "the agent placed a knife safely into a drawer instead of leaving it in unsafe locations."
orchestrate
    "if the knife is left in an unsafe place, pick it up and put it into the drawer."
end
```

### 2.2 Run the Embodied Agent Demo

From the project root:

```bash
cd case_studies/embodied_agent
python embodied_agent_demo.py
```

You will enter an interactive loop where you can issue natural language instructions, for example:

- `put the knife on the table`
- `turn on the stove and boil some water`

The agent will:

1. Interpret your instruction and plan a sequence of embodied actions using its tools.
2. Execute each tool in the **sandboxed environment**.
3. For each tool call:
   - **Pre-check** (learned rules): consult `learned_rules.txt` to see if this operation should be blocked before execution.
   - **Post-check** (initial rules): evaluate `rules.txt` to determine whether the resulting state constitutes an incident.
4. If an incident is detected, ResponseSpec triggers remediation (e.g., undoing dangerous actions or moving objects to safe locations) and may run **eradication** to generate new learned rules.

On future runs, these learned rules help the agent avoid repeating similar incidents by blocking dangerous actions early at the pre-check stage.

---

## 3. Where to Go Next

- **Rules & State Core Logic**  
  See `rule.py`, `state.py`, `tool_wrapper.py`, `interpreter.py`, and `response.py` for the core ResponseSpec implementation.

- **Eradication (Learned Rules Generation)**  
  See `eradication.py` for how new rules are generated from incidents and saved into `learned_rules.txt`.

- **Experiment Scripts**  
  In addition to the interactive demos, there are experiment scripts (e.g., for datasets like SafeAgentBench or RedCode) that run larger-scale evaluations using the same ResponseSpec integration.

You can customize rules, scenes, and tools to build your own safety-aware agents on top of this framework.
