# -*- coding: utf-8 -*-
# 各类生图方法的实现
import requests, json, os, sys
project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
sys.path.insert(0,project_root_dir)
from config.config import Config
from tools.general import get_model_config_sqlite

def zhipuT2iApi(prompt, size='864x1152'):
    '''智谱文生图接口'''
    conf_t = get_model_config_sqlite()
    url = "https://open.bigmodel.cn/api/paas/v4/images/generations"
    res = requests.post(url, json={
            "model":"cogview-3-flash",
            "prompt":prompt,
            "size":size,
            "quality":"hd",
            "watermark_enabled":False
        },
        headers={
            "Authorization": f"{next(t for t in conf_t if t[3] == 3)[2]}",
            "Content-Type": "application/json"
        }
    )
    try:
        print('生成图像：',json.loads(res.text)["data"][0]["url"])
    except:
        print(f'{res.text}')
        return json.loads(res.text)
    return json.loads(res.text)["data"][0]["url"]