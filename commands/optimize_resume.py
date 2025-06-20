from config import get_model
from litellm import completion
from diff_match_patch import diff_match_patch
from utils.workspace import WorkspaceManager

def optimize_resume():
    """根据工作区内容自动优化简历"""
    """简历优化命令，从工作区自动获取所需内容"""
    ws = WorkspaceManager()
    
    # 获取工作区内容
    jds = ws.get_jds()
    resumes = ws.get_resumes()
    
    # 参数检查
    if not jds:
        return "错误：工作区中没有JD文件，请先使用/file命令添加并分类JD文件"
    if not resumes:
        return "错误：工作区中没有简历文件，请先使用/file命令添加并分类简历文件"
    
    # 使用最新添加的JD和简历
    jd = jds[-1]
    resume = resumes[-1]
    
    # 生成优化建议
    prompt = f"""请以diff格式提供简历修改建议，使其更符合职位需求。
职位描述：{jd}
当前简历内容：
{resume}

请严格按照diff格式返回修改内容，只需返回代码块部分。"""
    
    try:
        response = completion(model=get_model(), messages=[{"role": "user", "content": prompt}])
        diff_text = response.choices[0].message.content
        
        # 应用diff
        dmp = diff_match_patch()
        patches = dmp.patch_fromText(diff_text)
        optimized_resume, _ = dmp.patch_apply(patches, resume)
        
        return f"简历优化完成，修改建议如下：\n{diff_text}\n\n优化后简历内容：\n{optimized_resume}"
    except Exception as e:
        return f"优化过程中发生错误：{str(e)}"


