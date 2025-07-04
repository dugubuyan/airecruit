from config import get_model
from litellm import completion

def bd_email_to_hr(jd, resumes):
    # TODO：根据jd的内容，将resumes中的候选人列表信息简要介绍推荐给hr，发送邮件给hr
