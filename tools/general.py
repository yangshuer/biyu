# -*- coding: utf-8 -*-
# 通用工具集合。
import hashlib
import os, sys
import sqlite3
project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
sys.path.insert(0,project_root_dir)
from config.config import Config

async def sha1_encrypt(data):
    '''sha1加密方法'''
    sha1=hashlib.sha1()
    data_bytes = data.encode()
    sha1.update(data_bytes)
    encrypted_data = sha1.hexdigest()
    return encrypted_data




def get_model_config_sqlite():
    # 从SQLITE中查询模型配置信息。
    db_path = Config.sqlite3.file_path
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        raise(f"数据库文件不存在: {db_path}")
    try:
        # 1. 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # 2. 查询所有数据
        cursor.execute("SELECT * FROM model_config")
        all_results = cursor.fetchall()
    except sqlite3.Error as e:
        raise(f"数据库错误: {e}")
    finally:
        # 3. 关闭连接
        if conn:
            conn.close()
    return all_results

if __name__ == "__main__":
    get_model_config_sqlite()