# -*- coding: utf-8 -*-
import os, sys
project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
sys.path.insert(0,project_root_dir)
from config.config import Config
# 创建异步数据库引擎
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    f"mysql+asyncmy://{Config.mysql.user}:{Config.mysql.password}@{Config.mysql.host}:{Config.mysql.port}/{Config.mysql.db}?charset=utf8mb4",
    echo=True
)

# 创建异步会话工厂
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)