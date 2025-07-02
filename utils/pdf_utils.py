import re
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
import io

class PDFToMarkdownConverter:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        
    def convert_to_markdown(self):
        """Convert PDF file to Markdown format with enhanced formatting
        
        Raises:
            ValueError: If PDF is corrupted or invalid
            Exception: For other unexpected errors
        """
        output = io.StringIO()
        try:
            # Extract text from PDF with layout preservation
            with open(self.pdf_path, 'rb') as pdf_file:
                try:
                    extract_text_to_fp(
                        pdf_file,
                        output,
                        laparams=LAParams(),
                        output_type='text',
                        codec='utf-8'
                    )
                except Exception as e:
                    raise ValueError(f"Failed to extract text from PDF: {str(e)}") from e
            
            text = output.getvalue()
            if not text.strip():
                raise ValueError("Extracted PDF text is empty - possibly corrupted PDF")
            
            # Enhanced Markdown formatting (order matters!)
            text = self.format_headings(text)
            text = self.format_code_blocks(text)  # Process code blocks before lists
            text = self.format_lists(text)
            text = self.format_links(text)
            
            # Basic cleanup
            text = re.sub(r'\n{3,}', '\n\n', text)  # Reduce excessive newlines
            text = re.sub(r' +', ' ', text)         # Reduce multiple spaces
            text = re.sub(r'　+', ' ', text)        # 清理中文全角空格
            
            return text
                
        except Exception as e:
            raise

    def format_headings(self,text):
        """Detect and format headings based on patterns"""
        # Format document title with ==== underline
        text = re.sub(r'^(.+)\n=+$', r'# \1', text, flags=re.MULTILINE)
        # Format section titles with ---- underline
        text = re.sub(r'^(.+)\n-+$', r'## \1', text, flags=re.MULTILINE)
        # Format numbered sections (support Chinese numbering)
        text = re.sub(r'^(\d+\.\d+(?:\.\d+)*)\s+(.+)$', r'### \1 \2', text, flags=re.MULTILINE)
        # Format Chinese numbered headings (e.g. 第一章、第一节)
        text = re.sub(r'^(第[一二三四五六七八九十百千零]+章)\s+(.+)$', r'# \1 \2', text, flags=re.MULTILINE)
        text = re.sub(r'^(第[一二三四五六七八九十百零]+节)\s+(.+)$', r'## \1 \2', text, flags=re.MULTILINE)
        # Format parenthesized numbering (e.g. (1), (一))
        text = re.sub(r'^\(([\d一二三四五六七八九十]+)\)\s+(.+)$', r'### \1. \2', text, flags=re.MULTILINE)
        return text

    def format_lists(self,text):
        """Detect and format bullet points and numbered lists"""
        # 支持更多项目符号：•◦▫️➢等中文常用符号
        text = re.sub(r'^[\s\u2003]*([•◦▫➢])\s+(.+)$', r'- \2', text, flags=re.MULTILINE)
        # 处理数字列表（包含中文括号）
        text = re.sub(r'^[\s\u2003]*([（\(]?\d+[）\)]?)\s+(.+)$', r'\1. \2', text, flags=re.MULTILINE)
        # 处理字母列表
        text = re.sub(r'^[\s\u2003]*([a-zA-Z])[\.、]\s+(.+)$', r'\1. \2', text, flags=re.MULTILINE)
        return text

    def format_code_blocks(self,text):
        """Detect and format code blocks based on indentation"""
        # Group consecutive indented lines into single code blocks
        text = re.sub(r'((?:^ {4,}.*\n)+)', r'```\n\1```\n\n', text, flags=re.MULTILINE)
        # 清理代码块前后的空行
        text = re.sub(r'\n+```', '\n```', text)
        text = re.sub(r'```\n+', '```\n', text)
        return text

    def format_links(self,text):
        """Detect and format URLs as Markdown links"""
        text = re.sub(r'(https?://\S+)', r'[\1](\1)', text)
        return text


# 使用示例
if __name__ == "__main__":
    converter = PDFToMarkdownConverter("/Users/alex/work/ai/hunter/repo/202106/java开发工程师-李世民.pdf")
    markdown_content = converter.convert_to_markdown()
    
    # 保存Markdown文件
    with open("output.md", "w", encoding="utf-8") as md_file:
        md_file.write(markdown_content)
    
    print(f"Successfully converted PDF to Markdown. Output saved to output.md")