from config import get_model
from litellm import completion

def optimize_resume(jd, resume):
    prompt = f"根据以下职位描述优化简历内容，使其更符合岗位需求：\n职位描述：{jd}\n当前简历：{resume}"
    return completion(model=get_model(), messages=[{"role": "user", "content": prompt}])


