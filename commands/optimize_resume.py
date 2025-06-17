from config import get_model
from litellm import completion
from diff_match_patch import diff_match_patch

def optimize_resume(jd, resume):
    # 请求LLM生成diff格式的修改建议
    prompt = f"""请以diff格式提供简历修改建议，使其更符合职位需求。
职位描述：{jd}
当前简历内容：
{resume}

请严格按照diff格式返回修改内容，只需返回代码块部分。"""
    response = completion(model=get_model(), messages=[{"role": "user", "content": prompt}])
    
    # 解析并应用diff
    dmp = diff_match_patch()
    patches = dmp.patch_fromText(response.choices[0].message.content)
    optimized_resume, _ = dmp.patch_apply(patches, resume)
    
    return optimized_resume


