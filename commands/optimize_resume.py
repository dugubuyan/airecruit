from pathlib import Path
# from diff_match_patch import diff_match_patch
# from utils.workspace import WorkspaceManager
from utils.file_utils import export_md_to_pdf

# def optimize_resume(diff_text,resume):
#     print("diif_text:",diff_text)
#     try:
#         # 应用diff
#         dmp = diff_match_patch()
#         patches = dmp.patch_fromText(diff_text)
#         optimized_resume, _ = dmp.patch_apply(patches, resume)
#         work_dir = Path("workdir")
#         pdf_path = export_md_to_pdf(optimized_resume, work_dir)
#         print(f"简历优化完成，PDF文件已生成至：{pdf_path}")

#     except Exception as e:
#         return f"优化过程中发生错误：{str(e)}"

