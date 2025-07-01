import mysql.connector
from typing import List, Dict

def resume_filtering(db_url: str, db_user: str, db_password: str, sql: str) -> List[Dict]:
    """执行SQL查询并返回简历列表
    
    Args:
        db_url: 数据库连接URL
        db_user: 数据库用户名
        db_password: 数据库密码
        sql: 要执行的查询语句
        
    Returns:
        包含简历数据的字典列表
    """
    try:
        conn = mysql.connector.connect(
            host=db_url,
            user=db_user,
            password=db_password,
            database=db_url.split('/')[-1]  # 从URL提取数据库名
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except mysql.connector.Error as err:
        print(f"数据库错误: {err}")
        return []
