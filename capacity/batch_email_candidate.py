from pathlib import Path
# from diff_match_patch import diff_match_patch
# from utils.workspace import WorkspaceManager
from utils.file_utils import export_md_to_pdf

def batch_email_candidate(jd,resume_list):
    print("jd:",jd)
    #从resume_list中找出email地址，然后根据jd的情况生成信件内容，邀请候选人投递职位。

