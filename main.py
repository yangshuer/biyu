# -*- coding: utf-8 -*-
import os, sys
project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),'.'))
sys.path.insert(0,project_root_dir)
from config.config import Config
from sanic import Sanic
from sanic.response import json
# 导入蓝图模块
from apps.agents_app import agents_bp
from apps.manages_app import manages_bp
from models.db import SessionLocal
from tools.decoration import redis_tools
# 创建server app 
app = Sanic("AiCreationApp")
# 注册蓝图
app.blueprint(agents_bp)
app.blueprint(manages_bp)

# 异步会话中间件
@app.middleware('request')
async def inject_async_session(request):
    # 创建异步会话
    request.ctx.db = SessionLocal()
    # 建议同时添加一个标识表示这是异步会话
    request.ctx.is_async_db = True  

@app.middleware('response')
async def close_async_session(request, response):
    await request.ctx.db.close()  # 注意异步关闭

@app.route("/")
async def hello(request):
    return json({"message": "Hello, Sanic!"})

if __name__ == "__main__":
    # 以开发环境配置启动服务
    app.run(host=Config.sanic.host, 
            port=Config.sanic.port, 
            debug=Config.sanic.debug,
            workers=Config.sanic.workers)
