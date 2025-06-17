from config import get_model
from litellm import completion

def generate_recommendation(jd, resume):
    prompt = f"根据以下职位描述和简历撰写推荐信：\n职位描述：{jd}\n简历：{resume}"
    return completion(model=get_model(), messages=[{"role": "user", "content": prompt}])
