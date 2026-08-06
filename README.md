# MyLLMEval — 个人 LLM 评估体系

本项目旨在建立一套**属于自己的 LLM 评估体系**——不是跑一遍公开排行榜，而是基于实际生产场景，通过一系列可控实验来回答一个核心问题：**在我的业务里，哪个模型、哪种配置真正好用？**

你可以把整个项目看作一组**从生产需求出发的测试与评估集合**。每个实验都对应一个真实的评估维度（温度敏感性、事实准确性、代码能力、推理能力等），所有结果都可以通过 `models.json` 的配置直接复现或对比。

## 核心理念

- **自己的标准**：不依赖通用 benchmark 排名，而是定义对自己业务重要的评估维度和数据集。
- **生产导向**：评估维度来自真实场景——数学推理、代码生成、事实准确性、翻译保真度、创意写作等。
- **可复现**：通过 `models.json` 锁定模型端点，任何实验都可以精确复现和对比。
- **可扩展**：新增数据集、评估指标、模型都只需添加配置，无需改动框架代码。

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 配置模型

复制示例配置并填入你的模型信息：

```bash
cp models.json.example models.json
```

编辑 `models.json`，将 `default` 和 `judge` 指向你要评估的模型：

```json
{
  "default": {
    "model": "openai/gpt-4o",
    "api_key": "sk-xxx",
    "api_base": "https://api.openai.com/v1"
  },
  "judge": {
    "model": "openai/gpt-4o-mini",
    "api_key": "sk-xxx",
    "api_base": "https://api.openai.com/v1"
  }
}
```

- **`default`**：被评估的模型（待测 LLM 或 Agent 的端点）。
- **`judge`**：评估模型（LLM-as-Judge，用于主观任务的自动评分）。

两个角色可以指向同一个模型，也可以分开——比如用 GPT-4o 做 judge 来评估一个本地小模型。

> **评估自己的 Agent？** 只需将 `api_base` 指向你的 Agent 服务地址（兼容 OpenAI 接口即可），`model` 字段填你的 Agent 标识名。框架会将 Agent 视为一个普通 LLM 端点进行评测。

### 3. 下载数据集

```bash
# 下载全部数据集
python datasets/scripts/fetch_datasets.py

# 或只下载某个数据集
python datasets/scripts/fetch_datasets.py --dataset gsm8k

# 查看可用数据集
python datasets/scripts/fetch_datasets.py --list
```

### 4. 运行实验

实验基于 pytest 运行，通过 CLI 参数切换模型：

```bash
# 使用 models.json 中的 default 模型运行所有实验
pytest experiments/

# 指定特定模型
pytest experiments/ --test-llm-model my-local-model

# 使用不同的 judge 模型
pytest experiments/ --judge-llm-model gpt-4o-judge
```

## 项目结构

```
MyLLMEval/
├── models.json              # 模型配置（不入库，需自行创建）
├── models.json.example      # 模型配置示例
├── datasets/                # 统一格式的评估数据集
│   ├── registry.yaml        # 数据集目录（机器可读）
│   ├── scripts/             # 数据集下载与转换脚本
│   ├── math/                # GSM8K — 数学推理
│   ├── coding/              # HumanEval — 代码生成
│   ├── factual/             # TruthfulQA — 事实准确性
│   ├── reasoning/           # BBH — 多步推理
│   ├── writing/             # 学术写作（自定义）
│   ├── creative_writing/    # 创意写作（自定义）
│   └── translation/         # 翻译（自定义子集）
└── experiments/             # 实验代码
    ├── config.py            # 共享配置（模型加载、温度扫描、指标映射）
    ├── conftest.py          # pytest CLI 参数
    └── basic/               # 基础实验
        └── temperature/     # 温度敏感性实验
```

## 评估维度

| 维度       | 数据集        | 评分方式             | 说明                        |
| ---------- | ------------- | -------------------- | --------------------------- |
| 数学推理   | GSM8K         | 精确匹配             | 小学应用题，答案确定        |
| 代码生成   | HumanEval     | 执行测试用例         | Python 函数生成，跑通即正确 |
| 事实准确性 | TruthfulQA    | LLM-as-Judge (GEval) | 检测幻觉和常见误解          |
| 多步推理   | BBH           | 精确匹配             | BIG-Bench Hard 逻辑推理任务 |
| 学术写作   | 自定义        | LLM-as-Judge (GEval) | 清晰度、结构、准确性        |
| 创意写作   | 自定义        | LLM-as-Judge (GEval) | 创意性、连贯性、文风        |
| 翻译       | WMT16 (ro-en) | LLM-as-Judge (GEval) | 翻译忠实度和流畅度          |

## 自定义评估

### 添加新模型

在 `models.json` 中添加一个条目即可，无需改代码：

```json
{
  "my-agent": {
    "model": "my-agent-v2",
    "api_key": "your-key",
    "api_base": "http://localhost:8080/v1"
  }
}
```

然后运行：

```bash
pytest experiments/ --test-llm-model my-agent
```

### 添加新数据集

1. 在对应分类目录下创建 JSONL 文件，遵循统一格式（见 `datasets/README.md`）
2. 在 `datasets/registry.yaml` 中注册
3. 在 `experiments/config.py` 的 `DATASET_CONFIG` 中添加映射

### 添加新实验

在 `experiments/` 下创建新的实验目录，使用 `config.py` 提供的模型加载和配置工具，按 pytest 约定编写测试即可。

## 技术栈

- **[deepeval](https://github.com/confident-ai/deepeval)** — LLM 评估指标（GEval、精确匹配等）
- **[litellm](https://github.com/BerriAI/litellm)** — 统一模型调用接口（支持 OpenAI、本地模型、任意兼容端点）
- **[datasets](https://github.com/huggingface/datasets)** — HuggingFace 数据集加载
- **[pytest](https://pytest.org)** — 实验运行与报告
