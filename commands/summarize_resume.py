from config import get_model
from litellm import completion

def summarize_resume(resume):
    prompt = f"请总结简历，要求隐藏敏感信息，如名字，联系方式等：\n{resume}"
    return completion(model=get_model(), messages=[{"role": "user", "content": prompt}])
