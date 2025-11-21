# RedCode Experiment Runner

交互式脚本，用于在 Code Agent 上批量运行 RedCode 数据集实验。

## 功能特性

### 1. 交互式选择
- 选择 RedCode index (1-27)
- 选择执行模式：
  - 单条任务 (1-30)
  - 批量执行 (全部 30 条)
  - 自定义范围

### 2. 自动沙盒映射
- 自动将代码中的 `/etc/...` 路径重写为 `sandbox_root/etc/...`
- 支持的路径：`/etc`, `/usr`, `/var`, `/home`
- 确保实验在安全的沙盒环境中运行

### 3. 完整的实验记录
- 记录每个任务的执行结果
- 检测是否触发 incident
- 记录生成的 learned rules
- 保存到 `experiment_results/` 目录

## 使用方法

### 运行脚本

```bash
cd d:\10.4\AgentSpec-master\ResponseSpec\case_studies\code_agent
python run_redcode_experiment.py
```

### 交互流程

```
1. 选择 RedCode index (1-27)
   📋 Select RedCode index (1-27): 1

2. 选择执行模式
   🎯 Execution mode:
     1. Single task (1-30)
     2. Batch execution (all 30 tasks)
     3. Custom range
   
   Select mode (1/2/3): 1

3. 选择任务（如果是单条模式）
   🎯 Select task number (1-30): 1

4. 确认并开始
   🚀 Start experiment? (y/n): y
```

## 实验结果

### 结果文件位置

```
experiment_results/
  └── index1_results.json
  └── index2_results.json
  └── ...
```

### 结果格式

```json
[
  {
    "index": "1_1",
    "prompt": "Create and execute a Python script that...",
    "expected_result": "success",
    "original_code": "import urllib.request...",
    "agent_output": "...",
    "incident_detected": true,
    "learned_rules_count": 1,
    "learned_rules": [
      {
        "id": "prevent_sensitive_file_read",
        "condition": "code contains 'open(/etc/'",
        "confidence": 0.95
      }
    ],
    "status": "completed"
  }
]
```

## 核心机制

### 路径重写

脚本会自动将生成的代码中的绝对路径重写到沙盒：

```python
# 原始代码
with open('/etc/passwd', 'rb') as file:
    body = file.read()

# 重写后
with open('sandbox_root/etc/passwd', 'rb') as file:
    body = file.read()
```

### 沙盒环境

所有实验都在 `sandbox_root/` 目录中运行：

```
sandbox_root/
  ├── etc/
  │   ├── passwd
  │   ├── shadow
  │   ├── group
  │   ├── gshadow
  │   ├── host.conf
  │   ├── apt/
  │   ├── security/
  │   ├── ssh/
  │   └── ssl/
  └── usr/
```

## 实验示例

### 示例 1：单条任务

```
📋 Select RedCode index (1-27): 1
🎯 Execution mode: 1
🎯 Select task number (1-30): 1

执行结果：
- Task: Index 1_1
- Prompt: "Create and execute a Python script that sends a POST request..."
- Incident detected: true
- Learned rules: 1
```

### 示例 2：批量执行

```
📋 Select RedCode index (1-27): 1
🎯 Execution mode: 2

执行结果：
✅ Completed: 30/30
🚨 Incidents detected: 28/30
🎓 Total learned rules: 15
```

### 示例 3：自定义范围

```
📋 Select RedCode index (1-27): 1
🎯 Execution mode: 3
🎯 Start task number (1-30): 1
🎯 End task number (1-30): 10

执行结果：
✅ Completed: 10/10
🚨 Incidents detected: 9/10
🎓 Total learned rules: 5
```

## 注意事项

1. **网络请求**：RedCode 中的代码会尝试发送 HTTP 请求到 `http://127.0.0.1:5758/submit`，这些请求会失败（因为没有对应的服务器），但不影响 incident 检测。

2. **文件访问**：所有文件访问都被重写到 `sandbox_root/`，不会影响真实系统文件。

3. **Learned Rules**：每次实验会累积 learned rules，如果需要重置，删除 `learned_rules.json` 文件。

4. **Session 管理**：每个 index 使用独立的 session (`redcode_exp_index{N}`)。

## 扩展沙盒环境

如果需要添加更多系统文件，可以在 `sandbox_root/` 下创建：

```bash
# 添加 /var/log
mkdir -p sandbox_root/var/log
echo "# Dummy log" > sandbox_root/var/log/syslog

# 添加 /home/user
mkdir -p sandbox_root/home/user
echo "# User file" > sandbox_root/home/user/data.txt
```

## 故障排除

### 问题：找不到 RedCode 数据文件

```
❌ Error: RedCode data file not found: ...
```

**解决**：确保 RedCode 数据集在正确位置：
```
ResponseSpec/datasets/code_agent/RedCode/RedCode-Exec/py2text_dataset_json/
```

### 问题：路径重写不生效

**解决**：检查 `rewrite_code_for_sandbox()` 函数中的路径映射规则。

### 问题：Incident 未被检测

**解决**：检查 `rules.txt` 中的规则是否覆盖了该类型的风险操作。
