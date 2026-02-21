# -*- coding: utf-8 -*-
import sys
import os
project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# 将项目的最外层目录添加到搜索路径
sys.path.append(project_root_dir)
import json
import redis
from config.config import Config
class RedisManager:
    def __init__(self):
        '''初始化redis连接池'''
        self.redis_pool = redis.ConnectionPool(
            host=Config.redis.host,
            port=Config.redis.port,
            db=Config.redis.db,
            password=Config.redis.password,
            decode_responses=True,
            max_connections=Config.redis.max_connections
        )
    def set(self, key, value, expire=None):
        client = redis.Redis(connection_pool=self.redis_pool)
        client.set(key, value, ex=expire)

    def get(self, key):
        client = redis.Redis(connection_pool=self.redis_pool)
        return client.get(key)

    def hset(self,key,value:dict,expire=None):
        client = redis.Redis(connection_pool=self.redis_pool)
        client.hset(key,key,json.dumps(value))
        if expire != None:
            client.expire(key,expire)

    def hgetall(self,key):
        client = redis.Redis(connection_pool=self.redis_pool)
        return client.hgetall(key)

    def delete(self,key):
        client = redis.Redis(connection_pool=self.redis_pool)
        client.delete(key)

    def delete_pattern(self, pattern):
        """删除匹配模式的所有key"""
        client = redis.Redis(connection_pool=self.redis_pool)
        pattern = pattern.replace("['*']", "*").replace("['", "\\['").replace("']", "\\']")
        keys = client.keys(pattern)
        if keys:
            client.delete(*keys)
        return len(keys)


if __name__ == '__main__':
    pass