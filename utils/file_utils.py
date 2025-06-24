from pathlib import Path
import os
from weasyprint import HTML
import logging
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
        
        # 添加基本样式
        html_content = f"""
        <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ 
                        font-family: SimSun;
                        line-height: 1.6;
                        margin: 2cm;
                    }}
                    h1, h2, h3 {{ color: #2c3e50; }}
                    a {{ color: #3498db; text-decoration: none; }}
                </style>
            </head>
            <body>
                {md_content}
            </body>
        </html>
        """
        
        # 使用WeasyPrint生成PDF
        HTML(string=html_content).write_pdf(
            target=str(output_path),
            stylesheets=None,
            presentational_hints=True
        )
        
        return str(output_path)
    except Exception as e:
        raise RuntimeError(f"PDF生成失败: {str(e)}") from e
