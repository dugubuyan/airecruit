import pdfplumber
import re
from typing import List, Dict, Tuple
import unicodedata

class PDFToMarkdownConverter:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text_blocks = []
        self.font_stats = {}
        self.line_spacing = 0
        self.indent_threshold = 10
        self.heading_threshold = 1.2
        self.bullet_patterns = [r'^•', r'^\d+\.', r'^[a-z]\)', r'^\-', r'^\*']
        
    def extract_text_blocks(self):
        """提取PDF中的文本块并分析字体特征"""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                # 提取文本块及其属性
                blocks = page.extract_text_lines(
                    x_tolerance=1, 
                    y_tolerance=1,
                    keep_blank_chars=False
                )
                
                for block in blocks:
                    # 计算块中心位置
                    block['center_x'] = (block['x0'] + block['x1']) / 2
                    
                    # 标准化文本
                    text = unicodedata.normalize('NFKC', block['text'])
                    
                    # 收集字体统计信息
                    font_size = block['size']
                    self.font_stats[font_size] = self.font_stats.get(font_size, 0) + len(text)
                    
                    # 保存文本块
                    self.text_blocks.append({
                        'text': text.strip(),
                        'size': font_size,
                        'top': block['top'],
                        'center_x': block['center_x'],
                        'page': page.page_number
                    })
                
                # 计算行间距（基于页面上的文本位置）
                if blocks:
                    tops = sorted([b['top'] for b in blocks])
                    diffs = [tops[i+1] - tops[i] for i in range(len(tops)-1)]
                    if diffs:
                        self.line_spacing = sum(diffs) / len(diffs)
    
    def analyze_document_structure(self):
        """分析文档结构特征"""
        # 确定主要字体大小（用于正文）
        if self.font_stats:
            main_size = max(self.font_stats, key=self.font_stats.get)
            self.base_font_size = main_size
        else:
            self.base_font_size = 10  # 默认值
        
    def convert_to_markdown(self) -> str:
        """将提取的文本块转换为格式化的Markdown"""
        self.extract_text_blocks()
        self.analyze_document_structure()
        
        if not self.text_blocks:
            return ""
        
        # 按页面和垂直位置排序文本块
        self.text_blocks.sort(key=lambda b: (b['page'], b['top']))
        
        md_lines = []
        previous_block = None
        
        for i, block in enumerate(self.text_blocks):
            text = block['text']
            
            # 跳过空文本块
            if not text:
                continue
                
            # 确定缩进级别
            indent_level = int(block['center_x'] // self.indent_threshold) if self.indent_threshold > 0 else 0
            
            # 检测标题
            is_heading = self.is_heading(block, previous_block)
            if is_heading:
                heading_level = self.determine_heading_level(block)
                md_lines.append(f"{'#' * heading_level} {text}")
                continue
                
            # 检测列表项
            is_list_item, list_marker = self.is_list_item(text)
            if is_list_item:
                # 移除列表标记
                clean_text = re.sub(r'^\s*[' + re.escape(list_marker) + r']\s*', '', text)
                indent = '  ' * indent_level
                md_lines.append(f"{indent}- {clean_text}")
                continue
                
            # 检测代码块
            if self.is_code_block(text):
                md_lines.append(f"```\n{text}\n```")
                continue
                
            # 普通段落处理
            # 添加段落间距（如果上一个块不是列表或标题）
            if previous_block and not self.is_list_item(previous_block['text'])[0] and not is_heading:
                if block['top'] - previous_block['top'] > self.line_spacing * 1.5:
                    md_lines.append('')  # 添加空行分隔段落
            
            # 添加缩进
            indent = '  ' * indent_level
            md_lines.append(f"{indent}{text}")
            
            previous_block = block
        
        return '\n'.join(md_lines)
    
    def is_heading(self, current_block: Dict, previous_block: Dict) -> bool:
        """基于字体大小和位置判断是否为标题"""
        if current_block['size'] > self.base_font_size * self.heading_threshold:
            return True
            
        # 检查是否位于页面顶部
        if current_block['top'] < 100:  # 页面顶部区域
            return True
            
        # 检查与前一个块的距离
        if previous_block:
            vertical_gap = current_block['top'] - previous_block['top']
            if vertical_gap > self.line_spacing * 2:
                return True
                
        return False
    
    def determine_heading_level(self, block: Dict) -> int:
        """根据字体大小确定标题级别"""
        size_ratio = block['size'] / self.base_font_size
        if size_ratio > 2.0:
            return 1
        elif size_ratio > 1.7:
            return 2
        elif size_ratio > 1.4:
            return 3
        elif size_ratio > 1.2:
            return 4
        else:
            return 5
    
    def is_list_item(self, text: str) -> Tuple[bool, str]:
        """检测列表项并返回列表标记"""
        for pattern in self.bullet_patterns:
            if re.search(pattern, text):
                return True, re.search(pattern, text).group(0)
        return False, ''
    
    def is_code_block(self, text: str) -> bool:
        """基于字符模式检测代码块"""
        # 简单的启发式规则：包含多个特殊字符的文本块
        special_chars = r'[{}()\[\]<>;=+\-*/&|^%~]'
        if len(re.findall(special_chars, text)) > 3:
            return True
        return False

# 使用示例
if __name__ == "__main__":
    converter = PDFToMarkdownConverter("/Users/alex/work/ai/hunter/repo/202106/java开发工程师-杨广-20210713.pdf")
    markdown_content = converter.convert_to_markdown()
    
    # 保存Markdown文件
    with open("output.md", "w", encoding="utf-8") as md_file:
        md_file.write(markdown_content)
    
    print(f"Successfully converted PDF to Markdown. Output saved to output.md")