# 生物学习智能体 (Biology Learning Agent)

一个通过多轮迭代优化生物学试题答案的智能体系统。

## 项目概述

该系统模拟"学生做题-对照标准-发现偏差-修正思维"的完整学习闭环：

1. **Actor (学生)** - 生成初始答案
2. **Reviewer (老师)** - 对照评分标准评审答案并给出评分
3. **Reflector (反思者)** - 分析差距并生成改进策略

通过多轮迭代，系统能够从评分标准中自主学习答题策略，持续优化答案质量。

## 核心特性

- **混合LLM策略**: 本地qwen3-vl:8b处理图片 + Deepseek API处理文本
- **自动文档处理**: 提取Word文档中的图片和文字，生成纯文本输入
- **多轮优化**: 用户可配置训练轮数，系统迭代改进答案
- **完整状态追踪**: JSON带版本控制，记录每次迭代的完整历史

## 快速开始

### 安装

1. 克隆项目:
```bash
git clone https://github.com/yourusername/biology-learning-agent.git
cd biology-learning-agent
```

2. 创建虚拟环境:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows
```

3. 安装依赖:
```bash
pip install -r requirements.txt
```

### 准备环境

1. **安装Ollama**: 从 https://ollama.com/ 下载安装
2. **拉取本地模型**:
```bash
ollama pull qwen2.5-vl:8b
```
3. **配置API密钥**: 创建 `.env` 文件:
```bash
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 基本使用

```python
from engine.learning_engine import LearningEngine

# 初始化学习引擎
engine = LearningEngine()

# 处理一个Word文档试题
result = engine.process_question("path/to/question.docx", rounds=3)

# 查看结果
print(f"最终评分: {result.score}")
print(f"最终答案: {result.final_answer}")
```

## 项目结构

```
biology-learning-agent/
├── document_processor/      # 文档处理
│   ├── word_extractor.py    # Word文档解析
│   ├── image_describer.py   # 图片描述生成
│   └── text_formatter.py    # 文本格式化
│
├── agents/                  # 智能体系统
│   ├── actor.py            # 学生角色
│   ├── reviewer.py         # 老师角色
│   ├── reflector.py        # 反思者角色
│   └── agent_base.py       # 智能体基类
│
├── llm/                     # LLM集成
│   ├── local_llm.py        # 本地Ollama集成

│   ├── deepseek_client.py  # Deepseek API客户端
│   └── llm_base.py         # LLM基类
│
├── state/                   # 状态管理
│   ├── state_manager.py    # 状态管理

│   ├── persistence.py      # JSON持久化

│   └── versioning.py       # 版本控制

│
├── engine/                  # 执行引擎

│   └── learning_engine.py  # 学习循环引擎

│
├── utils/                  # 工具函数

│   └── config.py          # 配置管理

│
├── tests/                  # 测试文件

├── pyproject.toml         # 项目配置

├── requirements.txt       # Python依赖

└── README.md              # 项目说明

```

## 工作原理

1. **文档预处理**:
   - 使用 `python-docx` 提取Word文档中的图片和文字
   - 本地 `qwen3-vl:8b` 模型生成图片描述
   - 替换图片位置为描述文本，生成纯文本输入

2. **学习循环** (每轮迭代):
   - **Actor**: 基于试题内容和RULES.md规范生成答案
   - **Reviewer**: 对照评分标准评审答案，给出评分和改进建议
   - **Reflector**: 分析差距，生成改进策略供下一轮使用

3. **状态管理**:
   - 每轮迭代状态完整保存为JSON文件
   - 支持版本追踪和调试分析
   - 可恢复历史状态继续优化

## 开发指南

### 项目设置

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 类型检查
mypy .

# 代码格式化
black .
isort .
```

### 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开 Pull Request

## 许可证

MIT License - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系

- 问题反馈: [GitHub Issues](https://github.com/yourusername/biology-learning-agent/issues)
- 项目主页: https://github.com/yourusername/biology-learning-agent