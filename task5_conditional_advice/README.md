# 实验项目5：条件性游览建议的抽取

## 对应科研点
程序性知识的复杂依赖关系抽取（捕捉实际场景中的依赖）。

## 实验目标
挖掘文本中的条件逻辑，如“如果下雨，则...”、“如果带老人，则...”。

## 实验主要内容
1. **条件触发词识别**：设计规则或利用语义角色标注，识别表示条件的触发词（如果、假如、建议、若是等），提取条件句中的条件部分和建议部分。
2. **映射表构建**：将提取的“条件→建议”对整理成结构化映射表（如Excel或JSON），包含条件类型、条件描述、建议内容、来源景区等字段。
3. **高阶分析**：分析不同类型游客（亲子、老人、情侣）获得的建议差异，从建议数量、条件类型分布、景区间差异三个维度进行对比，并可视化展示。

## 实验技术方法
1. **规则抽取**：正则表达式匹配条件句型。
2. **语义角色标注**：可调用LTP、HanLP或LLM辅助识别。
3. **数据分析与可视化**：Pandas、Matplotlib。

## 实验主要步骤
1. 编写规则从游记和官方指南中抽取条件性建议，生成初步的映射表。
2. 人工校验并补充缺失的条件，完善映射表，保存为JSON/Excel。
3. 对映射表按游客类型分组统计，绘制对比柱状图。
4. 整理输出（映射表、分析图表）。

---

## 脚本操作指南

### 文件结构
- `config/`: 包含条件触发词和正则表达式配置
  - `condition_classification.json`: 条件分类规则
  - `condition_patterns.json`: 条件句式模式
  - `visitor_type_patterns.json`: 游客类型识别规则
- `processor.py`: 抽取逻辑
- `analyzer.py`: 分析逻辑
- `visualizer.py`: 可视化逻辑
- `main.py`: 主程序
- `visitor_classifier.py`: 游客类型分类器
- `output/`: 输出结果
  - `conditional_advice.json`: 提取的条件建议
  - `condition_mapping.json`: 条件-建议映射
  - `visitor_analysis.json`: 游客类型分析结果
  - `statistics_report.json`: 统计报告
  - `visualizations/`: 可视化图表 (advice_network.png, condition_distribution.png, scenic_spot_comparison.png, visitor_comparison.png)

### 运行步骤

1. **运行完整流程**：
   ```bash
   python main.py
   ```

2. **分步运行**（可选）：
   ```bash
   python main.py --extract    # 仅提取条件建议
   python main.py --analyze    # 仅分析结果
   python main.py --visualize  # 仅生成可视化
   python main.py --evaluate   # 仅评估结果
   ```

3. **结果检查**：
   查看 `output/` 目录下的 JSON 数据和可视化图表。
