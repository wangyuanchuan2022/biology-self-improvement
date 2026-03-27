# 生物解题自我精进教练 (biology-self-improvement-tutor)

一个具备自我反思与修正能力的生物学答题智能体Skill。

## 核心功能

### 双角色Agent系统
- **行动者 (Actor)**：基于RULES.md规范解答生物学题目
- **评审者 (Reviewer)**：对照标准答案进行差距分析

### 完整学习闭环
```
题目输入 → Actor答题 → Reviewer评审 → 差距分析报告 → 优化RULES.md → 下一轮迭代
                          ↑                                                  ↓
                          └────────── 记录改进来源（年份+题号）─────────────┘
```

### 审查重点
- **表达用词**：专业术语使用、规范句式
- **论述逻辑**：要点完整性、描述层次、实验设计

## 目录结构

```
biology-self-improvement-tutor/
├── SKILL.md                          # 主技能文件，包含完整工作流程
├── USAGE_EXAMPLES.md                 # 使用示例
├── README.md                         # 本文件
├── agents/                           # Agent定义
│   ├── actor.md                      # 行动者Agent
│   └── reviewer.md                   # 评审者Agent
├── scripts/                          # 辅助脚本
│   └── gap_analyzer.py               # 差距分析工具
├── references/                       # 参考资料
│   ├── README.md
│   ├── terminology_guide.md          # 生物学术语指南
│   └── question_templates.md         # 答题模板
└── evals/                            # 评估测试
    └── evals.json                    # 测试用例
```

## 快速开始

### 基础使用

1. 确保Skill已安装在 `.claude/skills/` 目录下
2. 准备题目和标准答案
3. 使用以下格式调用：

```
请使用biology-self-improvement-tutor技能解答这道题：

题目：[题目内容，包括图片描述]

标准答案：
[标准答案内容]

题目来源：[年份]年第[题号]题，[题型]
```

### 详细示例

参见 [USAGE_EXAMPLES.md](./USAGE_EXAMPLES.md) 获取完整使用示例。

## 核心特性

### 1. 行动者答题
- 严格遵循RULES.md规范
- 展示完整审题分析过程
- 输出结构化答案

### 2. 评审者分析
- 逐点对比标准答案
- 审查用词专业性
- 检查逻辑完整性
- 评估实验设计合理性

### 3. 差距分析报告
- 结构化展示用词差距
- 明确指出逻辑漏洞
- 提供优化后的答案

### 4. RULES.md优化
- 自动记录改进来源
- 添加具体可操作的规则
- 持续迭代提升答题质量

## 与项目文件配合

### 关键文件路径
- **RULES.md**：`D:\python\projects\biology-self-improvement\RULES.md`
- **试题库**：`D:\python\projects\biology-self-improvement\生物 试题与答案\`

### 文档格式支持
配合document-skills使用，可处理：
- PDF格式的试卷和答案
- DOCX格式的试题与评分标准
- 图片描述整合分析

## 工作原理详解

### 行动者 (Actor)
定位：严谨的生物学考生
- 仔细审题，识别考点
- 调用RULES.md对应题型指南
- 组织层次化答案
- 自我检查对照清单

### 评审者 (Reviewer)
定位：严格的高考阅卷教师
- 拆解标准答案得分点
- 审查专业术语使用
- 检查论述逻辑完整性
- 对照评分标准预估得分

## 开发说明

### 测试用例
在 `evals/evals.json` 中添加测试用例，包含：
- 题目内容
- 标准答案
- 题目来源信息
- 预期输出要求

### 扩展参考资料
在 `references/` 目录下可添加：
- 更多题型模板
- 专业术语表
- 评分标准细则

## 注意事项

1. **不要省略任何步骤**：完整的闭环是提升的关键
2. **记录所有改进**：每次优化必须注明题目来源
3. **具体可操作**：差距分析和规则要具体，让用户知道如何改进
4. **多轮迭代**：鼓励用户进行多轮练习，逐步提升

## 许可证

本项目遵循MIT许可证。
