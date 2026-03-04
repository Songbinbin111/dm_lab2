#!/usr/bin/env python3
"""
景区游记实体识别脚本

功能:
1. 从游记中识别三类实体：景点POI、交通方式、时间节点
2. 使用Jieba分词 + 自定义词典
3. 生成词频统计和词云图

使用方法:
    python entity_extraction.py
"""

import re
import json
import os
from datetime import datetime
from collections import Counter, defaultdict
from typing import Dict, List, Set, Optional, Tuple
from matplotlib.font_manager import FontProperties

try:
    import pandas as pd
    import jieba
    import jieba.posseg as pseg
except ImportError as e:
    print(f"错误: 需要安装缺失的库")
    print(f"请运行: pip install pandas jieba openpyxl wordcloud matplotlib")
    raise


def stable_unique(items: List[str]) -> List[str]:
    """保序去重"""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

# =============================================================================
# 1. 格式检测器
# =============================================================================

class FormatDetector:
    """数据格式检测器"""

    @staticmethod
    def detect(text: str) -> str:
        """
        检测文本格式类型

        Args:
            text: 待检测的文本

        Returns:
            格式类型: 'formatted_route', 'numbered_list', 'descriptive'
        """
        if not text:
            return 'descriptive'

        arrow_count = text.count('→')
        numbered_lines = len(re.findall(r'^\d+\.', text, re.MULTILINE))
        has_time_ranges = bool(re.search(r'\d{1,2}:\d{2}-\d{1,2}:\d{2}', text))

        if arrow_count > 5 and has_time_ranges:
            return 'formatted_route'  # 箭头路线格式
        elif numbered_lines > 5:
            return 'numbered_list'     # 编号列表格式
        else:
            return 'descriptive'       # 描述性格式


# =============================================================================
# 2. POI实体提取器
# =============================================================================

class POIExtractor:
    """景点POI实体提取器"""

    def __init__(self):
        # 加载自定义词典
        self._load_dicts()
        # 加载需要排除的词（交通和时间词典）
        self._load_exclude_dicts()
        
        # 常见景点后缀
        self.poi_suffixes = ['海', '池', '宫', '殿', '门', '峰', '阁', '寺', '松', '沟', '山', '区', '湖', '瀑', '滩', '寨', '瀑布', '景区', '索道', '站', '桥', '路', '街', '园', '洞', '溪', '界', '寨', '廊', '梯', '道', '台']
        # 高频噪声词（会被误识别为POI）
        self.poi_noise_words = {
            '热门', '门票', '门票价格', '区域', '区分', '山水', '海拔', '风景区', '景区',
            '小时', '分钟', '公里', '路线', '攻略', '旅程', '景观', '建议', '注意',
            '如果', '选择', '游览', '提前', '预约', '因为', '所以', '但是', '虽然',
            '装备', '交通', '住宿', '吃饭', '美食', '价格', '费用', '时间', '有些',
            '可以', '需要', '我们', '他们', '自己', '感觉', '觉得', '比如', '例如',
            '以及', '还有', '包含', '包括', '不用', '不要', '一定', '最好', '可能',
            '特别', '非常', '比较', '真的', '超级', '很多', '一点', '一下', '专门',
            '上山', '下山', '上海', '外滩', '北京', '中国', '有些', '那些', '这些',
             '迷路', '入园', '出园', '味道', '分段', '休息区', '商业街', '登山',
             '核心区', '云海', '日出', '索道', '缆车', '大巴', '公交', '地铁',
             '机场', '车站', '高铁', '火车', '打车', '拼车', '包车', '自驾',
             '核心', '休整', '小众', '环线', '大门', '后门', '侧门', '出口', '入口',
             '回头路', '走路', '电梯', '公园', '观景台', '天梯', '市区', '山峰', 
             '步道', '石板路', '劈山', '奇阁'
        }

    def _load_exclude_dicts(self):
        """加载需要排除的词典（交通和时间）"""
        self.exclude_words = set()
        for filename in ['transport.txt', 'time.txt']:
            path = os.path.join('custom_dicts', filename)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split()
                        if parts:
                            self.exclude_words.add(parts[0])

    def _load_dicts(self):
        """加载自定义词典"""
        dict_dir = 'custom_dicts/poi'
        self.poi_dicts = {
            'taishan': set(),
            'xihu': set(),
            'zhangjiajie': set(),
            'common': set()
        }

        # 加载各景区词典
        for spot in ['taishan', 'xihu', 'zhangjiajie']:
            dict_path = os.path.join(dict_dir, f'{spot}.txt')
            if os.path.exists(dict_path):
                with open(dict_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split()
                        if parts:
                            self.poi_dicts[spot].add(parts[0])
                            self.poi_dicts['common'].add(parts[0])

        # 为Jieba加载词典
        for spot in ['taishan', 'xihu', 'zhangjiajie']:
            dict_path = os.path.join(dict_dir, f'{spot}.txt')
            if os.path.exists(dict_path):
                jieba.load_userdict(dict_path)

    def extract(self, text: str, format_type: str, scenic_spot: str = '') -> List[str]:
        """
        提取POI实体

        Args:
            text: 待处理的文本
            format_type: 文本格式类型
            scenic_spot: 景区名称

        Returns:
            POI实体列表
        """
        if not text:
            return []

        entities = []

        # 根据格式类型使用不同的提取策略
        if format_type == 'formatted_route':
            entities.extend(self._extract_from_arrow_route(text))
        elif format_type == 'numbered_list':
            entities.extend(self._extract_from_numbered_list(text))

        # 描述性文本总是需要处理
        entities.extend(self._extract_from_descriptive(text, scenic_spot))

        # 全局清洗和过滤
        cleaned_entities = []
        for entity in entities:
            # 1. 长度过滤
            if len(entity) < 2 or len(entity) > 10:
                continue
            
            # 2. 噪声词过滤
            if entity in self.poi_noise_words:
                continue
            
            # 排除交通和时间词汇
            if entity in self.exclude_words:
                continue
                
            # 3. 数字和特殊字符过滤
            # 只允许纯中文，或者是自定义词典中的词
            # 过滤包含 / 的词
            if '/' in entity:
                continue
                
            if not re.match(r'^[\u4e00-\u9fa5]+$', entity):
                 if entity not in self.poi_dicts['common']:
                     continue
            
            # 4. 包含特定关键词的过滤（针对误提取的长词）
            noise_chars = ['票', '费', '元', '钱', '车', '住', '吃', '穿', '带', '买']
            if any(char in entity for char in noise_chars) and entity not in self.poi_dicts['common']:
                continue

            cleaned_entities.append(entity)

        # 保序去重
        return stable_unique(cleaned_entities)

    def _clean_and_validate(self, text: str, scenic_spot: str) -> List[str]:
        """清洗并验证POI（核心优化）"""
        # 1. 基础清洗：去除括号及内容
        cleaned = re.sub(r'[\(（][^\)）]+[\)）]', '', text).strip()
        if not cleaned:
            return []
            
        # 2. 如果清洗后的文本就在自定义词典中，直接返回
        if cleaned in self.poi_dicts['common']:
            return [cleaned]
            
        # 3. 使用Jieba分词提取其中的已知POI
        words = jieba.cut(cleaned)
        found_pois = []
        for word in words:
            if word in self.poi_dicts['common']:
                found_pois.append(word)
        
        if found_pois:
            return found_pois
            
        # 4. 如果没有找到已知POI，但文本看起来像是一个单一景点，尝试返回它
        # 长度检查
        if 2 <= len(cleaned) <= 10:
             # 避免返回包含大量标点的长句
             if not re.search(r'[，。；,.;]', cleaned):
                 # 再次检查后缀
                 if any(cleaned.endswith(suffix) for suffix in self.poi_suffixes):
                     return [cleaned]
        
        return []

    def _extract_from_arrow_route(self, text: str) -> List[str]:
        """从箭头路线中提取景点"""
        # 移除时间标记 [上午] 等
        text = re.sub(r'\[.*?\]', '', text)
        
        # 提取箭头连接的词
        parts = re.split(r'[→]', text)
        
        results = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            # 清洗并验证
            # 注意：scenic_spot 参数在 _extract_from_arrow_route 中没有传递进来
            # 但 _clean_and_validate 实际上只用到了 self.poi_dicts，所以不需要 scenic_spot
            # 这里为了接口一致性，我们可以暂时传空，或者修改接口
            pois = self._clean_and_validate(part, '')
            results.extend(pois)
            
        return results

    def _extract_from_numbered_list(self, text: str) -> List[str]:
        """从编号列表中提取景点"""
        lines = re.findall(r'\d+\.\s*([^\n]+)', text)
        results = []
        for line in lines:
            pois = self._clean_and_validate(line, '')
            results.extend(pois)
        return results

    def _extract_from_descriptive(self, text: str, scenic_spot: str) -> List[str]:
        """从描述性文本中提取（使用jieba分词+词性过滤）"""
        words = pseg.cut(text)
        results = []

        for word, flag in words:
            # 过滤条件：词性为地名(ns)或名词(n)，长度合适，且包含景点特征
            if flag in ['ns', 'n', 'nr'] and 2 <= len(word) <= 6:
                # 检查是否在自定义词典中
                if word in self.poi_dicts['common']:
                    results.append(word)
                # 检查是否包含景点后缀
                elif any(word.endswith(suffix) for suffix in self.poi_suffixes):
                    # 进一步过滤：不能是描述性词语
                    if word not in self.poi_noise_words and not self._is_descriptive_word(word):
                        results.append(word)

        return results

    def _is_descriptive_word(self, word: str) -> bool:
        """判断是否为描述性词语"""
        descriptive_patterns = [
            r'^[一二三四五六七八九十]+$',
            r'^\d+$',
            r'分钟|小时|时间|路程|公里|米',
            r'门票|价格|路线|攻略',
        ]
        return any(re.search(pattern, word) for pattern in descriptive_patterns)


# =============================================================================
# 3. 交通方式实体提取器
# =============================================================================

class TransportExtractor:
    """交通方式实体提取器"""

    def __init__(self):
        # 加载自定义词典
        self._load_dict()
        # 基本方式词典
        self.basic_methods = ['步行', '乘车', '缆车', '坐车', '徒步', '换乘']

    def _load_dict(self):
        """加载交通词典"""
        dict_path = 'custom_dicts/transport.txt'
        self.transport_dict = set()
        if os.path.exists(dict_path):
            with open(dict_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if parts:
                        self.transport_dict.add(parts[0])
                        jieba.add_word(parts[0], 10000, 'n')

    def extract(self, text: str) -> Dict[str, List[str]]:
        """
        提取交通方式实体

        Args:
            text: 待处理的文本

        Returns:
            分类的交通方式字典
        """
        if not text:
            return {'basic': [], 'specific': [], 'time_distance': []}

        result = {
            'basic': [],
            'specific': [],
            'time_distance': []
        }

        # 基本方式
        for method in self.basic_methods:
            if method in text:
                result['basic'].append(method)

        # 具体工具（从词典）
        for tool in self.transport_dict:
            if tool in text:
                result['specific'].append(tool)

        # 时间+距离模式
        time_distance_patterns = [
            r'\d+分钟[车程路程]',
            r'约?\d+分钟[车程路程]',
            r'\d+小时[车程路程]',
            r'\d+\.?\d*公里',
            r'半个小时',
            r'一刻钟',
        ]
        for pattern in time_distance_patterns:
            matches = re.findall(pattern, text)
            result['time_distance'].extend(matches)

        # 去重
        for key in result:
            result[key] = sorted(set(result[key]))

        return result


# =============================================================================
# 4. 时间节点实体提取器
# =============================================================================

class TimeExtractor:
    """时间节点实体提取器"""

    def __init__(self):
        # 加载自定义词典
        self._load_dict()
        # 相对时间词典
        self.relative_times = [
            '早上', '上午', '中午', '下午', '傍晚', '晚上', '清晨', '凌晨',
            '第一天', '第二天', '第三天',
        ]

    def _load_dict(self):
        """加载时间词典"""
        dict_path = 'custom_dicts/time.txt'
        self.time_dict = set()
        if os.path.exists(dict_path):
            with open(dict_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if parts:
                        self.time_dict.add(parts[0])
                        jieba.add_word(parts[0], 10000, 'r')

    def extract(self, text: str) -> Dict[str, List[str]]:
        """
        提取时间节点实体

        Args:
            text: 待处理的文本

        Returns:
            分类的时间节点字典
        """
        if not text:
            return {'exact': [], 'relative': [], 'duration': []}

        result = {
            'exact': [],
            'relative': [],
            'duration': []
        }

        # 具体时间
        exact_patterns = [
            r'\d{1,2}:\d{2}',           # 8:30
            r'\d{1,2}:\d{2}-\d{1,2}:\d{2}',  # 8:30-9:00
            r'\d{1,2}点\d{1,2}分',      # 8点30分
        ]
        for pattern in exact_patterns:
            matches = re.findall(pattern, text)
            result['exact'].extend(matches)

        # 相对时间
        for rel in self.relative_times:
            if rel in text:
                result['relative'].append(rel)

        # 持续时间
        duration_patterns = [
            r'游览时间\d+[分钟小时]+',
            r'约?\d+[分钟小时]+',
            r'半小时',
            r'一个小时',
        ]
        for pattern in duration_patterns:
            matches = re.findall(pattern, text)
            result['duration'].extend(matches)

        # 去重
        for key in result:
            result[key] = sorted(set(result[key]))

        return result


# =============================================================================
# 5. 统计分析器
# =============================================================================

class StatisticsAnalyzer:
    """词频统计与分析器"""

    def analyze(self, results: List[Dict]) -> Dict:
        """
        分析所有结果并生成统计数据

        Args:
            results: 实体提取结果列表

        Returns:
            统计数据字典
        """
        stats = {
            'poi_frequency': Counter(),
            'transport_frequency': Counter(),
            'time_frequency': Counter(),
            'top_poi': [],
            'top_transport': [],
            'top_time': []
        }

        # 收集所有实体
        for record in results:
            scenic_spot = record.get('scenic_spot', '')

            # POI统计
            for poi in record.get('poi', []):
                stats['poi_frequency'][poi] += 1

            # 交通统计
            transport = record.get('transport', {})
            for category in ['basic', 'specific', 'time_distance']:
                for item in transport.get(category, []):
                    stats['transport_frequency'][item] += 1

            # 时间统计
            time = record.get('time', {})
            for category in ['exact', 'relative', 'duration']:
                for item in time.get(category, []):
                    stats['time_frequency'][item] += 1

        # 生成Top列表
        stats['top_poi'] = self._get_top_items(stats['poi_frequency'], scenic_spot)
        stats['top_transport'] = self._get_top_items(stats['transport_frequency'])
        stats['top_time'] = self._get_top_items(stats['time_frequency'])

        return stats

    def _get_top_items(self, counter: Counter, scenic_spot: str = '') -> List[Dict]:
        """获取高频词列表"""
        return [
            {'entity': entity, 'count': count}
            for entity, count in counter.most_common(50)
        ]


# =============================================================================
# 6. 可视化器
# =============================================================================

class WordCloudGenerator:
    """词云图生成器"""

    def __init__(self):
        self._check_dependencies()
        self.font_path = self._get_chinese_font()

    def _check_dependencies(self):
        """检查依赖库"""
        try:
            from wordcloud import WordCloud
            import matplotlib.pyplot as plt
            self.WordCloud = WordCloud
            self.plt = plt
        except ImportError:
            print("警告: 需要安装 wordcloud 和 matplotlib")
            print("请运行: pip install wordcloud matplotlib")
            raise

    def _get_chinese_font(self) -> str:
        """获取中文字体路径"""
        import platform
        system = platform.system()

        # macOS
        if system == 'Darwin':
            fonts = [
                '/System/Library/Fonts/PingFang.ttc',
                '/System/Library/Fonts/STHeiti Light.ttc',
                '/Library/Fonts/Arial Unicode.ttf'
            ]
        # Windows
        elif system == 'Windows':
            fonts = [
                'C:/Windows/Fonts/simhei.ttf',
                'C:/Windows/Fonts/msyh.ttc',
            ]
        # Linux
        else:
            fonts = [
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
                '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
            ]

        for font in fonts:
            if os.path.exists(font):
                return font

        print("警告: 未找到中文字体，词云可能显示为方块")
        return None

    def generate_wordcloud(self, freq_dict: Dict, output_path: str, title: str):
        """
        生成词云图

        Args:
            freq_dict: 词频字典
            output_path: 输出文件路径
            title: 图表标题
        """
        # 过滤低频词
        filtered = {k: v for k, v in freq_dict.items() if v >= 1}

        if not filtered:
            print(f"警告: 没有足够的数据生成词云图: {title}")
            return

        # 创建词云
        wc = self.WordCloud(
            font_path=self.font_path,
            width=1200,
            height=600,
            background_color='white',
            max_words=100,
            colormap='viridis',
            prefer_horizontal=0.7,
            scale=2,
            margin=10
        )

        # 生成词云
        wc.generate_from_frequencies(filtered)

        # 保存图片
        self.plt.figure(figsize=(15, 8))
        self.plt.imshow(wc, interpolation='bilinear')
        self.plt.axis('off')
        # 使用找到的字体创建 FontProperties
        title_font = FontProperties(fname=self.font_path) if self.font_path else None
        self.plt.title(title, fontsize=20, fontproperties=title_font)
        self.plt.tight_layout(pad=0)
        self.plt.savefig(output_path, dpi=300, bbox_inches='tight')
        self.plt.close()

        print(f"已生成词云图: {output_path}")

    def create_output_dirs(self, scenic_spots: List[str]):
        """创建词云图输出目录结构"""
        base_dir = os.path.join('output', 'wordcloud')
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        # 景区名称映射（中文 -> 英文）
        spot_name_map = {
            '泰山': 'taishan',
            '西湖': 'xihu',
            '张家界': 'zhangjiajie'
        }

        for spot in scenic_spots:
            # 确保景区名称在映射表中
            spot_en = spot_name_map.get(spot, spot)
            spot_dir = os.path.join(base_dir, spot_en)
            if not os.path.exists(spot_dir):
                os.makedirs(spot_dir)


# =============================================================================
# 7. 主程序
# =============================================================================

def load_data(input_path: str) -> pd.DataFrame:
    """加载Excel数据"""
    df = pd.read_excel(input_path)
    print(f"成功读取: {input_path}")
    print(f"数据形状: {df.shape}")
    return df


def process_record(row: pd.Series, detectors: Dict, extractors: Dict) -> Dict:
    """处理单条记录"""
    scenic_spot = str(row['景区名称'])
    result = {
        'scenic_spot': scenic_spot,
        # 游客实体（用于后续官方-游客对比）
        'poi': [],
        # 官方实体（审计用，不参与游客路线对比）
        'poi_official': [],
        'transport': {'basic': [], 'specific': [], 'time_distance': []},
        'transport_official': {'basic': [], 'specific': [], 'time_distance': []},
        'time': {'exact': [], 'relative': [], 'duration': []},
        'time_official': {'exact': [], 'relative': [], 'duration': []}
    }

    # 处理官方游览路线
    if '官方游览路线' in row:
        official_route = str(row['官方游览路线'])
        format_type = detectors['format'].detect(official_route)

        result['poi_official'].extend(extractors['poi'].extract(official_route, format_type, scenic_spot))
        transport = extractors['transport'].extract(official_route)
        for key in transport:
            result['transport_official'][key].extend(transport[key])
        time = extractors['time'].extract(official_route)
        for key in time:
            result['time_official'][key].extend(time[key])
    
    # 处理游客游记
    # Check for '游记' column (new dataset format) or '游客游记1'-'游客游记5' (old format)
    travelog_texts = []
    
    if '游记' in row:
        travelog_texts.append(str(row['游记']))
    
    for i in range(1, 6):
        travelog_col = f'游客游记{i}'
        if travelog_col in row:
            travelog_texts.append(str(row[travelog_col]))
            
    for travelog in travelog_texts:
        format_type = detectors['format'].detect(travelog)

        result['poi'].extend(extractors['poi'].extract(travelog, format_type, scenic_spot))
        transport = extractors['transport'].extract(travelog)
        for key in transport:
            result['transport'][key].extend(transport[key])
        time = extractors['time'].extract(travelog)
        for key in time:
            result['time'][key].extend(time[key])

    # 保序去重
    result['poi'] = stable_unique(result['poi'])
    result['poi_official'] = stable_unique(result['poi_official'])
    for key in result['transport']:
        result['transport'][key] = stable_unique(result['transport'][key])
    for key in result['transport_official']:
        result['transport_official'][key] = stable_unique(result['transport_official'][key])
    for key in result['time']:
        result['time'][key] = stable_unique(result['time'][key])
    for key in result['time_official']:
        result['time_official'][key] = stable_unique(result['time_official'][key])

    return result


def save_results(results: List[Dict], stats: Dict, output_path: str):
    """保存JSON结果"""
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'source_file': 'data_cleaned.xlsx',
            'total_records': len(results),
            'scenic_spots': [r['scenic_spot'] for r in results]
        },
        'results': results,
        'statistics': {
            'top_poi': stats['top_poi'],
            'top_transport': stats['top_transport'],
            'top_time': stats['top_time']
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"已保存结果: {output_path}")


def main():
    """主函数"""
    print("=" * 60)
    print("景区游记实体识别系统")
    print("=" * 60)

    # 1. 加载数据
    print("\n[1/5] 加载数据...")
    # 修改默认路径，指向任务1生成的清洗后数据
    df = load_data('../task1_data_collection/data/data_cleaned.xlsx')

    # 2. 初始化检测器和提取器
    print("\n[2/5] 初始化检测器和提取器...")
    detectors = {'format': FormatDetector()}
    extractors = {
        'poi': POIExtractor(),
        'transport': TransportExtractor(),
        'time': TimeExtractor()
    }

    # 3. 处理每条记录
    print("\n[3/5] 提取实体...")
    results = []
    for idx, row in df.iterrows():
        print(f"  处理 {row['景区名称']}...")
        record = process_record(row, detectors, extractors)
        results.append(record)

    # 4. 统计分析
    print("\n[4/5] 统计分析...")
    analyzer = StatisticsAnalyzer()
    stats = analyzer.analyze(results)

    print(f"\n  Top 10 POI:")
    for item in stats['top_poi'][:10]:
        print(f"    {item['entity']}: {item['count']}次")

    print(f"\n  Top 10 交通方式:")
    for item in stats['top_transport'][:10]:
        print(f"    {item['entity']}: {item['count']}次")

    # 5. 保存结果
    save_results(results, stats, os.path.join('output', 'entity_results.json'))

    # 6. 生成词云图
    print("\n[5/5] 生成词云图...")
    try:
        wc_gen = WordCloudGenerator()

        # 创建输出目录
        scenic_spots = [r['scenic_spot'] for r in results]
        wc_gen.create_output_dirs(scenic_spots)

        # 景区名称映射（中文 -> 英文）
        spot_name_map = {
            '泰山': 'taishan',
            '西湖': 'xihu',
            '张家界': 'zhangjiajie'
        }

        # 为每个景区生成3张词云图
        for record in results:
            spot_cn = record['scenic_spot']
            spot_en = spot_name_map.get(spot_cn, spot_cn)
            
            # Base directory for wordclouds
            base_wc_dir = os.path.join('output', 'wordcloud')

            # POI词云
            if record['poi']:
                poi_freq = Counter(record['poi'])
                output_path = os.path.join(base_wc_dir, spot_en, 'poi.png')
                wc_gen.generate_wordcloud(dict(poi_freq), output_path, f'{spot_cn} - 景点POI')

            # 交通词云
            all_transport = []
            for cat in ['basic', 'specific', 'time_distance']:
                all_transport.extend(record['transport'].get(cat, []))
            if all_transport:
                transport_freq = Counter(all_transport)
                output_path = os.path.join(base_wc_dir, spot_en, 'transport.png')
                wc_gen.generate_wordcloud(dict(transport_freq), output_path, f'{spot_cn} - 交通方式')

            # 时间词云
            all_time = []
            for cat in ['exact', 'relative', 'duration']:
                all_time.extend(record['time'].get(cat, []))
            if all_time:
                time_freq = Counter(all_time)
                output_path = os.path.join(base_wc_dir, spot_en, 'time.png')
                wc_gen.generate_wordcloud(dict(time_freq), output_path, f'{spot_cn} - 时间节点')

        print(f"已生成 {len(results) * 3} 张词云图到 output/wordcloud/ 目录")
    except Exception as e:
        print(f"词云图生成失败: {e}")

    print("\n" + "=" * 60)
    print("处理完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
