# -*- coding: utf-8 -*-
# 装饰器工具集合。
import sys
import os
project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# 将项目的最外层目录添加到搜索路径
sys.path.append(project_root_dir)
from functools import wraps
import jwt, redis
import json as pack_json
from tools.redis_tool import RedisManager
from sanic import json


def login_required(wrapped):
    """ token校验装饰器 """
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            async def check_token(request):
                """ 校验token是否有效 """
                try:
                    jwt.decode(request.headers.get('X-Auth-Token'), "KEEP_IT_SECRET_KEEP_IT_SAFE", algorithms=["HS256"])
                except jwt.exceptions.InvalidTokenError:
                    return False
                else:
                    return True
            is_authenticated = await check_token(request)
            if is_authenticated:
                # 执行视图函数
                response = await f(request, *args, **kwargs)
                return response
            else:
                return json({'error': f'登录信息异常，请重新登录～'}, status=401)
        return decorated_function
    return decorator(wrapped)

redis_tools = RedisManager()
def query_decorator(**kwargs):
    def query_decorator(func):
        '''redis缓存查询装饰器'''
        @wraps(func)
        async def select(request):
            try:
                global redis_tools
                client = redis.Redis(connection_pool = redis_tools.redis_pool)
                # 构造key
                if kwargs['usefuncname'] == True:
                    # 方法名+请求参数
                    key = func.__name__
                else:
                    key = ''
                    # 修改这里：区分GET和POST请求参数获取方式
                if request.method == 'GET':
                    params = dict(request.args)
                else:  # POST/PUT等
                    params = dict(request.json)
                params_str = ":".join([f"{k}={v}" for k, v in sorted(params.items())])
                key = f"{func.__name__}:{params_str}"
                r = client.get(key)
                if  r != None:
                    # 缓存中有记录，返回查询结果
                    return json(pack_json.loads(r.encode('utf-8')), status=200)
                else:
                    # 缓存中无记录，执行视图方法获取查询结果，将结果加入缓存
                    res = await func(request)
                    # print(res.body.decode('utf-8'))
                    client.set(key,res.body.decode('utf-8'),
                             ex=kwargs['ex'] #设置缓存1小时
                            ) 
                    return res
            except Exception as e:
                return await func(request)
        return select
    return query_decorator