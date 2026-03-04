# 实验项目4：程序性知识的共指消解

## 对应科研点
先行词共指消解技术。

## 实验目标
解决文本中代词（它、这、那里）指代不明的问题。

## 实验主要内容
1. **代词检测**：使用正则匹配和Jieba分句，从游记或路线文本中检测出所有代词及其所在句子。
2. **指代消解实现**：采用至少一种方法进行指代消解，例如：手工标注少量样本，训练一个简单的分类模型；调用现有的指代消解模型（如HuggingFace上的coref模型）；基于最近名词匹配的规则（查找代词前文最近出现的实体）。
3. **效果评估**：对消解结果进行人工验证，统计准确率，并输出消解后的文本或知识三元组。

## 实验技术方法
1. **代词检测**：正则表达式、Jieba分词。
2. **指代消解**：可选用Transformers库中的指代消解pipeline（如allenai/longformer-base-4096）、自建规则、或调用LLM进行推理。
3. **评估**：人工抽样检查。

## 实验主要步骤
1. 编写代词检测脚本，从3-5篇游记中提取含代词的句子，生成待消解列表。
2. 实现并运行指代消解方法（规则或模型），记录消解结果。
3. 人工评估5个消解案例的准确性，总结方法的优缺点，输出消解后的文本示例。

---

## 脚本操作指南

### 文件结构
- `coref_extractor.py`: 代词提取与规则消解
- `evaluator.py`: 评估模块
- `visualizer.py`: 可视化模块
- `main.py`: 主程序
- `annotated/`: 手工标注数据
  - `manual_annotations.json`: 手工标注的共指消解数据
- `output/`: 输出结果
  - `auto_resolution_results.json`: 自动消解结果
  - `pronoun_sentences.json`: 提取的含代词句子
  - `statistics_report.json`: 统计报告
  - `evaluation_report.json` / `evaluation_report.xlsx`: 评估报告
  - `visualizations/`: 可视化图表

### 运行步骤

1. **运行完整流程**：
   ```bash
   python main.py
   ```

2. **分步运行**（可选）：
   ```bash
   python main.py --extract    # 仅提取代词并进行自动消解
   python main.py --evaluate   # 仅评估结果（需先有手工标注）
   python main.py --visualize  # 仅生成可视化
   ```

3. **结果检查**：
   输出位于 `output/` 目录，包含 JSON 结果、评估报告和可视化图表。
