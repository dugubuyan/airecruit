from config import get_model
from litellm import completion

def extract_contact_and_send(jd):
    prompt = f"提取以下职位描述中的联系邮箱或方式：\n{jd}"
    return completion(model=get_model(), messages=[{"role": "user", "content": prompt}])
