from config import get_model
from litellm import completion

def search_resume_by_jd(jd):
    print("search_resume_by_jd、::",jd)
    #通过jd中的要求，生成要查询的sql语句，然后通过sql语句去查询本地数据库，返回resume信息列表
