# 文件格式转换功能
def convert_pdf_to_md(pdf_path, output_path):
    """转换PDF文件到Markdown格式"""
    from pdfminer.high_level import extract_text
    text = extract_text(pdf_path)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

def convert_docx_to_md(docx_path, output_path):
    """转换DOCX文件到Markdown格式"""
    from docx import Document
    doc = Document(docx_path)
    text = '\n'.join([para.text for para in doc.paragraphs])
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

# --- Export to PDF ---
from pathlib import Path
import pdfkit
import os

def export_md_to_pdf(md_content: str, output_path: str | Path):
    """
    将Markdown内容转换为PDF文件
    
    参数:
        md_content: Markdown格式的文本内容
        output_path: 输出PDF路径（目录或完整文件路径）
        
    返回:
        生成的PDF文件路径
    """
    try:
        output_path = Path(output_path)
        if output_path.is_dir():
            output_path = output_path / "resume_optimized.pdf"
            
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 配置pdfkit选项
        options = {
            'encoding': 'UTF-8',
            'enable-local-file-access': None  # 允许加载本地资源
        }
        
        # 使用pdfkit转换Markdown到PDF
        pdfkit.from_string(
            input=md_content,
            output_path=str(output_path),
            options=options
        )
        
        return str(output_path)
    except Exception as e:
        raise RuntimeError(f"PDF生成失败: {str(e)}") from e
