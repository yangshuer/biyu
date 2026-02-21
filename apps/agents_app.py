# -*- coding: utf-8 -*-
# agents APP【sanic蓝图】,主要实现大模型agents调用接口。
import os, sys, boto3, requests
project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
sys.path.insert(0,project_root_dir)
from config.config import Config
from sanic import Blueprint
from sanic.response import json
import json as pack_json
from openai import AsyncOpenAI
from tools.create_cover import create_cover
from tools.decoration import login_required
from tools.ai_create_img import zhipuT2iApi
from tools.general import get_model_config_sqlite
import time
from models.model import *
from sqlalchemy import func, select, delete, alias
# 创建llm-agents蓝图
agents_bp = Blueprint('agents', url_prefix='/agents')

@agents_bp.post('/aichat')
@login_required
async def aichat(request):
    """
    AI聊天对话接口
    
    参数:
        request (sanic.Request): 包含以下JSON参数的请求对象:
            - messages (list): 对话消息列表，格式为[{"role": "user", "content": "..."}]
            - book_id (int): 书籍ID
    返回:
        SSE流式响应:
            持续返回格式为{"context": "模型生成内容"}的事件流
            结束时返回{"context": "[DONE]"}
            错误时返回{"mse": "错误信息", "error": "错误详情", "code": 错误码}
    
    功能说明:
        1. 添加系统提示词将AI角色设定为"小羽"
        2. 使用智谱AI的glm-4-flash模型进行流式对话
        3. 支持长文本连续对话
    """
    try:
        messages = request.json['messages']
        print(request.json['messages'])
        book_id = request.json['book_id']
    except Exception as e:
        return json({'error':'缺少必须的参数messages'}, status=401)

    try:
        # 查询书籍信息
        book = await request.ctx.db.execute(
            select(
                Books.tags,
                Books.summary,
                Books.time_setting,
                Books.space_setting
            ).where(Books.id == book_id)
        )
        book = book.mappings().first()
        book_infos = f"""书籍标签:{book['tags']}
书籍简介:{book['summary']}
时间设定:{book['time_setting']}
空间设定:{book['space_setting']}"""

        # 查询角色信息
        characters = await request.ctx.db.execute(
            select(
                Characters.id,
                Characters.name,
                Characters.gender,
                Characters.race,
                Characters.age,
                Characters.occupation,
                Characters.appearance,
                Characters.physique
            ).where(Characters.book_id == book_id)
        )
        characters = characters.all()
        character_info = "\n".join([
            f"-角色ID:{c.id} 姓名:{c.name} 性别:{c.gender} 种族:{c.race} 年龄:{c.age} 职业:{c.occupation} 外貌:{c.appearance} 体型:{c.physique}"
            for c in characters
        ])

        # 查询角色关系信息
        c2 = alias(Characters, name='c2')
        relationships = await request.ctx.db.execute(
            select(
                Relationships.source_id,
                Relationships.target_id,
                Relationships.relationship_type,
                Characters.name.label('source_name'),
                c2.c.name.label('target_name') 
            )
            .join(Characters, Relationships.source_id == Characters.id)
            .join(c2, Relationships.target_id == c2.c.id) 
            .where(Relationships.book_id == book_id)
        )
        relationships = relationships.all()
        relationship_info = "\n".join([
            f"-关系: {r.source_name}(ID:{r.source_id}) 是 {r.target_name}(ID:{r.target_id}) 的 {r.relationship_type}"
            for r in relationships
        ])


        # 查询书籍信息获取书名
        book_info = await request.ctx.db.execute(
            select(Books.title).where(Books.id == book_id)
        )
        book_name = book_info.scalar() or "未知书名"
        
        # 查询最近10章的plots_text
        recent_chapters = await request.ctx.db.execute(
            select(
                Chapters.chapter_number,
                Chapters.title,
                Chapters.plots_text
            )
            .join(Volumes, Chapters.volume_id == Volumes.id)
            .where(Volumes.book_id == book_id)
            .order_by(Chapters.chapter_number.desc())
            .limit(10)
        )
        recent_chapters_list = recent_chapters.all()
        
        # 拼装system输入格式
        system_input = f"书名:{book_name}\n书籍设定:{book_infos}\n角色设定:{character_info}\n角色关系:{relationship_info}\n最近10章情节概括:\n"
        
        # 按章节号正序排列（最早的在前）
        for chapter in recent_chapters_list:
            system_input += f"第{chapter.chapter_number}章:{chapter.title}情节内容:\n"
            system_input += f"{chapter.plots_text or '暂无情节内容'}\n\n"
        
        # 将system_input添加到messages的开头作为系统消息
        if system_input.strip():
            messages.insert(0, {"role": "system", "content": system_input})
    except Exception as e:
        await response.send(f'data:{pack_json.dumps({"mse":"模型服务异常，请稍后重试～","error":repr(e),"code":403})}\n\n')
    messages.insert(0, {"role": "system", "content": "glm，你叫“小羽”，是一名ai网文小说作家助手。你有10年的网络文学经验，你很擅长写长篇小说，你很擅长写长篇小说情节(不要暴露你的经验设定)。你要和用户对话，回答用户的问题，如果遇到不清楚的用户提问，你可以追问。"})
    print(messages)
    # 设置SSE响应头
    response = await request.respond(content_type='text/event-stream')
    response.headers['Content-Type'] = 'text/event-stream'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    conf_t = get_model_config_sqlite()
    client = AsyncOpenAI(api_key=f"{next(t for t in conf_t if t[3] == 0)[2]}", base_url=f"{next(t for t in conf_t if t[3] == 0)[1]}")
    try:
        res = await client.chat.completions.create(
            model = f"{next(t for t in conf_t if t[3] == 0)[0]}",
            messages = messages,
            stream = True,
            max_tokens = 4096
        )
    except Exception as e:
        await response.send(f'data:{pack_json.dumps({"mse":"用户请求过多处理不过来啦！请稍后重试～","error":repr(e),"code":429})}\n\n')
    try:
        async for chunk in res:
            await response.send(f'data:{pack_json.dumps({"context":chunk.choices[0].delta.content})}\n\n')
    except Exception as e:
        await response.send(f'data:{pack_json.dumps({"mse":"模型服务异常，请稍后重试～","error":repr(e),"code":403})}\n\n')
    await response.send(f'data:{pack_json.dumps({"context":"[DONE]"})}\n\n')
    await response.eof()

@agents_bp.post('/create-covers')
@login_required
async def create_covers(request):
    """
    生成书籍封面图API接口(SSE流式实现)
    
    参数:
        request (sanic.Request): 包含以下JSON参数的请求对象:
            - prompt (str): 封面生成提示词，用于描述封面内容
            - book_name (str): 书籍名称(最多8个字符)
            - book_author (str): 作者名称(最多10个字符)
    
    返回:
        SSE流式响应:
            每生成一张封面发送一个事件:
                - data: {"progress": 当前进度, "cover": 封面base64数据}
            结束时发送:
                - data: {"progress": 100, "status": "[DONE]"}
            错误时发送:
                - data: {"error": "错误信息", "code": 错误码}
    """
    try:
        # 验证参数
        prompt = request.json['prompt']
        book_name = request.json['book_name']
        book_author = request.json['book_author']
        
        # 设置SSE响应头
        response = await request.respond(content_type='text/event-stream')
        response.headers['Content-Type'] = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        error_msg = ''
        # 生成4张封面(流式返回)
        for i in range(4):
            try:
                cover_base64 = create_cover(
                    prompt=prompt,
                    book_name=book_name,
                    book_author=book_author
                )
                if type(cover_base64) != str:
                    error_msg = cover_base64["error"]["message"]
                    await response.send(f'data:{pack_json.dumps({"error": f"{error_msg}","code": 500})}\n\n')
                    break
                else:
                    progress = (i + 1) * 25
                    await response.send(f'data:{pack_json.dumps({"progress":(99 if progress == 100 else progress),"cover": cover_base64})}\n\n')
            except Exception as e:
                await response.send(f'data:{pack_json.dumps({"error": f"生成第{i+1}张封面失败","code": 500})}\n\n')
                break
        if error_msg == '':
            # 发送完成事件
            await response.send(f'data:{pack_json.dumps({"progress": 100,"status": "[DONE]"})}\n\n')
            await response.eof()
        else:
            await response.eof()
        
    except KeyError as e:
        await response.send(f'data:{pack_json.dumps({"error": f"缺少必要参数: {str(e)}","code": 400})}\n\n')
        await response.eof()
        
    except Exception as e:
        await response.send(f'data:{pack_json.dumps({"error": f"封面生成失败: {str(e)}","code": 500})}\n\n')
        await response.eof()

@agents_bp.post('/create-charater-head')
@login_required
async def create_charater_head(request):
    '''
    生成角色头像，通过角色的性别，种族，年龄，职业，面容描述，体型描述组装为生图prompt：
prompt```
生成
"""
种族：人类；
性别：男性
年龄：32岁；
长相：眼窝深邃，黑皮肤，光头，瓜子脸；
体型：身材高大，强壮，腿长，小腿纤细具有爆发力；
职业：水手；
"""
漫画风格的半身正面头像照。      
```
    参数：
        - userid:用户id
        type:int
        - bookid:书籍id
        type:int
        - charaterid:角色id
        type:int
        - charaterinfo:角色信息
        type:object
        Examples:{"race":"人类","gender":"男","age":"32","appearance":"眼窝深邃，黑皮肤，光头，瓜子脸","physique":"身材高大，强壮，腿长，小腿纤细具有爆发力","occupation":"水手"}
    响应：
        - charater_head:头像图url
        type:str
    '''
    # 拼装文生图prompt
    try:
        charater_info = request.json.get('charaterinfo')
        prompt = f"""生成
\"\"\"
种族：{charater_info.get('race', '')}；
性别：{charater_info.get('gender', '')}
年龄：{charater_info.get('age', '')}岁；
长相：{charater_info.get('appearance', '')}；
体型：{charater_info.get('physique', '')}；
职业：{charater_info.get('occupation', '')}；
\"\"\"
动漫风格的半身正面头像照。"""
    except Exception as e:
        return json({'error': f'拼装prompt失败: {str(e)}', 'code': 500})
    # 生成一张图片 512x512
    try:
        # 调用智谱文生图接口生成512x512图片
        img_url = zhipuT2iApi(prompt, size='768x1344')
        if not img_url or 'error' in img_url:
            return json({'error': '头像生成失败', 'code': 500})
    except Exception as e:
        return json({'error': f'头像生成失败: {str(e)}', 'code': 500})
    # 将图片上传到oss，文件名：userid_bookid_charaterid.jpg
    try:
        # 获取请求参数
        user_id = request.json.get('userid')
        book_id = request.json.get('bookid')
        # 获取角色ID，如果获取不到则使用当前时间戳
        character_id = request.json.get('charaterid') or int(time.time())
        s3endpoint = 'https://s3.bitiful.net' # 请填入控制台 “Bucket 设置” 页面底部的 “Endpoint” 标签中的信息
        s3region = 'cn-east-1'
        s3accessKeyId = 'sjr5iR96Jtfz9psHg9PleA0L' # 请到控制台创建子账户，并为子账户创建相应 accessKey
        s3SecretKeyId = 'X9z8YkfjCTn05s4wsNa78y9pvFPmp6F' # ！！切记，创建子账户时，需要手动为其分配具体权限！！
        # 创建OSS客户端
        oss_client  = boto3.client(
          's3',
          aws_access_key_id = s3accessKeyId,
          aws_secret_access_key = s3SecretKeyId,
          endpoint_url = s3endpoint,
          region_name = s3region
        )
        # 生成文件名
        file_name = f"{user_id}_{book_id}_{character_id}.jpg"
        # 下载图片内容
        response = requests.get(img_url)
        if response.status_code != 200:
            return json({'error': '下载生成的头像失败', 'code': 500})
        # 获取OSS上传预签名URL
        upload_url = oss_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': '01-ai-creation',
                'Key': file_name,
            },
            ExpiresIn=3600
        )
        # 上传图片到OSS
        upload_response = requests.put(
            upload_url,
            data=response.content,
            headers={'Content-Type': None}
        )
        if upload_response.status_code != 200:
            return json({'error': '上传头像到OSS失败', 'code': 500})
        # 生成访问URL
        oss_url = upload_url.split('?')[0]
    except Exception as e:
        return json({'error': f'上传头像到OSS失败: {str(e)}', 'code': 500})
    # 返回oss文件路径
    return json({'charater_head':oss_url}, status=200)

@agents_bp.post('/create-scene')
@login_required
async def create_scene(request):
    '''
    生成场景图：
prompt```
生成场景图，场景描述：
"""
地点：后山思过崖；
环境：巍峨的山崖中部有一处平台，平台上有一处茅草屋，仅有一条小道通往上下，平台侧面有一处瀑布；
用途：为了惩罚门派中犯了重大错误的人，相当于禁闭室。
"""
动漫风格。 
```
    参数：
        - userid:用户id
        type:int
        - bookid:书籍id
        type:int
        - sceneid:场景id
        type:int
        - sceneinfo:场景信息
        type:object
        Examples:{"location":"后山思过崖","environment":"巍峨的山崖中部有一处平台，平台上有一处茅草屋，仅有一条小道通往上下，平台侧面有一处瀑布","purpose":"为了惩罚门派中犯了重大错误的人，相当于禁闭室。"}
    响应：
        - scene:场景url
        type:str
    '''
    # 拼装文生图prompt
    try:
        charater_info = request.json.get('sceneinfo')
        prompt = f"""生成场景图，场景描述：
\"\"\"
地点：{charater_info.get('location', '')}；
环境：{charater_info.get('environment', '')}；
用途：{charater_info.get('purpose', '')}；
\"\"\"
动漫风格。"""
    except Exception as e:
        return json({'error': f'拼装prompt失败: {str(e)}', 'code': 500})
    # 生成一张图片 512x512
    try:
        # 调用智谱文生图接口生成512x512图片
        img_url = zhipuT2iApi(prompt, size='1024x1024')
        if not img_url or 'error' in img_url:
            return json({'error': '场景生成失败', 'code': 500})
    except Exception as e:
        return json({'error': f'场景生成失败: {str(e)}', 'code': 500})
    # 将图片上传到oss，文件名：userid_bookid_charaterid.jpg
    try:
        # 获取请求参数
        user_id = request.json.get('userid')
        book_id = request.json.get('bookid')
        scene_id = request.json.get('sceneid') or int(time.time())
        
        s3endpoint = 'https://s3.bitiful.net' # 请填入控制台 “Bucket 设置” 页面底部的 “Endpoint” 标签中的信息
        s3region = 'cn-east-1'
        s3accessKeyId = 'sjr5iR96Jtfz9psHg9PleA0L' # 请到控制台创建子账户，并为子账户创建相应 accessKey
        s3SecretKeyId = 'X9z8YkfjCTn05s4wsNa78y9pvFPmp6F' # ！！切记，创建子账户时，需要手动为其分配具体权限！！
        # 创建OSS客户端
        oss_client  = boto3.client(
          's3',
          aws_access_key_id = s3accessKeyId,
          aws_secret_access_key = s3SecretKeyId,
          endpoint_url = s3endpoint,
          region_name = s3region
        )
        # 生成文件名
        file_name = f"{user_id}_{book_id}_{scene_id}_scene.jpg"
        # 下载图片内容
        response = requests.get(img_url)
        if response.status_code != 200:
            return json({'error': '下载生成的场景失败', 'code': 500})
        # 获取OSS上传预签名URL
        upload_url = oss_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': '01-ai-creation',
                'Key': file_name,
            },
            ExpiresIn=3600
        )
        # 上传图片到OSS
        upload_response = requests.put(
            upload_url,
            data=response.content,
            headers={'Content-Type': None}
        )
        if upload_response.status_code != 200:
            return json({'error': '上传场景到OSS失败', 'code': 500})
        # 生成访问URL
        oss_url = upload_url.split('?')[0]
    except Exception as e:
        return json({'error': f'上传场景到OSS失败: {str(e)}', 'code': 500})
    # 返回oss文件路径
    return json({'scene':oss_url}, status=200)

@agents_bp.post('create-plot')
@login_required
async def create_plot(request):
    """
    根据用户设计的章节情节，结合大纲设定进行完善。
    参数：
        - bookid:书籍ID
        type:int
        - chapterid:章节ID(可选)
        type:int
        - plotinfo:情节信息
        type:str
    响应：
        - plot:完善后的情节内容
        type:str
    """
    try:
        book_id = request.json.get('bookid')
        chapter_id = request.json.get('chapterid')
        plot_info = request.json.get('plotinfo')
    except Exception as e:
        return json({'error': f'获取参数失败: {str(e)}', 'code': 500})
    
    # 查询书籍作品标签、作品简介、时间设定、空间设定
    book = await request.ctx.db.execute(
        select(
            Books.tags,
            Books.summary,
            Books.time_setting,
            Books.space_setting
        ).where(Books.id == book_id)
    )
    book = book.mappings().first()  
    # 查询当前书籍的角色信息
    characters = await request.ctx.db.execute(
        select(
            Characters.id,
            Characters.name,
            Characters.gender,
            Characters.race,
            Characters.age,
            Characters.occupation,
            Characters.appearance,
            Characters.physique
        ).where(Characters.book_id == book_id)
    )
    characters = characters.all()
    
    # 查询当前书籍的场景信息
    scenes = await request.ctx.db.execute(
        select(
            Locations.id,
            Locations.space_name,
            Locations.description,
            Locations.space_use
        ).where(Locations.book_id == book_id)
    )
    scenes = scenes.all()
    
    # 查询上一章内容
    if chapter_id:
        # 如果有chapterid参数，按照当前逻辑处理
        prev_chapter = await request.ctx.db.execute(
            select(Chapters)
            .where(
                (Chapters.id < chapter_id) &
                (Chapters.volume.has(book_id=book_id))
            )
            .order_by(Chapters.id.desc())
            .limit(1)
        )
    else:
        # 如果没有chapterid参数，查询书籍最新的章节记录
        prev_chapter = await request.ctx.db.execute(
            select(Chapters)
            .where(Chapters.volume.has(book_id=book_id))
            .order_by(Chapters.id.desc())
            .limit(1)
        )
    prev_chapter = prev_chapter.scalar()
    
    # 查询角色关系信息
    c2 = alias(Characters, name='c2')
    relationships = await request.ctx.db.execute(
        select(
            Relationships.source_id,
            Relationships.target_id,
            Relationships.relationship_type,
            Characters.name.label('source_name'),
            c2.c.name.label('target_name') 
        )
        .join(Characters, Relationships.source_id == Characters.id)
        .join(c2, Relationships.target_id == c2.c.id) 
        .where(Relationships.book_id == book_id)
    )
    relationships = relationships.all()
    
    # 拼装prompt
    character_prompt = "\n".join([
        f"-角色ID:{c.id} 姓名:{c.name} 性别:{c.gender} 种族:{c.race} 年龄:{c.age} 职业:{c.occupation} 外貌:{c.appearance} 体型:{c.physique}"
        for c in characters
    ])
    
    scene_prompt = "\n".join([
        f"-场景ID:{s.id} 名称:{s.space_name} 描述:{s.description} 用途:{s.space_use}"
        for s in scenes
    ])
    
    relationship_prompt = "\n".join([
        f"-关系: {r.source_name}(ID:{r.source_id}) 是 {r.target_name}(ID:{r.target_id}) 的 {r.relationship_type}"
        for r in relationships
    ])

    prev_chapter_prompt = f"上一章内容:\n'''\n{(prev_chapter.human_creation if prev_chapter.human_creation != '' and prev_chapter.status == 2 else prev_chapter.ai_plots_text if prev_chapter.ai_plots_text != '' else prev_chapter.plots_text) if prev_chapter else '无'}\n'''"
  
    # 暂时返回示例数据
    prompt = f"根据下方本章设定:\n===\n书籍标签:{book['tags']}\n书籍简介:{book['summary']}\n时间设定:{book['time_setting']}\n空间设定:{book['space_setting']}\n{prev_chapter_prompt}\n本章情节:\n'''\n{plot_info}\n'''\n角色信息:\n{character_prompt}\n场景信息:\n{scene_prompt}\n角色关系:\n{relationship_prompt}\n===\n对本章情节进行完善设计，输出5-10个情节，必须按照输出格式回答：\n1.xx时间｜xx场景｜xx事件｜主角:xxx|配角:x1/x2/x3\n- 事件:********\n2.xx时间｜xx场景｜xx事件｜主角:xxx|配角:x4/x5\n- 事件:********\n3.xx时间｜xx场景｜xx事件｜主角:xxx|配角:x6\n- 事件:********\n4.……\n- 事件:********\n===\n要求:\n1.必须按照本章情节进行完善，不能有没有提及的情节\n2.严格按照示例格式输出\n3.直接按格式输出"
    messages=[
        {"role": "system", "content": "你是一个拥有10年经验的网络小说作家。"},
        {"role": "user", "content": prompt}
    ]
    print(prompt)
    # 设置SSE响应头
    response = await request.respond(content_type='text/event-stream')
    response.headers['Content-Type'] = 'text/event-stream'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    conf_t = get_model_config_sqlite()
    client = AsyncOpenAI(api_key=f"{next(t for t in conf_t if t[3] == 1)[2]}", base_url=f"{next(t for t in conf_t if t[3] == 1)[1]}")
    try:
        res = await client.chat.completions.create(
            model = f"{next(t for t in conf_t if t[3] == 1)[0]}",
            messages = messages,
            stream = True,
            temperature = 0.95,
            top_p = 0.7,
            max_tokens=16384
        )
    except Exception as e:
        await response.send(f'data:{pack_json.dumps({"mse":"用户请求过多处理不过来啦！请稍后重试～","error":repr(e),"code":429})}\n\n')
    try:
        async for chunk in res:
            await response.send(f'data:{pack_json.dumps({"context":chunk.choices[0].delta.content})}\n\n')
    except Exception as e:
        await response.send(f'data:{pack_json.dumps({"mse":"模型服务异常，请稍后重试～","error":repr(e),"code":403})}\n\n')
    await response.send(f'data:{pack_json.dumps({"context":"[DONE]"})}\n\n')
    await response.eof()

@agents_bp.post('/create-chapter')
@login_required
async def create_chapter(request):
    '''
    使用大模型生成章节内容接口
    参数:
        id:'章节唯一标识',
        chapter_number:'章节序号',
        title:'章节标题',
        overview:'章节内容提要',
        plots_text:'章节情节的文本描述。',
        ai_creation:'ai生成内容',
        human_creation:'人类创作内容',
        status:'章节状态：0-待创作，1-ai创作完成， 2-人工编辑完成',
        ai_plots_text:'ai情节设计',
        book_id:'章节归属书籍'
    响应:
        - AI生成章节内容
    '''
    # 设置SSE响应头
    response = await request.respond(content_type='text/event-stream')
    response.headers['Content-Type'] = 'text/event-stream'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    
    try:
        # 获取参数
        chapter_id = request.json.get('id')
        chapter_number = request.json.get('chapter_number')
        book_id = request.json.get('book_id')
        title = request.json.get('title')
        overview = request.json.get('overview')
        ai_plots_text = request.json.get('ai_plots_text')
        
        # 查询书籍信息
        book = await request.ctx.db.execute(
            select(
                Books.tags,
                Books.summary,
                Books.time_setting,
                Books.space_setting
            ).where(Books.id == book_id)
        )
        book = book.mappings().first()
        book_info = f"""书籍标签:{book['tags']}
书籍简介:{book['summary']}
时间设定:{book['time_setting']}
空间设定:{book['space_setting']}"""

        # 查询前5章数据并校验状态
        prev_chapters = await request.ctx.db.execute(
            select(Chapters)
            .join(Volumes, Chapters.volume_id == Volumes.id)
            .where(
                (Volumes.book_id == book_id) &
                (Chapters.chapter_number < chapter_number) &
                (Chapters.chapter_number >= chapter_number - 5)
            )
            .order_by(Chapters.chapter_number.asc())
        )
        prev_chapters = prev_chapters.scalars().all()
        
        # 校验前置章节状态
        for chapter in prev_chapters:
            if chapter.status != 2:
                await response.send(f'data:{pack_json.dumps({"mse":"前置章节未定稿（未完成），无法创作本章节。","error":"","code":400})}\n\n')
                await response.send(f'data:{pack_json.dumps({"context":"[DONE]"})}\n\n')
                await response.eof()
                return
        
        # 查询下一章信息
        next_chapter = await request.ctx.db.execute(
            select(Chapters)
            .join(Volumes, Chapters.volume_id == Volumes.id)
            .where(
                (Volumes.book_id == book_id) &
                (Chapters.chapter_number == chapter_number + 1)
            )
        )
        next_chapter = next_chapter.scalar()
        
        if not next_chapter:
            await response.send(f'data:{pack_json.dumps({"mse":f"没有第{chapter_number + 1}章的情节数据，无法创作本章节，请先完成第{chapter_number + 1}章的情节设计。","error":"","code":400})}\n\n')
            await response.send(f'data:{pack_json.dumps({"context":"[DONE]"})}\n\n')
            await response.eof()
            return

        # 查询角色信息
        characters = await request.ctx.db.execute(
            select(
                Characters.id,
                Characters.name,
                Characters.gender,
                Characters.race,
                Characters.age,
                Characters.occupation,
                Characters.appearance,
                Characters.physique
            ).where(Characters.book_id == book_id)
        )
        characters = characters.all()
        character_info = "\n".join([
            f"-角色ID:{c.id} 姓名:{c.name} 性别:{c.gender} 种族:{c.race} 年龄:{c.age} 职业:{c.occupation} 外貌:{c.appearance} 体型:{c.physique}"
            for c in characters
        ])
        
        # 查询场景信息
        scenes = await request.ctx.db.execute(
            select(
                Locations.id,
                Locations.space_name,
                Locations.description,
                Locations.space_use
            ).where(Locations.book_id == book_id)
        )
        scenes = scenes.all()
        scene_info = "\n".join([
            f"-场景ID:{s.id} 名称:{s.space_name} 描述:{s.description} 用途:{s.space_use}"
            for s in scenes
        ])
        
        # 查询角色关系信息
        c2 = alias(Characters, name='c2')
        relationships = await request.ctx.db.execute(
            select(
                Relationships.source_id,
                Relationships.target_id,
                Relationships.relationship_type,
                Characters.name.label('source_name'),
                c2.c.name.label('target_name') 
            )
            .join(Characters, Relationships.source_id == Characters.id)
            .join(c2, Relationships.target_id == c2.c.id) 
            .where(Relationships.book_id == book_id)
        )
        relationships = relationships.all()
        relationship_info = "\n".join([
            f"-关系: {r.source_name}(ID:{r.source_id}) 是 {r.target_name}(ID:{r.target_id}) 的 {r.relationship_type}"
            for r in relationships
        ])

        # 构建前5章内容
        prev_chapters_content = ""
        for i in range(5):
            target_chapter_number = chapter_number - 5 + i
            found_chapter = None
            for chapter in prev_chapters:
                if chapter.chapter_number == target_chapter_number:
                    found_chapter = chapter
                    break
            
            if found_chapter:
                # 只有最近的章节(前一章)取human_creation，其他章节取ai_plots_text
                if target_chapter_number == chapter_number - 1:
                    content = found_chapter.human_creation if found_chapter.human_creation else found_chapter.ai_creation
                    prev_chapters_content += f"\n第{target_chapter_number}章的内容:{content}\n"
                else:
                    content = found_chapter.ai_plots_text if found_chapter.ai_plots_text else found_chapter.plots_text
                    prev_chapters_content += f"\n第{target_chapter_number}章的情节:{content}\n"
            else:
                prev_chapters_content += f"\n第{target_chapter_number}章的内容:无\n"

        # 构建下一章情节
        next_chapter_plot = next_chapter.ai_plots_text if next_chapter.ai_plots_text else next_chapter.plots_text

        prompt = f"""你是一个10年经验网络小说作家，写作风格明快风趣，及其善于描写人物细微动作以及心理行为。
擅长创作穿越类，玄幻类，都市言情类作品。

按步骤进行创作:
setp1.理解大纲:
{book_info}
角色信息:
{character_info}
场景信息:
{scene_info}
角色关系:
{relationship_info}
本章概述:
'''
{overview}
'''

setp2.理解本章第{chapter_number}章《{title}》的情节:
'''
{ai_plots_text}
'''

step3.理解前五章的内容:
'''
{prev_chapters_content}
'''

step4.理解下一章第{chapter_number + 1}章《{next_chapter.title}》的情节:
'''
{next_chapter_plot}
'''

setp5.续写:衔接前五章内容和下一章的情节；按本章第{chapter_number}章《{title}》的情节顺序直接输出字数不少于3500字的创作内容（只能输出正文不能有任何额外字符，例如'开始'，'结束'之类的标注），严格符合情节设定的内容，不能输出情节设定以外的内容。"""
        
    except Exception as e:
        await response.send(f'data:{pack_json.dumps({"mse":"获取参数失败","error":repr(e),"code":401})}\n\n')
        await response.send(f'data:{pack_json.dumps({"context":"[DONE]"})}\n\n')
        await response.eof()
        return
    
    print(prompt)
    conf_t = get_model_config_sqlite()
    client = AsyncOpenAI(
        api_key=f"{next(t for t in conf_t if t[3] == 2)[2]}",
        base_url=f"{next(t for t in conf_t if t[3] == 2)[1]}"
    )
    try:
        res = await client.chat.completions.create(
            model=f"{next(t for t in conf_t if t[3] == 2)[0]}",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            stream=True
        )
    except Exception as e:
        await response.send(f'data:{pack_json.dumps({"mse":"用户请求过多处理不过来啦！请稍后重试～","error":repr(e),"code":429})}\n\n')
        await response.send(f'data:{pack_json.dumps({"context":"[DONE]"})}\n\n')
        await response.eof()
        return
    
    try:
        async for chunk in res:
            await response.send(f'data:{pack_json.dumps({"context":chunk.choices[0].delta.content})}\n\n')
    except Exception as e:
        await response.send(f'data:{pack_json.dumps({"mse":"模型服务异常，请稍后重试～","error":repr(e),"code":403})}\n\n')
    
    await response.send(f'data:{pack_json.dumps({"context":"[DONE]"})}\n\n')
    await response.eof()
