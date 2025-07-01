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
        # 解析数据库类型
        from urllib.parse import urlparse
        parsed = urlparse(db_url)
        
        if parsed.scheme == 'sqlite':
            # SQLite连接
            import sqlite3
            db_path = parsed.path.split('///')[-1]  # 处理sqlite:///path格式
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # 支持字典格式返回
            
        elif parsed.scheme == 'mysql':
            import mysql.connector
            # MySQL连接
            conn = mysql.connector.connect(
                host=parsed.hostname,
                user=db_user,
                password=db_password,
                database=parsed.path.lstrip('/')  # 去除路径前的斜杠
            )
        else:
            raise ValueError(f"不支持的数据库类型: {parsed.scheme}")
        # 根据数据库类型创建游标
        if parsed.scheme == 'sqlite':
            cursor = conn.cursor()
        else:  # mysql
            cursor = conn.cursor(dictionary=True)
        cursor.execute(sql)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except (mysql.connector.Error, sqlite3.Error, ValueError) as err:
        print(f"数据库错误: {err}")
        return []
