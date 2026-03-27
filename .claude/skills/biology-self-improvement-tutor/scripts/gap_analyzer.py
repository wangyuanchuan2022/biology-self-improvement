#!/usr/bin/env python3
"""
生物解题自我精进教练 - 差距分析与RULES.md优化工具
"""

import re
from datetime import datetime
from pathlib import Path


class GapAnalyzer:
    """差距分析器"""

    def __init__(self, rules_path: str = None):
        self.rules_path = Path(rules_path) if rules_path else None

    def analyze_terminology(self, actor_answer: str, standard_answer: str) -> list:
        """分析用词差距"""
        gaps = []

        # 常见不专业用词映射
        terminology_map = {
            "加快": "促进",
            "变慢": "抑制",
            "变少": "减少",
            "变多": "增加",
            "影响": "[需明确：促进/抑制]",
            "重要": "[需具体化：是...所必需的]",
            "有用": "[需具体化]",
            "没关系": "无影响",
            "没作用": "无影响",
        }

        for informal, formal in terminology_map.items():
            if informal in actor_answer and informal not in standard_answer:
                if formal in standard_answer:
                    gaps.append({
                        "informal": informal,
                        "formal": formal,
                        "reason": f"标准答案使用'{formal}'，更专业"
                    })

        # 检查是否有"是...所必需的"结构
        if "是" in standard_answer and "所必需的" in standard_answer:
            if "所必需的" not in actor_answer:
                gaps.append({
                    "informal": "[缺少必要性表述]",
                    "formal": "是...所必需的",
                    "reason": "结论需要证明必要性时，必须使用'是...所必需的'结构"
                })

        # 检查是否有"缓解了...对...的抑制"结构
        if "缓解" in standard_answer and "抑制" in standard_answer:
            if "缓解" not in actor_answer:
                gaps.append({
                    "informal": "[缺少复杂效应表述]",
                    "formal": "缓解了XX对XX的抑制",
                    "reason": "描述复杂效应时，应使用'缓解...抑制'结构"
                })

        return gaps

    def analyze_logic(self, actor_answer: str, standard_answer: str) -> dict:
        """分析逻辑差距"""
        gaps = {
            "missing_points": [],
            "hierarchy_issues": "",
            "experiment_issues": []
        }

        # 简化示例：检查关键词缺失
        keywords = ["对照组", "自变量", "因变量", "检测指标", "切除", "敲除"]
        for keyword in keywords:
            if keyword in standard_answer and keyword not in actor_answer:
                gaps["missing_points"].append(f"缺少'{keyword}'相关描述")

        # 检查层次
        hierarchy_keywords = {
            "分子": ["mRNA", "蛋白", "基因", "DNA", "RNA"],
            "细胞": ["细胞", "细胞膜", "细胞核", "细胞器"],
            "个体": ["小鼠", "植株", "个体", "生物"]
        }

        found_levels = []
        for level, keywords in hierarchy_keywords.items():
            if any(kw in actor_answer for kw in keywords):
                found_levels.append(level)

        if len(found_levels) < 2:
            gaps["hierarchy_issues"] = f"描述层次不足，只覆盖了{found_levels}，建议遵循'分子→细胞→个体'层次"

        # 实验设计检查
        if "切除" in standard_answer and "切除" not in actor_answer:
            gaps["experiment_issues"].append("缺少'切除内源'的对照组设置")

        if "检测" in standard_answer:
            # 检查是否有具体检测指标
            if "mRNA" in standard_answer and "mRNA" not in actor_answer:
                gaps["experiment_issues"].append("检测指标不具体，应明确如'measure XX mRNA relative content'")

        return gaps

    def generate_gap_report(self, actor_answer: str, standard_answer: str,
                           year: str = "", question_num: str = "",
                           question_type: str = "") -> dict:
        """生成差距分析报告"""
        terminology_gaps = self.analyze_terminology(actor_answer, standard_answer)
        logic_gaps = self.analyze_logic(actor_answer, standard_answer)

        report = {
            "question_info": {
                "year": year,
                "question_num": question_num,
                "type": question_type
            },
            "terminology_gaps": terminology_gaps,
            "logic_gaps": logic_gaps,
            "summary": {
                "terminology_main_issue": "",
                "terminology_key_improvements": [],
                "logic_main_issue": "",
                "logic_key_improvements": []
            }
        }

        # 生成摘要
        if terminology_gaps:
            report["summary"]["terminology_main_issue"] = f"发现{len(terminology_gaps)}个用词问题"
            report["summary"]["terminology_key_improvements"] = [
                f"{g['informal']} → {g['formal']}" for g in terminology_gaps[:3]
            ]

        if logic_gaps["missing_points"] or logic_gaps["experiment_issues"]:
            issues = logic_gaps["missing_points"] + logic_gaps["experiment_issues"]
            report["summary"]["logic_main_issue"] = f"发现{len(issues)}个逻辑问题"
            report["summary"]["logic_key_improvements"] = issues[:3]

        return report


class RulesUpdater:
    """RULES.md更新器"""

    def __init__(self, rules_path: str):
        self.rules_path = Path(rules_path)
        self.content = self.rules_path.read_text(encoding='utf-8') if self.rules_path.exists() else ""

    def add_checklist_item(self, item: str, source: str) -> bool:
        """添加检查清单项目"""
        # 找到检查清单部分
        checklist_pattern = r"(## 第三部分：通用检查清单.*?)(?=##|$)"
        match = re.search(checklist_pattern, self.content, re.DOTALL)

        if not match:
            return False

        checklist_section = match.group(1)

        # 创建新的检查项
        source_tag = f"[改进来源：{source}]"
        new_item = f"[ ] {item} {source_tag}"

        # 检查是否已存在
        if item in self.content:
            return False

        # 在检查清单末尾添加（在最后的注释之前）
        if "# 底线" in checklist_section:
            # 在底线检查项之后添加
            insert_pattern = r"(\[ \] 底线：.*?\n)"
            replacement = f"\\1{new_item}\n"
        else:
            # 在检查清单最后添加
            insert_pattern = r"(\[ \].*?)(?=\n\n|\n##|\n$)"
            replacement = f"\\1\n{new_item}"

        self.content = re.sub(insert_pattern, replacement, self.content, flags=re.DOTALL)
        return True

    def add_experiment_design_rule(self, rule: str, source: str) -> bool:
        """添加实验设计规则"""
        # 找到实验设计部分
        exp_section_pattern = r"(## 一、实验设计类题目.*?)(?=## 二、|$)"
        match = re.search(exp_section_pattern, self.content, re.DOTALL)

        if not match:
            return False

        source_tag = f"[改进来源：{source}]"
        new_rule = f"- {rule} {source_tag}\n"

        # 在步骤部分添加
        if "步骤：" in match.group(1):
            insert_pattern = r"(步骤：\n\n)"
            replacement = f"\\1{new_rule}"
        else:
            # 在实验设计部分末尾添加
            section_end = match.end()
            self.content = self.content[:section_end] + f"\n{new_rule}" + self.content[section_end:]

        return True

    def save(self, output_path: str = None) -> str:
        """保存更新后的内容"""
        save_path = Path(output_path) if output_path else self.rules_path
        save_path.write_text(self.content, encoding='utf-8')
        return str(save_path)


def main():
    """示例使用"""
    print("生物解题自我精进教练 - 差距分析工具")
    print("=" * 50)

    # 示例分析
    analyzer = GapAnalyzer()

    # 示例数据
    actor_answer = "给小鼠注射甲状腺激素，测量耗氧量，看代谢是否加快。"
    standard_answer = """1. 实验分组：
    甲组：切除甲状腺 + 注射生理盐水
    乙组：切除甲状腺 + 注射甲状腺激素
    丙组：假手术 + 注射生理盐水
2. 检测指标：测量各组小鼠的耗氧量（具体可操作）
3. 预期结果：甲组耗氧量降低，乙组恢复正常，丙组正常
4. 结论：甲状腺激素是维持小鼠正常新陈代谢速率所必需的。"""

    report = analyzer.generate_gap_report(
        actor_answer, standard_answer,
        year="2023", question_num="第31题",
        question_type="实验设计题"
    )

    print("\n差距分析报告：")
    print(f"题目：{report['question_info']['year']}年{report['question_info']['question_num']}")
    print(f"题型：{report['question_info']['type']}")

    if report['terminology_gaps']:
        print("\n用词差距：")
        for gap in report['terminology_gaps']:
            print(f"  {gap['informal']} → {gap['formal']}: {gap['reason']}")

    if report['logic_gaps']['missing_points']:
        print("\n缺失要点：")
        for point in report['logic_gaps']['missing_points']:
            print(f"  - {point}")

    if report['logic_gaps']['experiment_issues']:
        print("\n实验设计问题：")
        for issue in report['logic_gaps']['experiment_issues']:
            print(f"  - {issue}")

    print("\n摘要：")
    print(f"用词主要问题：{report['summary']['terminology_main_issue']}")
    print(f"逻辑主要问题：{report['summary']['logic_main_issue']}")


if __name__ == "__main__":
    main()
