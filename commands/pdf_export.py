from pathlib import Path
from utils.file_utils import (export_md_to_pdf,open_pdf_in_browser)

def export_to_pdf(md_content):
    try:
        work_dir = Path("workdir")
        pdf_path = export_md_to_pdf(md_content, work_dir)
        print("md=====:",md_content)
        open_pdf_in_browser(pdf_path)
        return f"简历优化完成，PDF文件已生成至：{pdf_path}"
    except Exception as e:
        return f"发生错误：{str(e)}"