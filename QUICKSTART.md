# 快速入门指南 - 第一阶段完成

## 第一阶段完成情况

第一阶段（搭建项目结构，实现文档处理器）已完成。以下是已实现的功能：

### 1. 项目结构
```
biology-self-improvement/
├── document_processor/     # 文档处理器（已完成）
├── agents/                # 智能体系统（基础框架）
├── llm/                   # LLM集成（基础框架）
├── state/                 # 状态管理（待实现）
├── engine/                # 执行引擎（待实现）
├── utils/                 # 工具函数（配置管理）
├── tests/                 # 测试文件（待实现）
├── pyproject.toml         # 项目配置
├── requirements.txt       # 依赖列表
├── README.md              # 项目说明
├── LICENSE                # 许可证
├── .env.example           # 环境变量示例
├── demo_processor.py      # 演示脚本
└── create_example_docs.py # 创建示例文档
```

### 2. 文档处理器功能

#### 核心模块
- **WordExtractor**: 从Word文档提取图片和文字
- **ImageDescriber**: 使用Ollama (qwen3-vl:8b) 生成图片描述
- **TextFormatter**: 将文档内容格式化为智能体输入
- **DocumentProcessor**: 主处理器，整合所有功能

#### 数据模型
- `DocumentImage`: 图片信息
- `TextBlock`: 文本块信息
- `DocumentContent`: 完整文档内容
- `AgentInput`: 智能体输入格式

### 3. 使用方法

#### 环境设置
```bash
# 1. 克隆项目
git clone <repository-url>
cd biology-self-improvement

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 设置环境变量
cp .env.example .env
# 编辑 .env 文件，设置API密钥等
```

#### 安装Ollama
```bash
# 从 https://ollama.com/ 下载安装
# 拉取模型
ollama pull qwen3-vl:8b
# 启动服务（通常会自动启动）
```

#### 运行演示
```bash
# 创建示例文档
python create_example_docs.py

# 运行文档处理器演示
python demo_processor.py
```

### 4. 核心API

#### 文档处理器
```python
from document_processor import DocumentProcessor

# 创建处理器
processor = DocumentProcessor(
    ollama_base_url="http://localhost:11434",
    enable_image_descriptions=True
)

# 处理单个文档
agent_input = processor.process_document("试题.docx")

# 批量处理文档
results = processor.process_documents(
    ["试题1.docx", "试题2.docx"],
    output_dir="processed_output"
)

# 查看统计信息
processor.print_statistics()
```

#### 配置管理
```python
from utils.config import get_config, init_config

# 初始化配置
config = init_config()  # 自动加载 .env 和 config.json

# 获取配置值
api_key = config.get("deepseek.api_key")
model = config.get("ollama.model")

# 设置配置值
config.set("agents.max_iterations", 5)

# 验证配置
if config.validate():
    print("配置有效")
```

### 5. 测试文档处理器

#### 创建测试文档
```python
# 使用内置脚本创建示例文档
python create_example_docs.py
```

#### 运行功能测试
```python
# 运行演示脚本（包含依赖检查）
python demo_processor.py
```

### 6. 下一步开发

#### 第二阶段：LLM客户端和智能体
1. **实现Deepseek API客户端**
2. **完善Ollama本地客户端**
3. **实现三个智能体**:
   - Actor: 学生角色，生成答案
   - Reviewer: 老师角色，评审答案
   - Reflector: 反思者角色，分析改进
4. **创建状态管理模块**

#### 第三阶段：执行引擎和测试
1. **实现学习循环引擎**
2. **创建完整的状态持久化**
3. **编写单元测试和集成测试**
4. **性能优化和错误处理**

### 7. 故障排除

#### 常见问题

1. **python-docx未安装**
   ```bash
   pip install python-docx
   ```

2. **Ollama服务未运行**
   ```bash
   # 检查服务状态
   curl http://localhost:11434/api/tags

   # 启动服务
   ollama serve
   ```

3. **缺少API密钥**
   - 在 `.env` 文件中设置 `DEEPSEEK_API_KEY`
   - 或通过环境变量设置

4. **图片描述生成失败**
   - 检查Ollama服务是否运行
   - 确认模型是否已下载: `ollama list`
   - 检查网络连接

#### 调试模式
```python
from document_processor import WordExtractor

# 启用详细日志
extractor = WordExtractor()
content = extractor.extract("test.docx")
print(f"提取到 {len(content.images)} 张图片")
print(f"提取到 {len(content.text_blocks)} 个文本块")
```

### 8. 贡献指南

#### 开发工作流
```bash
# 1. 创建功能分支
git checkout -b feature/document-processor

# 2. 运行测试
pytest tests/

# 3. 提交更改
git add .
git commit -m "feat: 完善文档处理器功能"

# 4. 推送到远程
git push origin feature/document-processor
```

#### 代码规范
- 使用类型注解
- 遵循PEP 8
- 编写文档字符串
- 添加单元测试

---

**第一阶段完成时间**: 2026-03-28
**下一阶段开始**: LLM客户端和智能体实现