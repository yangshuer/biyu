# -*- coding: utf-8 -*-
from box import Box
import os, sys, asyncio, json
project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
sys.path.insert(0,project_root_dir)
from tools.encryption import main

run_mode = 'dev' # 'pro'
all_config = Box(
    {
        "devConfig":{# 开发环境配置
            "baseurl":"http:localhost", #默认地址
            "mysql":{# 数据库配置
                "user":"root",# 用户名
                "password":"root",# 密码
                "host":"localhost",# 地址
                "port":"3306",# 端口
                "db":"ai_creation",# 数据库
                "max_connections": 10  # 最大连接数
            },
            "sqlite3":{
                "file_path":"/Users/yangxue/PycharmProjects/AI_Creation_Platform/config/model_config"
            },
            "redis":{
                "host": "localhost",  # Redis服务器地址
                "port": "6379",  # Redis端口号
                "password": "admin",  # Redis密码
                "db": "0",  # Redis数据库编号
                "max_connections": 10  # 最大连接数
            },
            "rabbitmq":{
                "host": "localhost",  # RabbitMQ服务器地址
                "port": 5672,  # RabbitMQ端口号
                "user": "admin",  # RabbitMQ用户名
                "password": "admin"  # RabbitMQ密码
            },
            "sanic":{
                "host": "0.0.0.0",  # 监听地址
                "port": 8000,       # 监听端口
                "debug": True,      # 调试模式
                "access_log": True, # 访问日志
                "workers": 2,      # 工作进程数
            }
        }, 
        "proConfig":{# 生产环境配置
            "baseurl":"", #默认地址
            "mysql":{# 数据库配置
                "user":"",# 用户名
                "password":"",# 密码
                "host":"",# 地址
                "port":"",# 端口
                "base":"" # 数据库
            },
            "redis":{

            },
            "rabbitmq":{
                
            },
            "sanic":{
                "host": "0.0.0.0",  # 监听地址
                "port": 8000,       # 监听端口
                "debug": False,      # 调试模式
                "access_log": True, # 访问日志
                "workers": 2,      # 工作进程数
            }
        }   
    }
)
Config = all_config.devConfig if run_mode == 'dev' else all_config.proConfig
Config.conf = json.loads(asyncio.run(main()))
# print(Config)

if __name__ == "__main__":
    pass