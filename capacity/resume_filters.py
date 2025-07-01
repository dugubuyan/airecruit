from config import get_model
from litellm import completion

def resume_filtering(db_url, db_user, db_password, sql):
    prompt = f"请为以下简历内容生成适用于BOSS直聘/猎聘的筛选条件，并生成SQL插入语句：\n{resume}"
    return completion(model=get_model(), messages=[{"role": "user", "content": prompt}])
