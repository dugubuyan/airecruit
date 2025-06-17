from llm import get_llm
from utils import read_file

def optimize_resume(jd_path, resume_path, model=None):
    jd = read_file(jd_path)
    resume = read_file(resume_path)
    llm = get_llm(model)
    prompt = f"根据以下职位描述优化简历内容，使其更符合岗位需求：\n职位描述：{jd}\n当前简历：{resume}"
    return llm(prompt)


