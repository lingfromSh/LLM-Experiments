# 🔬 LLM Eval Platform

> 生产级 LLM 评估平台。开箱即用。

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![uv](https://img.shields.io/badge/package%20manager-uv-black.svg)](https://github.com/astral-sh/uv)

[English](./README.md) | **中文**

---

## 为什么做这个项目

LLM 评估现状很糟糕。你面临这些问题：

- 评估脚本跑一次就消失了，无法复用
- 无法追踪 prompt v2 是否真的比 v1 更好
- 没有对比框架——只能靠"看起来更好"的主观判断
- 内置指标不匹配你的实际场景
- 评估过程中完全没有可观测性

**LLM Eval Platform** 解决这些问题。它是一个完整的、生产就绪的评估系统，开箱即用：

✅ **数据集** — 从 HuggingFace 下载或导入自己的数据，平台内统一管理  
✅ **指标** — 内置精确匹配、代码执行、LLM-as-judge 和自定义指标  
✅ **追踪** — 每次推理和评分的完整可观测性  
✅ **历史记录** — 追踪每次评估运行，跨时间对比  
✅ **对比实验** — A/B 测试 prompt、模型、温度、agent 架构  
✅ **异步执行** — 提交评估后后台自动运行，无需等待

不再重复造评估基础设施。专注评估本身。

---

## 核心模块

### 📦 数据集 (Datasets)

统一的数据集管理，零摩擦。

**从 HuggingFace 下载：**

```bash
# 自动下载并注册数据集
python datasets/scripts/fetch_datasets.py --dataset gsm8k
python datasets/scripts/fetch_datasets.py --all
```

**从自己的文件导入：**

```python
# 通过 CLI 或 API 导入自定义数据集
python -m eval_platform.datasets import \
  --file my_data.jsonl \
  --category reasoning \
  --name "my-benchmark"
```

**平台内管理：**

- 所有数据集以统一的 JSONL 格式存储
- 注册表追踪元数据（来源、许可证、大小、评分方法）
- 版本控制，可复现
- 通过 CLI 或未来的 Web UI 浏览、过滤和管理

**支持的数据源：**

- HuggingFace Datasets（自动下载 + 转换）
- 本地 JSONL/JSON/CSV 文件
- 通过适配器支持自定义格式

### 📊 指标 (Metrics)

电池已装好——覆盖各种场景的评估指标。

**内置指标：**

| 指标                     | 使用场景                     | 实现方式                  |
| ------------------------ | ---------------------------- | ------------------------- |
| **精确匹配**             | 数学、推理、事实问答         | 正则提取 + 字符串比较     |
| **代码执行**             | 代码生成                     | 沙箱执行测试用例          |
| **GEval (LLM-as-Judge)** | 主观任务（写作、翻译、创意） | 带评分标准的校准 LLM 评分 |
| **BLEU/ROUGE**           | 翻译、摘要                   | n-gram 重叠度指标         |
| **语义相似度**           | 改写、嵌入质量               | 嵌入向量的余弦相似度      |
| **自定义指标**           | 你的领域                     | 支持任意逻辑的插件系统    |

**使用示例：**

```python
from eval_platform.metrics import GEval, ExactMatch, CodeExec

# 带自定义评分标准的 LLM-as-judge
metric = GEval(
    name="清晰度",
    criteria="解释是否清晰且结构良好？",
    threshold=0.7,
    model="gpt-4o"
)

# 确定性任务的精确匹配
metric = ExactMatch(extract_pattern=r"答案是：(\d+)")

# 带沙箱的代码执行
metric = CodeExec(timeout=5, test_cases=[...])
```

**扩展指标：**

```python
# 自定义指标插件
class MyMetric(BaseMetric):
    def score(self, input: str, output: str, expected: str) -> float:
        # 你的逻辑
        return 0.95
```

### 🔍 追踪 (Tracing)

每次评估运行的完整可观测性。

**追踪内容：**

- 每次 LLM 推理（prompt、completion、延迟、token 数）
- 每次指标计算（judge 推理过程、分数）
- 数据集加载和预处理
- 错误和异常

**基于 Arize Phoenix：**

```bash
# 启动追踪 UI
python -m phoenix.server.main serve
# 打开 http://localhost:6006
```

**你能得到：**

- 追踪瀑布图（父 → 子 span）
- Token 使用和成本追踪
- 延迟分解
- 错误检查
- 按模型、数据集、指标、时间范围过滤

**为什么重要：**
当你的评估说"模型 A 优于模型 B"时，追踪告诉你*为什么*。检查具体样本，看 judge 在哪里有分歧，识别延迟瓶颈。

### 📈 历史与报告 (History & Reports)

追踪每次评估运行。跨时间对比。

**自动追踪：**

```bash
# 每次运行都会被记录
pytest experiments/ -v
# 结果保存到 .eval_platform/runs/
```

**存储内容：**

- 运行元数据（时间戳、配置、git commit）
- 每样本结果（输入、输出、期望、分数）
- 聚合指标（均值、中位数、标准差、置信区间）
- 模型配置、prompt 模板、超参数

**查询历史：**

```bash
# 列出所有运行
eval-platform history list

# 显示特定运行的详情
eval-platform history show run_2024_01_15_14_30

# 对比两次运行
eval-platform history compare run_123 run_456
```

**使用场景：**

- 追踪 prompt 工程后的质量提升
- 检测模型更新后的性能回归
- 审计评估结果以符合合规要求
- 构建团队可见性的仪表板

### 🚀 异步执行 (Async Execution)

LLM 评估很慢。非常慢。单次运行可能需要几分钟到几小时。你不应该盯着它等。

**提交后就不用管了：**
```bash
# 提交评估到后台运行
eval-platform run submit \
  --experiment experiments/temperature/ \
  --model gpt-4o \
  --dataset gsm8k \
  --name "gpt4o-temp-sweep"

# 立即返回 job ID
# Job submitted: job_abc123

# 检查状态
eval-platform run status job_abc123
# Status: running (45% complete, ETA: 12m)

# 列出所有任务
eval-platform run list
```

**后台发生了什么：**
- 带优先级调度的任务队列
- 瞬态故障自动重试
- 带预计完成时间的进度追踪
- 资源管理（GPU 内存、API 速率限制）
- 优雅关闭和恢复

**通知：**
```bash
# 完成后通知
eval-platform run submit ... --notify slack,email

# 或 webhook
eval-platform run submit ... --webhook https://your-service/callback
```

**为什么重要：**
- 午饭前提交 10 个实验，饭后看结果
- 过夜运行扫描，不用开着终端
- CI/CD 集成不会阻塞流水线
- 团队成员可以提交任务，不用等别人完成

**高级特性：**
- 任务依赖（A 完成后运行 B）
- 资源配额（限制并发 GPU 使用）
- 成本预算（API 花费超过阈值时停止）
- 分布式执行（跨多台机器运行）

### ⚖️ 对比实验 (Comparison)

LLM 实验的系统化 A/B 测试。

**对比任何内容：**

```bash
# 相同任务，不同 prompt
eval-platform compare \
  --run-baseline prompt_v1 \
  --run-experiment prompt_v2 \
  --dataset gsm8k

# 相同 prompt，不同模型
eval-platform compare \
  --run-baseline gpt-4o \
  --run-experiment claude-3.5-sonnet \
  --dataset reasoning

# 相同模型，不同温度
eval-platform compare \
  --run-baseline temp_0.0 \
  --run-experiment temp_0.7 \
  --dataset creative_writing
```

**你能得到：**

- 并排分数对比
- 统计显著性检验（bootstrap 置信区间）
- 每样本分解（哪些样本改善/回归）
- 可视化（图表、热力图）

**高级对比：**

- 笛卡尔积：所有模型 × 所有 prompt × 所有数据集
- 回归检测：质量下降时告警
- 成本归一化对比：每美元质量

---

## 快速开始

### 安装

```bash
git clone https://github.com/<your-org>/llm-eval-platform.git
cd llm-eval-platform

# 使用 uv 安装（推荐）
uv sync

# 或使用 pip
pip install -e .
```

### 配置

**1. 配置模型：**

```bash
cp models.json.example models.json
```

```jsonc
// models.json
{
  "gpt-4o": {
    "model": "openai/gpt-4o",
    "api_key": "sk-...",
    "api_base": "https://api.openai.com/v1",
  },
  "claude": {
    "model": "anthropic/claude-3-5-sonnet-20241022",
    "api_key": "sk-ant-...",
  },
  "local": {
    "model": "openai/llama-3.1-8b",
    "api_key": "no_key",
    "api_base": "http://localhost:11434/v1",
  },
  "judge": {
    "model": "openai/gpt-4o",
    "api_key": "sk-...",
  },
}
```

**2. 获取数据集：**

```bash
# 下载所有基准数据集
python datasets/scripts/fetch_datasets.py --all

# 或特定数据集
python datasets/scripts/fetch_datasets.py --dataset gsm8k,humaneval
```

**3. 启动追踪：**

```bash
python -m phoenix.server.main serve
```

**4. 运行首次评估：**

```bash
# 基础正确性测试
pytest experiments/example.py -v

# 温度扫描
pytest experiments/basic/temperature/ -v

# 指定模型
pytest experiments/ -v --test-llm-model gpt-4o
```

**5. 查看结果：**

```bash
# 列出评估历史
eval-platform history list

# 对比运行
eval-platform compare run_001 run_002

# 打开追踪 UI
open http://localhost:6006
```

---

## 使用示例

### 示例 1：Prompt 工程 A/B 测试

你重写了系统 prompt。它真的更好吗？

```bash
# 运行基线（旧 prompt）
pytest experiments/ -v \
  --prompt-template prompts/v1.txt \
  --dataset gsm8k \
  --run-name "prompt_v1"

# 运行实验（新 prompt）
pytest experiments/ -v \
  --prompt-template prompts/v2.txt \
  --dataset gsm8k \
  --run-name "prompt_v2"

# 对比
eval-platform compare prompt_v1 prompt_v2
```

**输出：**

```
对比：prompt_v1 vs prompt_v2
数据集：gsm8k（100 个样本）

指标：精确匹配
  prompt_v1: 72.0% ± 4.5%
  prompt_v2: 78.0% ± 4.1%
  提升：+6.0%（p < 0.05）✓

每样本分解：
  改善：12 个样本
  回归：6 个样本
  不变：82 个样本
```

### 示例 2：模型选择

哪个模型在你的任务上表现最好？

```bash
# 评估多个模型
for model in gpt-4o claude local-llama; do
  pytest experiments/ -v \
    --test-llm-model $model \
    --dataset my_task \
    --run-name "model_$model"
done

# 对比所有
eval-platform compare model_gpt-4o model_claude model_local-llama
```

### 示例 3：温度优化

为你的场景找到最佳温度。

```bash
# 运行温度扫描（0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0）
pytest experiments/basic/temperature/ -v \
  --test-llm-model gpt-4o \
  --dataset creative_writing

# 分析结果
eval-platform history show temp_sweep_001
```

### 示例 4：自定义数据集

在你的专有数据上评估。

```bash
# 1. 准备数据集（JSONL 格式）
cat > my_eval.jsonl << 'EOF'
{"id": "1", "input": "我们的退款政策是什么？", "expected_output": "30 天内..."}
{"id": "2", "input": "如何升级？", "expected_output": "进入设置..."}
EOF

# 2. 导入平台
eval-platform datasets import \
  --file my_eval.jsonl \
  --category qa \
  --name "internal-qa-bench"

# 3. 运行评估
pytest experiments/ -v --dataset internal-qa-bench
```

---

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI / Web UI                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ 数据集   │  │ 指标     │  │ 追踪     │  │  历史与    │  │
│  │          │  │          │  │          │  │  报告      │  │
│  │ HF Hub   │  │ 精确匹配 │  │ Phoenix  │  │            │  │
│  │ 自定义   │  │ 代码执行 │  │ OpenTel  │  │ 运行日志   │  │
│  │ 注册表   │  │ GEval    │  │ Spans    │  │ 对比       │  │
│  │ JSONL    │  │ 自定义   │  │ 延迟     │  │ 回归检测   │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                   实验运行器                                  │
│            (pytest + LiteLLM + DeepEval)                     │
├─────────────────────────────────────────────────────────────┤
│                   存储层                                     │
│         (JSONL 数据集, SQLite 历史, 追踪数据)                │
└─────────────────────────────────────────────────────────────┘
```

**设计原则：**

- **开箱即用** — 所有功能即装即用
- **可扩展** — 自定义指标、数据集、导出器的插件系统
- **可观测** — 完整追踪，没有黑盒
- **可复现** — 声明式配置、版本化数据集、确定性执行
- **生产就绪** — 错误处理、重试、成本追踪、CI/CD 集成

---

## 支持的基准测试

| 数据集     | 类别          | 大小 | 评分方式 | 来源                    |
| ---------- | ------------- | ---- | -------- | ----------------------- |
| GSM8K      | 数学推理      | 100  | 精确匹配 | openai/gsm8k            |
| HumanEval  | 代码生成      | 164  | 代码执行 | openai/openai_humaneval |
| TruthfulQA | 事实准确性    | 100  | GEval    | TruthfulQA/truthful_qa  |
| BBH        | 多步推理      | 100  | 精确匹配 | lukaemon/bbh            |
| 学术写作   | 技术写作      | 30   | GEval    | 自定义                  |
| 创意写作   | 创意任务      | 30   | GEval    | 自定义                  |
| WMT 翻译   | 翻译（ro-en） | 50   | GEval    | wmt/wmt16               |

**添加自己的数据集：** 参见[数据集模块](#-数据集-datasets)

---

## 路线图

### 阶段 1 — 核心平台 ✅

- [x] 统一数据集管理（HF + 自定义导入）
- [x] 内置指标（精确匹配、代码执行、GEval）
- [x] 追踪集成（Arize Phoenix）
- [x] 评估历史追踪
- [x] 基础对比框架

### 阶段 2 — 异步执行 & Agent 评估 🔨

- [ ] 后台任务执行（Celery/RQ + Redis）
- [ ] 带优先级调度的任务队列
- [ ] 带预计完成时间的进度追踪
- [ ] 通知系统（Slack、邮件、webhooks）
- [ ] 资源管理和成本预算
- [ ] 多轮 agent 对话测试框架
- [ ] 工具使用评估（函数调用准确性、schema 合规性）
- [ ] Agent 轨迹评分（路径质量，而非仅最终答案）
- [ ] ReAct / CoT / 规划模式对比
- [ ] Agent 基准数据集（SWE-bench、WebArena）

### 阶段 3 — 高级特性

- [ ] 统计显著性检验（bootstrap 置信区间）
- [ ] 回归检测（质量下降时告警）
- [ ] 成本归一化评分（每美元质量、每 token 质量）
- [ ] CI/CD 集成（GitHub Actions、GitLab CI 模板）
- [ ] 分布式执行（跨多个 worker 运行扫描）

### 阶段 4 — Web 平台

- [ ] 数据集管理的 Web UI
- [ ] 交互式对比仪表板
- [ ] 团队协作（共享运行、评论、标注）
- [ ] 编程访问 API
- [ ] 导出到 W&B、MLflow、CSV、JSON

### 阶段 5 — 可扩展性

- [ ] 插件市场（社区指标、数据集）
- [ ] 自定义指标 SDK
- [ ] 数据集贡献指南
- [ ] 自托管部署指南
- [ ] 企业特性（SSO、RBAC、审计日志）

---

## 项目结构

```
llm-eval-platform/
├── models.json.example          # 模型配置
├── pyproject.toml               # 依赖
├── datasets/
│   ├── registry.yaml            # 数据集目录
│   ├── scripts/
│   │   └── fetch_datasets.py    # HF 下载 + 转换
│   ├── math/                    # GSM8K
│   ├── coding/                  # HumanEval
│   ├── factual/                 # TruthfulQA
│   ├── reasoning/               # BBH
│   ├── writing/                 # 学术写作
│   ├── creative_writing/        # 创意写作
│   └── translation/             # WMT
├── experiments/
│   ├── conftest.py              # Pytest fixtures
│   ├── config.py                # 共享配置
│   ├── example.py               # 最小示例
│   └── basic/
│       └── temperature/         # 温度扫描
└── .eval_platform/              # 运行历史（自动生成）
```

---

## 技术栈

| 组件           | 技术                   | 选择原因                    |
| -------------- | ---------------------- | --------------------------- |
| **测试运行器** | pytest                 | 生态系统、CI 集成、并行执行 |
| **LLM 接口**   | LiteLLM                | 100+ 提供商，统一 API       |
| **指标**       | DeepEval               | GEval、缓存、模型抽象       |
| **数据集**     | HuggingFace `datasets` | 标准注册表、流式处理        |
| **追踪**       | Arize Phoenix          | 开源、OTel 兼容、本地运行   |
| **历史**       | SQLite + JSONL         | 简单、可移植、可查询        |
| **包管理**     | uv                     | 快速、可复现的锁文件        |

---

## 贡献

这是一个早期项目。我们正在构建我们希望存在的评估平台。

**贡献方式：**

- **数据集** — 为你的领域添加基准测试
- **指标** — 实现新的评估方法
- **Agent 评估** — 帮助构建阶段 2
- **Web UI** — 设计仪表板
- **Bug 报告** — 如果有问题，我们想知道

参见 [CONTRIBUTING.md](CONTRIBUTING.md) 了解指南。

---

## 与替代方案的对比

| 特性           | LLM Eval Platform | DeepEval | LangSmith | 自定义脚本 |
| -------------- | ----------------- | -------- | --------- | ---------- |
| **开箱即用**   | ✅                | ✅       | ❌        | ❌         |
| **开源**       | ✅                | ✅       | ❌        | ✅         |
| **数据集管理** | ✅                | ❌       | ❌        | ❌         |
| **内置追踪**   | ✅                | ❌       | ✅        | ❌         |
| **历史追踪**   | ✅                | ❌       | ✅        | ❌         |
| **对比框架**   | ✅                | ❌       | ⚠️        | ❌         |
| **自托管**     | ✅                | ✅       | ❌        | ✅         |
| **Agent 评估** | 🔜                | ⚠️       | ✅        | ❌         |

---

## 许可证

MIT

---

## Star 历史

如果这个项目对你的 LLM 评估工作有帮助，请考虑给它一个 ⭐

---

**为 LLM 社区用 ❤️ 构建**

_停止猜测。开始度量。_
