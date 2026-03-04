#!/usr/bin/env python3
"""
路线解析器 - 解析不同格式的官方游览路线
支持三种格式：
1. 泰山格式：箭头连接（类似于序列）
2. 西湖格式：景点序列
3. 张家界格式：可能包含多线路或箭头连接
"""

import re
import json
import jieba
import os
from typing import Dict, List, Any, Optional

# POI 缓存
_POI_CACHE = {}

def load_poi_dict(spot_name: str) -> set:
    """加载景区POI词典"""
    global _POI_CACHE
    
    # 映射表
    name_map = {
        '西湖': 'xihu',
        '泰山': 'taishan',
        '张家界': 'zhangjiajie'
    }
    
    dict_name = name_map.get(spot_name, spot_name)
    if dict_name in _POI_CACHE:
        return _POI_CACHE[dict_name]
        
    pois = set()
    # 尝试加载文件
    # 假设当前脚本在 task3 目录，词典在 ../task2_entity_recognition/custom_dicts/poi
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        dict_path = os.path.join(current_dir, f'../task2_entity_recognition/custom_dicts/poi/{dict_name}.txt')
        
        if os.path.exists(dict_path):
            with open(dict_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if parts:
                        pois.add(parts[0])
                        # 同时也把 POI 加入 jieba，以便分词
                        jieba.add_word(parts[0])
    except Exception as e:
        print(f"Error loading POI dict for {spot_name}: {e}")
        
    _POI_CACHE[dict_name] = pois
    return pois

def get_time_period(time_str: str) -> str:
    """将时间字符串映射到时段（上午/中午/下午/晚上）"""
    # 提取小时数
    hour_match = re.search(r'(\d{1,2}):', time_str)
    if hour_match:
        hour = int(hour_match.group(1))
        if 5 <= hour < 9:
            return "清晨"
        elif 9 <= hour < 11:
            return "上午"
        elif 11 <= hour < 13:
            return "中午"
        elif 13 <= hour < 17:
            return "下午"
        elif 17 <= hour < 19:
            return "傍晚"
        else:
            return "晚上"
    return "未知时段"


def parse_arrow_route(text: str, spot_name: str) -> Dict[str, Any]:
    """
    通用解析器：解析带有箭头和详细信息的路线
    格式：[上午]A(详情)→B(详情) B→C(详情) ...
    """
    routes = []
    
    # 预处理：将中文括号转为英文括号，方便正则
    text = text.replace('（', '(').replace('）', ')')
    
    # 迭代查找 "A→B(details)"
    matches = list(re.finditer(r'([^→\s\[\]：:.,，。]+(?:[(][^)]+[)])?)\s*→\s*([^→\s\[\]：:.,，。(]+)(?:\(([^)]+)\))?', text))
    
    for i, match in enumerate(matches):
        start_node = match.group(1).strip()
        end_node = match.group(2).strip()
        details = match.group(3) # Optional, can be None
        if details:
            details = details.strip()
        else:
            details = ""
        
        # 清理 start_node，如果它包含上一段的残留（虽然正则[^→]应该避免了，但为了保险）
        start_pure = re.sub(r'\(.*?\)', '', start_node).strip()
        
        # 提取时间
        time_range = ""
        period = "未知时段"
        time_match = re.search(r'(\d{1,2}:\d{2}-\d{1,2}:\d{2})', details)
        if time_match:
            time_range = time_match.group(1)
            # Use start time to guess period
            start_time = time_range.split('-')[0]
            period = get_time_period(start_time)
        elif "上午" in text:
            period = "上午" # Crude fallback
            
        # 提取时长
        duration = ""
        dur_match = re.search(r'游览时间\s*(\d+\s*分钟|\d+\s*小时)', details)
        if dur_match:
            duration = dur_match.group(1)
            
        routes.append({
            "from_poi": start_pure,
            "to_poi": end_node,
            "poi": end_node,
            "time_range": time_range,
            "period": period,
            "duration": duration,
            "details": details,
            "full_text": match.group(0)
        })
        
    # 提取所有 POI
    all_pois = set()
    if routes:
        all_pois.add(routes[0]['from_poi'])
    for r in routes:
        all_pois.add(r['to_poi'])
        
    sorted_pois = sorted(list(all_pois)) # 简单排序
    
    return {
        "scenic_spot": spot_name,
        "route_format": "arrow_text",
        "total_pois": len(all_pois),
        "pois": sorted_pois,
        "routes": routes
    }


def parse_narrative_route(text: str, spot_name: str) -> Dict[str, Any]:
    """
    解析叙述性路线（针对西湖等长文本）
    """
    pois_set = load_poi_dict(spot_name)
    if not pois_set:
        print(f"Warning: No POI dict found for {spot_name}")
        
    routes = []
    
    # 分句
    sentences = re.split(r'[，。；！!？?]', text)
    
    current_period = "未知时段"
    # 时间词映射
    time_keywords = {
        "清晨": ["清晨", "日出前", "早起"],
        "早上": ["早上", "早点"],
        "上午": ["上午"],
        "中午": ["中午", "午餐", "用餐"],
        "下午": ["下午"],
        "傍晚": ["傍晚", "日落", "夕阳"],
        "晚上": ["晚上", "夜景", "夜游"]
    }
    
    # 动作词（辅助判断）
    actions = ["出发", "前往", "打卡", "游览", "抵达", "到达", "参观", "登上"]
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # 1. 更新时段
        for period, keywords in time_keywords.items():
            if any(kw in sentence for kw in keywords):
                current_period = period
                break
        
        # 2. 提取 POI
        # 方法 A: 使用 jieba 分词
        words = jieba.cut(sentence)
        found_pois_in_sentence = []
        for word in words:
            if word in pois_set and len(word) > 1:
                found_pois_in_sentence.append(word)
        
        # 方法 B: 直接匹配（补充 jieba 可能分错的情况）
        # 对于每个已知 POI，检查是否在句子中
        # 为了效率，只在没找到时尝试，或者作为补充
        # 这里为了简单，如果方法 A 没找到，再尝试部分匹配
        if not found_pois_in_sentence:
             for poi in pois_set:
                 if poi in sentence:
                     found_pois_in_sentence.append(poi)
        
        # 去重但保持顺序
        seen = set()
        unique_pois = []
        for p in found_pois_in_sentence:
            if p not in seen:
                unique_pois.append(p)
                seen.add(p)
                
        # 3. 构建 route 对象
        for poi in unique_pois:
            # 尝试查找关联的动作
            details = sentence
            
            routes.append({
                "from_poi": "", # 叙述性文本很难确定确切的起点，留空
                "to_poi": poi,
                "poi": poi,
                "time_range": "",
                "period": current_period,
                "duration": "",
                "details": details,
                "full_text": sentence
            })

    # 后处理：去重？
    # 西湖文本包含多条线路，可能会有重复 POI
    # 我们保留所有提取到的 POI，按顺序排列
    
    # 提取所有 POI 列表
    all_pois = []
    seen_pois = set()
    for r in routes:
        if r['poi'] not in seen_pois:
            all_pois.append(r['poi'])
            seen_pois.add(r['poi'])
            
    return {
        "scenic_spot": spot_name,
        "route_format": "narrative_text",
        "total_pois": len(all_pois),
        "pois": all_pois,
        "routes": routes
    }

class RouteParser:
    """路线解析器 - 统一接口"""

    @staticmethod
    def parse(scenic_spot: str, route_text: str) -> Dict[str, Any]:
        """根据景区类型解析路线"""
        # 1. 尝试使用箭头解析器
        result = parse_arrow_route(route_text, scenic_spot)
        
        # 如果箭头解析器没有找到任何路线（routes 为空），或者数量太少
        if not result['routes'] or len(result['routes']) < 2:
            # 2. 尝试使用叙述性解析器
            print(f"Info: Arrow parser failed or insufficient for {scenic_spot}, trying narrative parser...")
            narrative_result = parse_narrative_route(route_text, scenic_spot)
            if narrative_result['routes']:
                return narrative_result
                
        return result


class TimeHierarchyBuilder:
    """时间层级结构构建器"""

    @staticmethod
    def build_hierarchy(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """构建时间维度的游览层级结构"""
        scenic_spot = parsed_data.get("scenic_spot", "")
        route_format = parsed_data.get("route_format", "")
        routes = parsed_data.get("routes", [])

        # 检查是否包含时间信息，如果包含，则构建时间层级
        has_time_info = False
        for r in routes:
            if r.get("period") and r.get("period") != "未知时段":
                has_time_info = True
                break
        
        if has_time_info:
            return TimeHierarchyBuilder._build_time_based_hierarchy(parsed_data)

        # 只要是 arrow_text 格式，都尝试构建通用序列层级
        if route_format == "arrow_text":
             return TimeHierarchyBuilder._build_sequence_hierarchy(parsed_data)
        
        return {"error": f"Unsupported format: {scenic_spot} - {route_format}"}

    @staticmethod
    def _build_time_based_hierarchy(data: Dict[str, Any]) -> Dict[str, Any]:
        """构建基于时间的层级结构"""
        hierarchy = {
            "scenic_spot": data.get("scenic_spot", "通用"),
            "structure_type": "time_based",
            "hierarchy": {}
        }
        
        routes = data.get("routes", [])
        
        # 按时段分组
        periods = ["清晨", "早上", "上午", "中午", "下午", "傍晚", "晚上"]
        grouped = {p: [] for p in periods}
        
        current_period = "未知时段"
        
        for r in routes:
            period = r.get("period", "未知时段")
            if period in periods:
                current_period = period
            
            # 如果当前路线没有时段，但之前有，则沿用
            if period == "未知时段" and current_period in periods:
                period = current_period
                
            if period in periods:
                grouped[period].append({
                    "poi": r["poi"],
                    "details": r.get("details", "")
                })
                
        # 填充层级结构
        for period in periods:
            if grouped[period]:
                hierarchy["hierarchy"][period] = {
                    "time_range": TimeHierarchyBuilder._get_period_range(period),
                    "activities": grouped[period]
                }
                
        return hierarchy

    @staticmethod
    def _build_sequence_hierarchy(data: Dict[str, Any]) -> Dict[str, Any]:
        """构建通用的序列层级结构（适用于线性游览路线）"""
        hierarchy = {
            "scenic_spot": data.get("scenic_spot", "通用"),
            "structure_type": "sequence_based",
            "hierarchy": {
                "游览路线": {
                    "sections": []
                }
            }
        }

        # 将路线分组（前、中、后）
        routes = data.get("routes", [])
        
        # Determine full sequence
        full_sequence = []
        if routes:
            # If format is arrow_text, routes are segments (from_poi -> to_poi)
            # We should include the start point of the first segment
            if "from_poi" in routes[0]:
                full_sequence.append(routes[0]["from_poi"])
            
            # Add all destination points
            full_sequence.extend([r["poi"] for r in routes])
        else:
            full_sequence = []

        total = len(full_sequence)

        # 分为三个部分 (简单平均分割)
        if total > 0:
            third = total // 3
            # 处理不能整除的情况
            p1 = third
            p2 = 2 * third
            if total % 3 == 1:
                p2 += 1
            elif total % 3 == 2:
                p1 += 1
                p2 += 1
                
            hierarchy["hierarchy"]["游览路线"]["sections"] = [
                {
                    "name": "第一阶段",
                    "pois": full_sequence[:p1]
                },
                {
                    "name": "第二阶段",
                    "pois": full_sequence[p1:p2]
                },
                {
                    "name": "第三阶段",
                    "pois": full_sequence[p2:]
                }
            ]

        hierarchy["hierarchy"]["游览路线"]["total_pois"] = total
        hierarchy["hierarchy"]["游览路线"]["full_sequence"] = full_sequence

        return hierarchy

    @staticmethod
    def _get_period_range(period: str) -> str:
        """获取时段的时间范围"""
        ranges = {
            "清晨": "5:00-9:00",
            "上午": "9:00-11:00",
            "中午": "11:00-13:00",
            "下午": "13:00-17:00",
            "傍晚": "17:00-19:00",
            "晚上": "19:00-23:00"
        }
        return ranges.get(period, "")


def main():
    """测试函数"""
    import pandas as pd
    import os

    print("=" * 60)
    print("路线解析测试")
    print("=" * 60)

    # 读取数据
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(current_dir, '../task1_data_collection/data/data_cleaned.xlsx')
        if not os.path.exists(data_path):
             data_path = '../task1_data_collection/data/data.xlsx'
             
        df = pd.read_excel(data_path)
    except Exception as e:
        print(f"读取数据失败: {e}")
        return

    for idx, row in df.iterrows():
        scenic_spot = row['景区名称']
        route_text = row['官方游览路线']

        if pd.isna(route_text):
            continue

        print(f"\n{'='*60}")
        print(f"解析 {scenic_spot} 官方路线")
        print(f"{'='*60}")

        # 解析路线
        parsed = RouteParser.parse(scenic_spot, route_text)

        # 构建层级结构
        hierarchy = TimeHierarchyBuilder.build_hierarchy(parsed)

        print(f"\n路线格式: {parsed.get('route_format', 'unknown')}")
        print(f"景点数量: {parsed.get('total_pois', 0)}")
        print(f"\n前10个景点: {parsed.get('pois', [])[:10]}")

        print(f"\n层级结构类型: {hierarchy.get('structure_type', 'unknown')}")

        # 保存结果
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'route_hierarchy')
        os.makedirs(output_dir, exist_ok=True)
        
        with open(f'{output_dir}/{scenic_spot}_hierarchy.json', 'w', encoding='utf-8') as f:
            json.dump({
                "parsed": parsed,
                "hierarchy": hierarchy
            }, f, ensure_ascii=False, indent=2)

        print(f"\n已保存: route_hierarchy/{scenic_spot}_hierarchy.json")


if __name__ == '__main__':
    main()
