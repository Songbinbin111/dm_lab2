#!/usr/bin/env python3
"""
任务3：游览路线的层级结构挖掘 - 主程序

功能：
1. 分析官方指南中的路线描述方式
2. 构建时间维度的游览层级结构
3. 比较官方推荐路线和游客实际路线的结构差异
"""

import os
import json
from typing import Dict
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import numpy as np

# 先设置中文字体
from matplotlib.font_manager import FontProperties

def setup_matplotlib_font():
    """设置matplotlib中文字体"""
    import platform
    from matplotlib import font_manager
    system = platform.system()

    # 常见中文字体路径
    font_paths = []
    if system == 'Darwin':  # macOS
        font_paths = ['/System/Library/Fonts/PingFang.ttc', '/Library/Fonts/Arial Unicode.ttf']
    elif system == 'Windows':
        font_paths = ['C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/simhei.ttf']
    else:  # Linux
        font_paths = ['/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc']

    found_font = False
    for path in font_paths:
        if os.path.exists(path):
            try:
                # 显式注册字体文件
                font_manager.fontManager.addfont(path)
                # 获取该字体文件对应的家族名称
                prop = font_manager.FontProperties(fname=path)
                font_name = prop.get_name()
                
                # 设置为默认字体
                matplotlib.rcParams['font.sans-serif'] = [font_name, 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
                matplotlib.rcParams['font.family'] = 'sans-serif'
                found_font = True
                break
            except Exception as e:
                print(f"警告: 无法加载字体 {path}: {e}")

    if not found_font:
        # 最后的兜底方案：尝试常见的系统字体名称
        matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'STHeiti']

    matplotlib.rcParams['axes.unicode_minus'] = False

setup_matplotlib_font()

from route_parser import RouteParser, TimeHierarchyBuilder
from route_analyzer import RouteComparator, load_visitor_data, generate_comparison_report


def get_chinese_font():
    """获取中文字体路径"""
    import platform
    system = platform.system()

    if system == 'Darwin':  # macOS
        fonts = [
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/Library/Fonts/Arial Unicode.ttf'
        ]
    elif system == 'Windows':
        fonts = [
            'C:/Windows/Fonts/simhei.ttf',
            'C:/Windows/Fonts/msyh.ttc',
        ]
    else:  # Linux
        fonts = [
            '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        ]

    for font in fonts:
        if os.path.exists(font):
            return font
    return None

def visualize_generic_sequence(hierarchy: Dict, output_path: str, title: str):
    """通用序列结构可视化"""
    parsed_data = hierarchy.get('parsed', {})
    routes = parsed_data.get('routes', [])
    if not routes:
        route_hierarchy = hierarchy.get('hierarchy', {})
        if '游览路线' not in route_hierarchy and 'hierarchy' in route_hierarchy:
             route_hierarchy = route_hierarchy.get('hierarchy', {})
        full_sequence = route_hierarchy.get('游览路线', {}).get('full_sequence', [])
        routes = [{"poi": poi} for poi in full_sequence]

    if not routes:
        print(f"Warning: No routes found for {title}")
        return

    fig, ax = plt.subplots(figsize=(12, 6))
    
    pois = [r['poi'] for r in routes]
    x = range(len(pois))
    y = [0] * len(pois)
    
    ax.plot(x, y, 'o-', markersize=10, color='#87CEEB', lw=2)
    
    for i, poi in enumerate(pois):
        ax.text(i, 0.1, poi, ha='center', rotation=45, fontsize=10)
        ax.text(i, -0.1, str(i+1), ha='center', fontsize=10)
        
    ax.set_title(f'{title} - 游览路线序列', fontsize=14)
    ax.axis('off')
    ax.set_ylim(-1, 1)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def visualize_time_hierarchy(hierarchy_data: Dict, scenic_spot: str, output_path: str):
    """可视化时间层级结构"""
    scenic_spot = hierarchy_data.get('scenic_spot', scenic_spot)
    structure_type = hierarchy_data.get('structure_type', 'unknown')

    if structure_type == "time_based" or scenic_spot in ["泰山", "西湖", "张家界"]:
        # 使用基于时间的通用层级可视化
        visualize_time_based_hierarchy(hierarchy_data, output_path, scenic_spot)
    else:
        # 通用可视化（序列结构）
        visualize_generic_sequence(hierarchy_data, output_path, scenic_spot)

def visualize_time_based_hierarchy(hierarchy: Dict, output_path: str, title: str):
    """可视化基于时间的层级结构（适配泰山、西湖等）"""
    hierarchy_data = hierarchy.get('hierarchy', {})
    
    # 兼容处理：如果hierarchy_data包含'游览路线'键（如泰山数据）
    if '游览路线' in hierarchy_data:
        # 尝试将序列转换为时间结构，或提取已有的时间结构
        # 这里假设 hierarchy_data 已经是按时间组织的，如果不是，需要转换
        # 简单起见，如果不是标准的时间键，我们回退到序列可视化
        if not any(k in hierarchy_data for k in ["上午", "中午", "下午"]):
            visualize_generic_sequence(hierarchy, output_path, title)
            return

    fig, ax = plt.subplots(figsize=(14, 8))

    # 构建层级数据
    periods = list(hierarchy_data.keys())
    period_order = ["清晨", "早上", "上午", "中午", "下午", "傍晚", "晚上"]
    periods = [p for p in period_order if p in periods]

    y_positions = []
    pois_by_period = []
    
    # 收集数据
    for period in periods:
        activities = hierarchy_data[period].get('activities', [])
        if not activities:
             continue
        pois = [act['poi'] for act in activities]
        pois_by_period.extend(pois)
        y_positions.extend([period] * len(pois))

    if not pois_by_period:
        
        parsed_data = hierarchy.get('parsed', {})
        routes = parsed_data.get('routes', [])
        if routes:
             print(f"Warning: No time-based data found for {title}, but routes exist. Falling back to sequence.")
             plt.close()
             visualize_generic_sequence(hierarchy, output_path, title)
             return
             
        print(f"Warning: No valid data found for {title} visualization.")
        plt.close()
        return

    # 创建散点图
    x_data = list(range(len(pois_by_period)))
    y_data = y_positions

    # 按时段给不同颜色
    colors = []
    color_map = {
        "清晨": "#FFD700",
        "早上": "#FFD700",
        "上午": "#87CEEB",
        "中午": "#FF6347",
        "下午": "#9370DB",
        "傍晚": "#FFA500",
        "晚上": "#4169E1"
    }
    for y in y_data:
        colors.append(color_map.get(y, "#CCCCCC"))

    plt.scatter(x_data, y_data, c=colors, s=300, alpha=0.7, edgecolors='black', linewidths=1)

    # 连接线
    plt.plot(x_data, y_data, color='gray', linestyle='--', alpha=0.3, zorder=0)

    # 添加POI标签
    for i, (x, y, poi) in enumerate(zip(x_data, y_data, pois_by_period)):
        plt.annotate(poi, (x, y), xytext=(0, 15), textcoords='offset points',
                    ha='center', va='bottom', fontsize=9, alpha=0.9, fontweight='bold',
                    rotation=45 if len(poi) > 4 else 0)
        # 添加序号
        plt.text(x, y, str(i+1), ha='center', va='center', fontsize=8, color='white', fontweight='bold')

    plt.xlabel('游览顺序', fontsize=12)
    plt.ylabel('时段', fontsize=12)
    plt.title(f'{title} - 时间维度游览层级结构', fontsize=16, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    # 调整Y轴顺序
    plt.yticks(range(len(periods)), periods)
    # 但由于我们直接用了字符串作为y数据，matplotlib会自动处理分类轴，但顺序可能不对
    # 更好的做法是映射到整数
    
    # 重新绘制（修正Y轴为数值以控制顺序）
    plt.clf()
    fig, ax = plt.subplots(figsize=(14, 8))
    
    y_map = {p: i for i, p in enumerate(period_order)}
    y_numeric = [y_map[y] for y in y_data]
    
    # 绘制背景带
    for i, period in enumerate(period_order):
        color = color_map.get(period, "#CCCCCC")
        plt.axhspan(i-0.4, i+0.4, alpha=0.1, color=color)
    
    # 连接线
    plt.plot(x_data, y_numeric, color='gray', linestyle='--', alpha=0.5, zorder=1)
    
    # 散点
    plt.scatter(x_data, y_numeric, c=colors, s=400, alpha=0.9, edgecolors='black', linewidths=1.5, zorder=2)
    
    # 标签
    for i, (x, y_idx, poi) in enumerate(zip(x_data, y_numeric, pois_by_period)):
        plt.annotate(poi, (x, y_idx), xytext=(0, 20), textcoords='offset points',
                    ha='center', va='bottom', fontsize=10, fontweight='bold',
                    rotation=45 if len(poi) > 3 else 0,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.7))
        plt.text(x, y_idx, str(i+1), ha='center', va='center', fontsize=9, color='white', fontweight='bold')

    plt.yticks(range(len(period_order)), period_order)
    plt.ylim(-0.5, len(period_order)-0.5)
    
    # 只显示存在的时段
    existing_indices = sorted(list(set(y_numeric)))
    plt.ylim(min(existing_indices)-0.5, max(existing_indices)+0.5)
    
    plt.xlabel('游览进程', fontsize=12)
    plt.title(f'{title} - 游览路线时空层级图', fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def visualize_comparison(comparison_data: Dict, output_path: str):
    """可视化对比结果"""
    reports = comparison_data.get('reports', [])

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('官方路线 vs 游客路线对比分析', fontsize=18, fontweight='bold')

    # 提取数据
    scenic_spots = []
    coverage_scores = []
    route_scores = []
    time_scores = []
    official_counts = []
    visitor_counts = []
    overlap_counts = []
    unmatched_counts = []

    for report in reports:
        spot = report.get('scenic_spot', '')
        coverage = report.get('coverage_comparison', {})
        route_similarity = report.get('route_similarity', {})
        time_dist = report.get('time_distribution', {})

        scenic_spots.append(spot)
        coverage_scores.append(coverage.get('jaccard_similarity', 0))
        route_scores.append(route_similarity.get('combined_similarity', coverage.get('jaccard_similarity', 0)))
        time_scores.append(time_dist.get('distribution_similarity', 0))
        official_counts.append(coverage.get('official_poi_count', 0))
        visitor_counts.append(coverage.get('visitor_poi_count', 0))
        overlap_counts.append(coverage.get('overlap_count', 0))
        unmatched_counts.append(coverage.get('unmatched_poi_count', 0))

    x = list(range(len(scenic_spots)))
    width = 0.22

    # 1. 景点数量对比
    ax1 = axes[0, 0]
    ax1.bar([i - 1.5 * width for i in x], official_counts, width, label='官方景点数', color='#FFD700')
    ax1.bar([i - 0.5 * width for i in x], visitor_counts, width, label='游客对齐景点数', color='#87CEEB')
    ax1.bar([i + 0.5 * width for i in x], overlap_counts, width, label='重合景点数', color='#9370DB')
    ax1.bar([i + 1.5 * width for i in x], unmatched_counts, width, label='未对齐词数', color='#FF7F50')
    ax1.set_xlabel('景区', fontsize=12)
    ax1.set_ylabel('数量', fontsize=12)
    ax1.set_title('景点覆盖度与对齐质量', fontsize=14)
    ax1.set_xticks(x)
    ax1.set_xticklabels(scenic_spots)
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')

    # 2. 路线相似度（集合 + 顺序）
    ax2 = axes[0, 1]
    colors = ['#FFD700', '#87CEEB', '#9370DB']
    ax2.bar(scenic_spots, route_scores, color=colors[:len(scenic_spots)])
    ax2.set_xlabel('景区', fontsize=12)
    ax2.set_ylabel('相似度', fontsize=12)
    ax2.set_title('路线相似度 (LCS+Jaccard 组合)', fontsize=14)
    ax2.set_ylim(0, 1)
    ax2.grid(True, alpha=0.3, axis='y')

    # 添加数值标签
    for i, (spot, score) in enumerate(zip(scenic_spots, route_scores)):
        ax2.text(i, score + 0.02, f'{score:.3f}', ha='center', fontsize=10)

    # 3. 时间分布相似度（全部景区）
    ax3 = axes[1, 0]
    ax3.bar(scenic_spots, time_scores, color=colors[:len(scenic_spots)])
    ax3.set_xlabel('景区', fontsize=12)
    ax3.set_ylabel('相似度', fontsize=12)
    ax3.set_title('时间分布相似度', fontsize=14)
    ax3.set_ylim(0, 1)
    ax3.grid(True, alpha=0.3, axis='y')
    for i, score in enumerate(time_scores):
        ax3.text(i, score + 0.02, f'{score:.3f}', ha='center', fontsize=10)

    # 4. 评估摘要
    ax4 = axes[1, 1]
    ax4.axis('off')

    summary_text = "对比分析摘要\n" + "="*30 + "\n\n"

    for report in reports:
        spot = report.get('scenic_spot', '')
        summary = report.get('summary', {})
        coverage = report.get('coverage_comparison', {})
        coverage_level = summary.get('coverage_level', '')
        route_level = summary.get('route_similarity_level', '')
        time_level = summary.get('time_distribution_level', '')
        key_findings = summary.get('key_findings', [])

        summary_text += f"【{spot}】\n"
        summary_text += f"覆盖评估: {coverage_level}\n"
        summary_text += f"路线评估: {route_level}\n"
        summary_text += f"时间评估: {time_level}\n"
        summary_text += (
            f"未对齐词: {coverage.get('unmatched_poi_count', 0)} "
            f"(清洗后总词 {coverage.get('cleaned_unique_count', 0)})\n"
        )

        for finding in key_findings:
            summary_text += f"  • {finding}\n"

        summary_text += "\n"

    ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes,
            fontsize=11, verticalalignment='top', family='sans-serif')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def main():
    """主函数"""
    print("=" * 60)
    print("任务3：游览路线的层级结构挖掘")
    print("=" * 60)

    # 创建输出目录
    for dir_name in ['hierarchies', 'comparisons']:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

    # 景区映射
    spot_en_map = {
        '泰山': 'taishan',
        '西湖': 'xihu',
        '张家界': 'zhangjiajie'
    }

    # 加载数据
    print("\n[1/4] 加载数据...")
    df = pd.read_excel('../task1_data_collection/data/data_cleaned.xlsx')
    visitor_data = load_visitor_data('../task2_entity_recognition/entity_results.json')

    # 解析官方路线
    print("\n[2/4] 解析官方路线...")

    official_data = {}
    hierarchy_data = {}

    for idx, row in df.iterrows():
        scenic_spot = row['景区名称']
        route_text = row['官方游览路线']

        if pd.isna(route_text):
            continue

        print(f"  解析 {scenic_spot}...")

        # 解析路线
        parsed = RouteParser.parse(scenic_spot, route_text)
        official_data[scenic_spot] = {"parsed": parsed}

        # 构建层级结构
        hierarchy = TimeHierarchyBuilder.build_hierarchy(parsed)
        hierarchy_data[scenic_spot] = hierarchy

        # 保存层级数据
        hierarchy_file = f'hierarchies/{scenic_spot}_hierarchy.json'
        with open(hierarchy_file, 'w', encoding='utf-8') as f:
            json.dump({"parsed": parsed, "hierarchy": hierarchy}, f,
                     ensure_ascii=False, indent=2)

    # 生成对比报告
    print("\n[3/4] 生成对比分析...")

    all_reports = []

    for scenic_spot in spot_en_map.keys():
        if scenic_spot not in official_data or scenic_spot not in visitor_data:
            continue

        print(f"  分析 {scenic_spot}...")

        report = generate_comparison_report(
            scenic_spot,
            official_data[scenic_spot],
            visitor_data[scenic_spot]
        )

        all_reports.append(report)

    # 保存对比报告
    full_report = {
        "generated_at": str(pd.Timestamp.now()),
        "total_spots": len(all_reports),
        "reports": all_reports
    }

    with open('comparisons/comparison_report.json', 'w', encoding='utf-8') as f:
        json.dump(full_report, f, ensure_ascii=False, indent=2)

    # 生成可视化图表
    print("\n[4/4] 生成可视化图表...")

    # 层级结构图
    for scenic_spot in spot_en_map.keys():
        if scenic_spot in hierarchy_data:
            print(f"  生成 {scenic_spot} 层级结构图...")
            output_path = f'hierarchies/{scenic_spot}_hierarchy.png'
            visualize_time_hierarchy(hierarchy_data[scenic_spot], scenic_spot, output_path)

    # 对比分析图
    print("  生成对比分析图...")
    visualize_comparison(full_report, 'comparisons/comparison_charts.png')

    # 打印摘要
    print("\n" + "=" * 60)
    print("任务3完成！")
    print("=" * 60)
    print("\n输出文件:")
    print("  - hierarchies/*.json  : 层级结构数据")
    print("  - hierarchies/*.png  : 层级结构可视化")
    print("  - comparisons/comparison_report.json : 对比分析报告")
    print("  - comparisons/comparison_charts.png  : 对比分析图表")
    print()


if __name__ == '__main__':
    main()
