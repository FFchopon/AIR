This document provides a minimal quick start for embody agent.

This case study provides a text-simulated sandbox environment for running experiments. For using the SafeAgentEnv environment, please refer to: https://github.com/shengyin1224/SafeAgentBench

## Embody Agent

Embodied agent use 17 tools to do tasks in a simulated environment with rich scene objects and safety rules.

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

### Batch Run SafeAgentBench Risk Tasks

Use `embodied_agent_batch.py` to feed `instruction` fields from a
`dataset/SafeAgentBench/risk_task` JSON file (01–10) into the embodied agent.
Rules are still loaded from `rules.txt` in this directory.

From the project root:

```bash
# Run first 3 tasks from Fire Hazard (01), starting at index 0
python case_studies/embodied_agent/embodied_agent_batch.py --task-file 01 --start 0 --count 3

# Run 5 Explosion Hazard tasks starting at index 10
python case_studies/embodied_agent/embodied_agent_batch.py -t 03 -s 10 -n 5

# Run all remaining tasks from index 20 onward; save JSON results
python case_studies/embodied_agent/embodied_agent_batch.py \
  --task-file 03_explosion_hazard.json \
  --start 20 \
  --output case_studies/embodied_agent/batch_results_03.json
```

Useful options:

| Option | Meaning |
|--------|---------|
| `--task-file` / `-t` | `01`–`10`, basename, or path to a risk_task JSON |
| `--start` / `-s` | 0-based start index (default: `0`) |
| `--count` / `-n` | Number of tasks to run (default: all remaining) |
| `--rule-file` | ResponseSpec rules (default: `rules.txt`) |
| `--model` | Model name (default: `gpt-5`) |
| `--output` / `-o` | Optional path for JSON result dump |