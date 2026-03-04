# 实验项目2：游览步骤的实体识别

## 对应科研点
基于大语言模型和归纳推理的实体类型识别。

## 实验目标
识别程序性文本中的核心要素（景点POI、交通方式、时间节点）。

## 实验主要内容
1. **实体识别**：使用Jieba分词+自定义词典或LangChain调用LLM方法，从实验1预处理后的文本中识别三类实体（景点POI、交通方式、时间节点）。
2. **归纳推理**：对比多个景区的识别结果，归纳出适用于景区领域的实体类型体系，形成实体定义规范表。
3. **可视化分析**：绘制各类实体的词频统计图（词云或柱状图），根据可视化结果添加停用词，优化实体提取质量。
4. **成果输出**：输出实体定义规范表、JSON格式的实体文件（包含每个实体的出现位置）、词频可视化图表。

## 实验技术方法
1. **分词工具**：Jieba分词，可自定义词典。
2. **LLM调用**：LangChain框架，设计Prompt调用OpenAI API或本地模型。
3. **可视化**：Matplotlib、WordCloud库。
4. **数据存储**：JSON格式。

## 实验主要步骤
1. 构建Jieba自定义词典，实现基于词典的实体识别，记录识别结果。或者，使用LangChain设计Prompt，调用LLM进行实体识别。
2. 统计实体词频，绘制词云/柱状图，根据可视化调整停用词，重新识别并优化。
3. 整理实体定义规范表，导出JSON文件，保存可视化图表。

---

## 脚本操作指南

### 文件结构
- `entity_extraction.py`: 实体提取主程序 (Jieba分词实现)
- `generate_wordcloud.py`: 词云生成程序
- `inspect_official_route.py`: 官方路线检查工具
- `test_extraction.py`: 提取测试脚本
- `custom_dicts/`: 自定义词典 (poi, transport, time)
  - `poi/`: 包含各景区POI词典 (taishan.txt, xihu.txt, zhangjiajie.txt)
  - `transport.txt`: 交通方式词典
  - `time.txt`: 时间词典

### 运行步骤

1. **安装依赖**：
   ```bash
   pip install jieba wordcloud matplotlib
   ```

2. **维护词典**：
   检查 `custom_dicts/poi/` 下的 `taishan.txt`, `xihu.txt`, `zhangjiajie.txt`，确保包含正确的景点名称。

3. **提取实体**：
   ```bash
   python entity_extraction.py
   ```
   这将生成 `output/entity_results.json`。

4. **生成可视化**：
   ```bash
   python generate_wordcloud.py
   ```
   词云图将输出到 `output/wordcloud/` 目录，包含各景区的 POI、时间、交通词云图。
