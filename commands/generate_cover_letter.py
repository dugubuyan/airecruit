from config import get_model
from litellm import completion

def generate_cover_letter(jd, resume):
    prompt = f"根据以下职位描述和简历生成一封cover letter：\n职位描述：{jd}\n简历：{resume}"
    return completion(model=get_model(), messages=[{"role": "user", "content": prompt}])
