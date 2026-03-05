# 实验项目6：多源程序性知识的融合与图谱可视化

## 对应科研点
知识图谱构建与表示。

## 实验目标
将不同来源（官网、游记）的知识整合，并进行图形化展示。

## 实验主要内容
1. **数据融合**：将实验3输出的官方路线结构化数据与实验2提取的实体（景点、交通、时间）进行融合，建立实体间的关联。同时可融入实验5的条件性建议作为边属性。
2. **图谱构建**：使用图数据库（Neo4j）或图分析库（NetworkX）构建知识图谱，定义节点类型（景点、操作、时间等）和边类型（先后顺序、条件关系、包含关系等）。
3. **可视化**：绘制知识图谱，展示至少一个景区的完整游览知识网络，突出关键节点和关系。

## 实验技术方法
1. **图数据库**：Neo4j（使用Cypher查询语言）或NetworkX。
2. **可视化**：Neo4j Browser、Matplotlib（NetworkX绘图）、PyVis等。
3. **数据整合**：Python脚本处理JSON数据，生成节点和关系列表。

## 实验主要步骤
1. 整合实验3和实验2的输出数据，设计图谱的节点类型和关系类型，生成节点和边的CSV文件。
2. 将数据导入Neo4j（或使用NetworkX构建图），并编写查询/绘图代码生成可视化图谱。
3. 调整图谱布局，截取关键部分，保存可视化结果，并简单分析图谱中的核心节点和路径。

---

## 脚本操作指南

### 文件结构
- `data_loader.py`: 数据加载与融合
- `graph_builder.py`: 图谱构建 (NetworkX)
- `visualizer.py`: 可视化
- `main.py`: 主程序
- `config/`: 配置文件
  - `node_types.json`: 节点类型定义
  - `edge_types.json`: 边类型定义
- `output/`: 输出结果
  - `knowledge_graph/`: 图谱数据 (JSON)
    - `*_fused.json`: 融合后的数据
    - `*_graph.json`: 图谱结构数据
    - `*_quality_report.json`: 质量报告
  - `visualizations/`: 可视化图片

### 运行步骤

1. **执行融合与构建**：
   ```bash
   python main.py
   ```
   支持参数：`--fusion` (仅融合), `--build` (仅构建), `--visualize` (仅可视化), `--spot 泰山` (指定景区)。

2. **结果检查**：
   查看 `output/knowledge_graph/` 下的 JSON 图谱数据和 `output/visualizations/` 下的图片。
