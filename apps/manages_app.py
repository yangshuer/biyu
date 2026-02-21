# -*- coding: utf-8 -*-
# 管理后台APP【sanic蓝图】,主要实现业务功能以及对数据库的CRUD操作接口。
import os, sys, sqlite3
project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
sys.path.insert(0,project_root_dir)
from sanic import Blueprint
from sanic.response import json
from sqlalchemy import func, select, delete
from models.model import *
from tools.general import sha1_encrypt, get_model_config_sqlite
from tools.decoration import login_required, query_decorator
from tools.redis_tool import RedisManager
from tools.jm import encrypt_config, main as get_model_conf
from config.config import Config
import re, jwt, datetime, pika, boto3, base64, time
import json as pack_json
from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

# 创建管理后台蓝图
manages_bp = Blueprint('manages', url_prefix='/manages')

@manages_bp.post('/signin')
async def signin(request):
    '''
    用户注册接口
    ---
    说明: 用户通过邮箱、密码和用户名进行注册
    参数:
      - name: email
        in: body
        type: string
        required: true
        description: 用户注册邮箱地址
      - name: password
        in: body
        type: string
        required: true
        description: 用户设置的登录密码
      - name: username
        in: body
        type: string
        required: true
        description: 用户昵称
    响应:
      200:
        description: 注册成功
        schema:
          type: object
          properties:
            message:
              type: string
              example: 注册成功
            user_id:
              type: integer
              example: 1
            username:
              type: string
              example: 测试用户
            email:
              type: string
              example: test@example.com
      400:
        description: 请求参数缺失或格式错误/邮箱已存在
      500:
        description: 服务器内部处理错误
    '''
    data = request.json
    if not all(key in data for key in ['email', 'password', 'username']):
        return json({'error': '缺少必要参数'}, status=400)
    
    # 校验邮箱格式
    if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data['email']) is None:
        return json({'error': '邮箱校验不合法'}, status=400)

    try:
        # 异步查询,检查邮箱是否已存在
        existing_user = await request.ctx.db.execute(
            select(Users).where(Users.email == data['email'])
        )
        existing_user = existing_user.scalar()
        
        if existing_user:
            return json({'error': '该邮箱已被注册'}, status=400)

        # 异步创建
        new_user = Users(
            email=data['email'],
            password=await sha1_encrypt(data['password']),
            username=data['username'],
            account_balance=decimal.Decimal('0.00')
        )
        
        request.ctx.db.add(new_user)
        await request.ctx.db.commit()  # 注意异步提交
        
        return json({
            'message': '注册成功',
            'user_id': new_user.id,
            'username': new_user.username,
            'email': new_user.email
        }, status=200)
        
    except Exception as e:
        await request.ctx.db.rollback()  # 数据库异步回滚
        return json({'error': f'注册失败: {str(e)}，请稍后重试～'}, status=500)
    finally:
        await request.ctx.db.close()
    
@manages_bp.post('/login')
async def login(request):
    '''
    用户登录接口
    ---
    说明: 用户通过邮箱和密码进行登录验证
    参数:
      - name: email
        in: body
        type: string
        required: true
        description: 用户注册时使用的邮箱地址
      - name: password
        in: body
        type: string
        required: true
        description: 用户设置的登录密码
    响应:
      200:
        description: 登录验证成功
        schema:
          type: object
          properties:
            message:
              type: string
              example: 登录成功
            user_id:
              type: integer
              example: 1
            username:
              type: string
              example: 测试用户
            email:
              type: string
              example: test@example.com
            token:
              type: string
              example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
      400:
        description: 请求参数缺失或格式错误
      401:
        description: 用户密码验证失败
      404:
        description: 邮箱对应的用户不存在
      500:
        description: 服务器内部处理错误
    '''
    data = request.json
    if not all(key in data for key in ['email', 'password']):
        return json({'error': '缺少邮箱或密码参数'}, status=400)
    
    try:
        # 异步查询用户
        user = await request.ctx.db.execute(
            select(Users).where(Users.email == data['email'])
        )
        user = user.scalar()
        
        if not user:
            return json({'error': '用户不存在'}, status=404)
            
        # 验证密码
        encrypted_password = await sha1_encrypt(data['password'])
        if user.password != encrypted_password:
            return json({'error': '密码错误'}, status=401)
            
        return json({
            'message': '登录成功',
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'token': jwt.encode({'email': data['email'], 'exp': datetime.datetime.now()+datetime.timedelta(days=1)},"KEEP_IT_SECRET_KEEP_IT_SAFE",algorithm='HS256')
        }, status=200)
        
    except Exception as e:
        return json({'error': f'登录失败: {str(e)}，请稍后重试～'}, status=500)
    finally:
        await request.ctx.db.close()
    
@manages_bp.post('/reset-password')
async def reset_password(request):
    '''
    summary: 重置用户密码
    description: 通过邮箱验证后重置用户密码
    参数:
      - name: email
        in: body
        required: true
        schema:
          type: string
        description: 用户注册邮箱
      - name: password
        in: body
        required: true
        schema:
          type: string
        description: 新密码
    响应:
      200:
        description: 密码重置成功
      400:
        description: 参数错误
      404:
        description: 用户不存在
      500:
        description: 服务器内部错误
    '''
    data = request.json
    if not all(key in data for key in ['email', 'password']):
        return json({'error': '缺少邮箱或密码参数'}, status=400)
    
    try:
        # 异步查询用户
        user = await request.ctx.db.execute(
            select(Users).where(Users.email == data['email'])
        )
        user = user.scalar()
        
        if not user:
            return json({'error': '用户不存在'}, status=404)
            
        # 加密新密码并更新
        encrypted_password = await sha1_encrypt(data['password'])
        user.password = encrypted_password
        request.ctx.db.add(user)
        await request.ctx.db.commit()
        
        return json({'message': '密码重置成功'}, status=200)
        
    except Exception as e:
        await request.ctx.db.rollback()
        return json({'error': f'密码重置失败: {str(e)}'}, status=500)
    finally:
        await request.ctx.db.close()

@manages_bp.post('/forgot-password')
async def forgot_password(request):
    '''
    summary: 忘记密码-发送重置邮件
    description: |
      用户忘记密码时，通过此接口向注册邮箱发送包含重置密码链接的邮件。
      本接口作为生产者，会将邮件发送任务添加到RabbitMQ消息队列中异步处理。
    参数:
      - name: email
        in: body
        required: true
        schema:
          type: string
          format: email
          example: user@example.com
        description: 用户注册时使用的邮箱地址
    响应:
      200:
        description: 邮件发送任务已成功加入队列
        schema:
          type: object
          properties:
            message:
              type: string
              example: 密码重置邮件已发送
      400:
        description: 请求参数缺失或格式错误
      404:
        description: 邮箱对应的用户不存在
      500:
        description: 服务器内部处理错误或消息队列服务异常
    '''
    data = request.json
    if 'email' not in data:
        return json({'error': '缺少邮箱参数'}, status=400)
    try:
        # 异步查询用户是否存在
        user = await request.ctx.db.execute(
            select(Users).where(Users.email == data['email'])
        )
        user = user.scalar()
        
        if not user:
            return json({'error': '用户不存在'}, status=404)
        
        try:
            host_server = 'smtp.sina.com'  #qq邮箱smtp服务器
            sender_qq = 'cf_taoister@sina.com' #发件人邮箱
            pwd = '48f3438493561d47'
            receiver = data['email']#收件人邮箱
            mail_title = '【笔羽】- 重制密码' #邮件标题
            reset_url = f"{Config.baseurl}:5173/reset-password/{data['email']}"
            mail_content = f"""请复制并打开链接重制密码:{reset_url}?resetpara={time.time()}""" #邮件正文内容
            msg = MIMEMultipart()
            msg["Subject"] = Header(mail_title,'utf-8')
            msg["From"] = sender_qq
            msg['To'] = ";".join(receiver)
            msg.attach(MIMEText(mail_content,'plain','utf-8'))
            smtp = SMTP_SSL(host_server,465) # ssl登录
            smtp.login(sender_qq,pwd)
            smtp.sendmail(sender_qq,receiver,msg.as_string())
            smtp.quit()
        except Exception as e:
            return json({'message': f"{data['email']}邮件发送失败:{str(e)}"}, status=400)
        # # 创建RabbitMQ连接
        # connection = pika.BlockingConnection(
        #     pika.ConnectionParameters(host=Config.rabbitmq.host, 
        #                               port=Config.rabbitmq.port, 
        #                               credentials=pika.PlainCredentials(Config.rabbitmq.user, 
        #                                                                 Config.rabbitmq.password)))
        # channel = connection.channel()
        # # 声明队列(如果不存在则创建)
        # channel.queue_declare(queue='forgot_pass_email', durable=True)
        # # 发布消息到队列
        # channel.basic_publish(exchange='', routing_key='forgot_pass_email', body=pack_json.dumps(data), properties=pika.BasicProperties(delivery_mode=2))# delivery_mode=2 消息持久化
        # # 关闭连接
        # connection.close()
        return json({'message': '密码重置邮件已发送'}, status=200)
        
    except Exception as e:
        return json({'error': f'发送密码重置邮件失败: {str(e)}'}, status=500)
    finally:
        await request.ctx.db.close()
    
@manages_bp.get('/getbooklist')
@login_required
@query_decorator(usefuncname = True, ex=3600)
async def getbooklist(request):
    '''
    获取用户book list，查询书名匹配查询字符串的书籍列表。如果query为''则查询全部。
    参数:
      - query:查询字符串
      type:str
      - userid ：用户id
      type：int
      - page ：分页页数，不传默认取第一页。
      type：int
    响应：
      - booklist：符合条件的书籍列表
      type：[object]
      - all_page：列表分页总页数。
      type：int
      - current_page:当前分页
      type：int
    '''
    try:
        # 获取请求参数
        user_id = request.args.get('userid')
        query = request.args.get('query', '').strip()
        page = int(request.args.get('page', 1))
        per_page = 10  # 每页显示10条记录
        
        if not user_id:
            return json({'error': '缺少用户ID参数'}, status=400)
            
        # 构建基础查询
        books_query = select(Books).where(Books.user_id == user_id)
        
        # 添加书名查询条件
        if query:
            books_query = books_query.where(Books.title.like(f'%{query}%'))
            
        # 计算总数和分页
        total_count = await request.ctx.db.execute(select(func.count()).select_from(books_query))
        total_count = total_count.scalar()
        all_page = (total_count + per_page - 1) // per_page
        offset = (page - 1) * per_page
        
        # 执行分页查询
        books = await request.ctx.db.execute(
            books_query.order_by(Books.id.desc())
            .offset(offset)
            .limit(per_page)
        )
        books = books.scalars().all()
        
        # 构建返回数据
        book_list = []
        for book in books:
            # 查询最新章节
            latest_chapter = await request.ctx.db.execute(
                select(Chapters)
                .join(Volumes, Volumes.id == Chapters.volume_id)
                .where((Volumes.book_id == book.id) & (Chapters.status == 2))
                .order_by(Chapters.id.desc())
                .limit(1)
            )
            latest_chapter = latest_chapter.scalar()
            
            # 查询最新视频
            latest_video = await request.ctx.db.execute(
                select(Videos)
                .where(Videos.book_id == book.id)
                .order_by(Videos.id.desc())
                .limit(1)
            )
            latest_video = latest_video.scalar()
            
            book_list.append({
                'id': book.id,
                'title': book.title,
                'tags': book.tags,
                'summary': book.summary,
                'surface_plot': book.surface_plot,
                'stats': book.stats,
                'count_word_num': book.count_word_num,
                'latest_chapter': {
                    'id': latest_chapter.id if latest_chapter else None,
                    'title': latest_chapter.title if latest_chapter else None,
                    'chapter_number': latest_chapter.chapter_number if latest_chapter else None
                },
                'latest_video': {
                    'id': latest_video.id if latest_video else None,
                    'chapter_id': latest_video.chapter_id if latest_video else None,
                    'chapter_number': latest_video.chapter.chapter_number if latest_video and latest_video.chapter else None,
                    'title': latest_video.chapter.title if latest_video and latest_video.chapter else None
                }
            })
            
        return json({
            'booklist': book_list,
            'all_page': all_page,
            'current_page': page,
        }, status=200)
        
    except Exception as e:
        return json({'error': f'获取书籍列表失败: {str(e)}'}, status=500)
    finally:
        await request.ctx.db.close()
    
@manages_bp.get('/oss_put_url')
@login_required
async def oss_put_url(request):
    '''获取oss上传文件的预签名URL
    '''
    try:
      # Config
      s3endpoint = 'https://s3.bitiful.net' # 请填入控制台 “Bucket 设置” 页面底部的 “Endpoint” 标签中的信息
      s3region = 'cn-east-1'
      s3accessKeyId = 'sjr5iR96Jtfz9psHg9PleA0L' # 请到控制台创建子账户，并为子账户创建相应 accessKey
      s3SecretKeyId = 'X9z8YkfjCTn05s4wsNa78y9pvFPmp6F' # ！！切记，创建子账户时，需要手动为其分配具体权限！！

      # 连接 S3
      client = boto3.client(
          's3',
          aws_access_key_id = s3accessKeyId,
          aws_secret_access_key = s3SecretKeyId,
          endpoint_url = s3endpoint,
          region_name = s3region
      )
      url = client.generate_presigned_url(
          'put_object',
          Params={
              'Bucket': '01-ai-creation',
              'Key': request.args.get('key'),
          },
          ExpiresIn=3600
      )
      response = json({'url': url}, status=200)
      # 添加CORS头
      response.headers["Access-Control-Allow-Origin"] = "*"
      return response
    except Exception as e:
        return json({'error': e}, status=500)

@manages_bp.get('/oss_get_url')
@login_required
async def oss_get_url(request):
    '''获取oss下载文件的预签名URL
    '''
    try:
      # Config
      s3endpoint = 'https://s3.bitiful.net' # 请填入控制台 “Bucket 设置” 页面底部的 “Endpoint” 标签中的信息
      s3region = 'cn-east-1'
      s3accessKeyId = 'sjr5iR96Jtfz9psHg9PleA0L' # 请到控制台创建子账户，并为子账户创建相应 accessKey
      s3SecretKeyId = 'X9z8YkfjCTn05s4wsNa78y9pvFPmp6F' # ！！切记，创建子账户时，需要手动为其分配具体权限！！

      # 连接 S3
      client = boto3.client(
          's3',
          aws_access_key_id = s3accessKeyId,
          aws_secret_access_key = s3SecretKeyId,
          endpoint_url = s3endpoint,
          region_name = s3region
      )
      url = client.generate_presigned_url(
          'get_object',
          Params={
              'Bucket': '01-ai-creation',
              'Key': request.args.get('key'),
          },
          ExpiresIn=60
      )
      response = json({'url': url}, status=200)
      # 添加CORS头
      response.headers["Access-Control-Allow-Origin"] = "*"
      return response
    except Exception as e:
        return json({'error': e}, status=500)

@manages_bp.post('/savebook')
@login_required
async def savebook(request):
    '''
    创建/更新书籍：数据库写入新数据(增/改)，删除书籍list的相关缓存(通过书名过滤）。
    参数：
      - bookinfo:书籍信息
      type:object
      Examples:{
        "userid":id,"bookid":id,"name":"书名","tag":"标签","covers":"封面图oss地址","introduction":"简介","timeSetting":"时间设定","spaceSetting":"空间设定"
      }
    '''
    data = request.json
    required_keys = ['userid', 'name', 'tag', 'covers', 'introduction', 'timeSetting', 'spaceSetting']
    if not all(key in data for key in required_keys):
        return json({'error': '缺少必要参数'}, status=400)

    try:
        # 更新已有书籍
        if 'bookid' in data and data['bookid']:
            # 查询要更新的书籍
            book = await request.ctx.db.execute(
                select(Books).where(
                    (Books.id == data['bookid']) & 
                    (Books.user_id == data['userid'])
                )
            )
            book = book.scalar()

            # 检查同名书籍
            same_name_book = await request.ctx.db.execute(
                select(Books).where(
                    (Books.user_id == data['userid']) & 
                    (Books.title == data['name']) &
                    (Books.id != data['bookid'])  # 排除当前书籍
                )
            )
            same_name_book = same_name_book.scalar()
            
            if same_name_book:
                return json({'error': '您已创建过同名书籍'}, status=400)
            
            if not book:
                return json({'error': '书籍不存在或不属于当前用户'}, status=404)
                
            # 更新书籍信息
            book.title = data['name']
            book.tags = data['tag']
            book.surface_plot = data['covers']
            book.summary = data['introduction']
            book.time_setting = data['timeSetting']
            book.space_setting = data['spaceSetting']
            
            request.ctx.db.add(book)
            message = '书籍更新成功'
            
        # 创建新书籍
        else:
            # 检查同名书籍
            existing_book = await request.ctx.db.execute(
                select(Books).where(
                    (Books.user_id == data['userid']) & 
                    (Books.title == data['name'])
                )
            )
            existing_book = existing_book.scalar()
            
            if existing_book:
                return json({'error': '您已创建过同名书籍'}, status=400)

            # 创建新书籍
            new_book = Books(
                user_id=data['userid'],
                title=data['name'],
                tags=data['tag'],
                surface_plot=data['covers'],
                summary=data['introduction'],
                time_setting=data['timeSetting'],
                space_setting=data['spaceSetting'],
                stats='创作中',
                count_word_num=0
            )
            
            request.ctx.db.add(new_book)
            message = '书籍创建成功'

        await request.ctx.db.commit()

        # 删除该用户的所有书籍列表缓存
        RedisManager().delete_pattern(f"getbooklist:page=['*']:userid=['{data['userid']}']")
        RedisManager().delete_pattern(f"getbooklist:page=['*']:query=['*']:userid=['{data['userid']}']")
        RedisManager().delete_pattern(f"bookinfo:id=['{book.id if 'bookid' in data else new_book.id}']")

        return json({
            'message': message,
            'book_id': book.id if 'bookid' in data else new_book.id,
            'title': data['name']
        }, status=200)
        
    except Exception as e:
        await request.ctx.db.rollback()
        return json({'error': f'操作失败: {str(e)}'}, status=500)
    finally:
        await request.ctx.db.close()

@manages_bp.delete('/delbook')
@login_required
async def delbook(request):
    '''
    删除书籍：删除指定ID的书籍
    参数：
        - id:书籍ID
        type:int
    '''
    try:
        data = request.json
        if not data or 'id' not in data:
            return json({'error': '缺少书籍ID参数'}, status=400)

        # 先删除所有关联的子记录
        await request.ctx.db.execute(
            delete(Characters).where(Characters.book_id == data['id'])
        )
        await request.ctx.db.execute(
            delete(Locations).where(Locations.book_id == data['id'])
        )
        await request.ctx.db.execute(
            delete(Volumes).where(Volumes.book_id == data['id'])
        )
        await request.ctx.db.execute(
            delete(Relationships).where(Relationships.book_id == data['id'])
        )
        await request.ctx.db.execute(
            delete(Videos).where(Videos.book_id == data['id'])
        )

        # 查询并删除书籍
        book = await request.ctx.db.execute(
            select(Books).where(Books.id == data['id'])
        )
        book = book.scalar()
        
        if not book:
            return json({'error': '书籍不存在'}, status=404)

        # 获取用户ID用于清理缓存
        user_id = book.user_id
        
        # 执行删除操作
        await request.ctx.db.delete(book)
        await request.ctx.db.commit()

        # 清理该用户的所有书籍列表缓存
        RedisManager().delete_pattern(f"getbooklist:page=['*']:userid=['{user_id}']")
        RedisManager().delete_pattern(f"getbooklist:page=['*']:query=['*']:userid=['{user_id}']")
        RedisManager().delete_pattern(f"bookinfo:id=['{data['id']}']")

        return json({'message': '书籍删除成功'}, status=200)

    except Exception as e:
        await request.ctx.db.rollback()
        return json({'error': f'删除失败: {str(e)}'}, status=500)
    finally:
        await request.ctx.db.close()
    
@manages_bp.get('/bookinfo')
@login_required
@query_decorator(usefuncname = True, ex=3600)
async def bookinfo(request):
    '''
    获取书籍：获取指定ID的书籍info
    参数：
        - id:书籍ID
        type:int
    '''
    try:
        book_id = request.args.get('id')
        if not book_id:
            return json({'error': '缺少书籍ID参数'}, status=400)
            
        # 查询书籍基础信息
        book = await request.ctx.db.execute(
            select(
                Books.title,
                Books.tags,
                Books.summary,
                Books.surface_plot,
                Books.space_setting,
                Books.time_setting
            ).where(Books.id == book_id)
        )
        book_info = book.first()
        
        if not book_info:
            return json({'error': '书籍不存在'}, status=404)
            
        return json({
            'title': book_info.title,
            'tags': book_info.tags,
            'summary': book_info.summary,
            'surface_plot': book_info.surface_plot,
            'space_setting': book_info.space_setting,
            'time_setting': book_info.time_setting
        }, status=200)
        
    except Exception as e:
        return json({'error': f'查询书籍信息失败: {str(e)}'}, status=500)
    finally:
        await request.ctx.db.close()

@manages_bp.get('/book_characters')
@login_required
@query_decorator(usefuncname = True, ex=3600)
async def book_characters(request):
    '''
    获取书籍角色列表：获取指定书籍ID的所有角色信息
    参数：
        - query: 查询条件
        type: str
        - book_id: 书籍ID
        type: int
        - page: 分页页数，不传默认取第一页
        type: int
    响应：
        - characters: 角色列表
        type: [object]
        - all_page: 列表分页总页数
        type: int
        - current_page: 当前分页
        type: int
    '''
    try:
        book_id = request.args.get('book_id')
        query = request.args.get('query', '')
        page = int(request.args.get('page', 1))
        per_page = 10  # 每页显示10条记录
        
        if not book_id:
            return json({'error': '缺少书籍ID参数'}, status=400)
        
        # 构建基础查询
        characters_query = select(Characters).where(Characters.book_id == book_id)
        
        # 添加查询条件
        if query:
            characters_query = characters_query.where(Characters.name.like(f'%{query}%'))
        
        # 计算总数和分页
        total_count = await request.ctx.db.execute(
            select(func.count()).select_from(characters_query)
        )
        total_count = total_count.scalar()
        all_page = (total_count + per_page - 1) // per_page
        offset = (page - 1) * per_page
        
        # 执行分页查询
        characters = await request.ctx.db.execute(
            characters_query.order_by(Characters.id)
            .offset(offset)
            .limit(per_page)
        )
        characters = characters.scalars().all()
        
        if not characters:
            return json({
                'characters': [],
                'all_page': all_page,
                'current_page': page
            }, status=200)
        
        # 构建返回数据
        character_list = []
        for char in characters:
            character_list.append({
                'id': char.id,
                'name': char.name,
                'gender': char.gender,
                'personality': char.personality,
                'background': char.background,
                'age': char.age,
                'occupation': char.occupation,
                'appearance': char.appearance,
                'physique': char.physique,
                'face_image': char.face_image,
                'race': char.race
            })
        
        return json({
            'characters': character_list,
            'all_page': all_page,
            'current_page': page
        }, status=200)
        
    except Exception as e:
        return json({'error': f'查询角色列表失败: {str(e)}'}, status=500)
    finally:
        await request.ctx.db.close()

@manages_bp.delete('/delcharacters')
@login_required
async def deletecharacter(request):
    """
    删除指定角色:以及相关的角色关系记录
    参数:
        id (int): 角色ID
        book_id(ing):书籍ID
    返回:
        json: 操作结果
    """
    try:
        data = request.json
        character_id = data.get('id')
        book_id = data.get('book_id')
        
        if not character_id:
            return json({'error': '缺少角色ID参数'}, status=400)
        
        if not book_id:
            return json({'error': '缺少书籍ID参数'}, status=400)
            
        # 检查角色是否存在
        character = await request.ctx.db.execute(
            select(Characters).where(Characters.id == character_id)
        )
        character = character.scalar_one_or_none()
        
        if not character:
            return json({'error': '角色不存在'}, status=404)
            
        # 先删除该角色的所有关系记录
        await request.ctx.db.execute(
            delete(Relationships).where(
                (Relationships.source_id == character_id) | 
                (Relationships.target_id == character_id)
            )
        )
            
        # 再删除角色
        await request.ctx.db.execute(
            delete(Characters).where(Characters.id == character_id))
        await request.ctx.db.commit()
        
        # 删除 角色相关的redis 缓存
        RedisManager().delete_pattern(f"book_characters:book_id=['{book_id}']:page=['*']")
        RedisManager().delete_pattern(f"book_characters:book_id=['{book_id}']:page=['*']:query=['*']")
        RedisManager().delete_pattern(f"querycharacter:book_id=['{book_id}']")
        RedisManager().delete_pattern(f"characterrelations:character_id=['{character_id}']")
        return json({'message': '角色及相关关系记录删除成功'}, status=200)
        
    except Exception as e:
        await request.ctx.db.rollback()
        return json({'error': f'删除角色失败: {str(e)}'}, status=500)
    finally:
        await request.ctx.db.close()
    
@manages_bp.post('/savecharacter')
@login_required
async def savecharacter(request):
    """
    保存角色数据, 如果ID为空则新增数据,如果不为空则更新数据
    参数：
        - characterinfo 
        type:object
        Examples:{
            "id": "2",
            "book_id":"13",
            "name": "科比",
            "gender": "男",
            "personality": "要强，好胜心重",
            "background": "1996年美国男子篮球第一高中生",
            "age": "23",
            "occupation": "篮球运动员",
            "appearance": "光头，双眼皮，瓜子脸，高鼻梁",
            "physique": "身高臂长，腿长",
            "avatar": "https://aigc-files.bigmodel.cn/api/cogview/20250506164441efb6aa09b0524886_0.png",
            "race": "人类"
            "relations":[ // 角色关系列表 「关联角色name」是「me」的什么relationship
                {
                  name: '米老鼠',
                  id: 1,
                  relationship: '好友' 
                }
            ]
        }
    """
    try:
        data = request.json
        required_fields = ['name', 'gender', 'book_id']
        if not all(field in data for field in required_fields):
            return json({'error': '缺少必要参数'}, status=400)

        db = request.ctx.db
        
        # 更新或创建角色
        if 'id' in data and data['id']:
            # 更新现有角色
            character = await db.execute(
                select(Characters).where(Characters.id == data['id']))
            character = character.scalar_one_or_none()
            
            if not character:
                return json({'error': '角色不存在'}, status=404)
                
            character.name = data['name']
            character.gender = data['gender']
            character.personality = data.get('personality')
            character.background = data.get('background')
            character.age = data.get('age')
            character.occupation = data.get('occupation')
            character.appearance = data.get('appearance')
            character.physique = data.get('physique')
            character.face_image = data.get('avatar')
            character.race = data.get('race')
            
            character_id = data['id']
        else:
            # 创建新角色
            character = Characters(
                book_id=data['book_id'],
                name=data['name'],
                gender=data['gender'],
                personality=data.get('personality'),
                background=data.get('background'),
                age=data.get('age'),
                occupation=data.get('occupation'),
                appearance=data.get('appearance'),
                physique=data.get('physique'),
                face_image=data.get('avatar'),
                race=data.get('race')
            )
            db.add(character)
            await db.flush()
            character_id = character.id

        # 处理角色关系
        if 'relations' in data:
            # 先删除该角色作为target的所有关系
            await db.execute(
                delete(Relationships).where(Relationships.target_id == character_id))
            
            # 添加新的关系
            for relation in data['relations']:
                if 'id' in relation and relation['id']:
                    new_relation = Relationships(
                        book_id=data['book_id'],
                        source_id=relation['id'],
                        target_id=character_id,
                        relationship_type=relation['relationship']
                    )
                    db.add(new_relation)

        await db.commit()
        # 删除 角色相关的redis 缓存
        RedisManager().delete_pattern(f"book_characters:book_id=['{data['book_id']}']:page=['*']")
        RedisManager().delete_pattern(f"book_characters:book_id=['{data['book_id']}']:page=['*']:query=['*']")
        RedisManager().delete_pattern(f"querycharacter:book_id=['{data['book_id']}']")
        RedisManager().delete_pattern(f"characterrelations:character_id=['{character_id}']")
        return json({'message': '角色保存成功', 'id': character_id}, status=200)
        
    except Exception as e:
        await request.ctx.db.rollback()
        return json({'error': f'保存角色失败: {str(e)}'}, status=500)
    finally:
        await request.ctx.db.close()
    
@manages_bp.get('/querycharacter')
@login_required
@query_decorator(usefuncname = True, ex=3600)
async def querycharacter(request):
    """
    查询角色：获取书籍全部角色信息
    参数：
        - book_id:书籍id
        type:int
    响应：
        - characterlist: 角色列表
        type:list[object]
        Examples:[
            {
                "id":1,
                "name":"名字"
            }
        ]
    """
    try:
        book_id = request.args.get('book_id')
        
        if not book_id:
            return json({'error': '缺少书籍ID参数'}, status=400)
            
        # 查询所有角色
        characters = await request.ctx.db.execute(
            select(
                Characters.id,
                Characters.name
            ).where(
                Characters.book_id == book_id
            ).order_by(Characters.id)
        )
        
        character_list = [{'id': c.id, 'name': c.name} for c in characters.all()]
        
        return json({
            'characterlist': character_list
        }, status=200)
        
    except Exception as e:
        return json({'error': f'查询角色失败: {str(e)}'}, status=500)
    finally:
        await request.ctx.db.close()
    
@manages_bp.get('/characterrelations')
@login_required
@query_decorator(usefuncname = True, ex=3600)
async def characterrelations(request):
    """
    查询某角色的关系列表 target_id = character_id
    参数：
        - character_id:角色的id 
        type:int
    响应：
        - relations:角色关系列表
        type:list[object]
        Examples:[
            {
                "id":1, //source_id
                "name":"名字",
                "relationship": "好友" //relationship_type
            }
        ]
    """
    try:
        character_id = request.args.get('character_id')
        
        if not character_id:
            return json({'error': '缺少角色ID参数'}, status=400)
            
        # 查询该角色的所有关系
        relations = await request.ctx.db.execute(
            select(
                Relationships.source_id,
                Characters.name,
                Relationships.relationship_type
            ).join(
                Characters, Relationships.source_id == Characters.id
            ).where(
                Relationships.target_id == character_id
            ).order_by(Relationships.source_id)
        )
        
        relation_list = [{
            'id': r.source_id,
            'name': r.name,
            'relationship': r.relationship_type
        } for r in relations.all()]
        
        return json({
            'relations': relation_list
        }, status=200)
        
    except Exception as e:
        return json({'error': f'查询角色关系失败: {str(e)}'}, status=500)
    finally:
        await request.ctx.db.close()
    
@manages_bp.get('/querysescene')
@login_required
@query_decorator(usefuncname = True, ex=3600)
async def querysescene(request):
    '''
    查询场景列表：获取指定书籍ID的所有场景信息
    参数：
        - book_id: 书籍ID
        type: int
        - query: 查询条件
        type: str
        - page: 分页页数，不传默认取第一页
        type: int
    响应：
        - scenes: 场景列表
        type: [object]
        - all_page: 列表分页总页数
        type: int
        - current_page: 当前分页
        type: int
    '''
    try:
        # 获取请求参数
        book_id = request.args.get('book_id')
        query = request.args.get('query', '').strip()
        page = int(request.args.get('page', 1))
        per_page = 10  # 每页显示10条记录
        
        if not book_id:
            return json({'error': '缺少书籍ID参数'}, status=400)
            
        # 构建基础查询
        scenes_query = select(Locations).where(Locations.book_id == book_id)
        
        # 添加场景名称查询条件
        if query:
            scenes_query = scenes_query.where(Locations.space_name.like(f'%{query}%'))
            
        # 计算总数和分页
        total_count = await request.ctx.db.execute(select(func.count()).select_from(scenes_query))
        total_count = total_count.scalar()
        all_page = (total_count + per_page - 1) // per_page
        offset = (page - 1) * per_page
        
        # 执行分页查询
        scenes = await request.ctx.db.execute(
            scenes_query.order_by(Locations.id.desc())
            .offset(offset)
            .limit(per_page)
        )
        scenes = scenes.scalars().all()
        
        # 构建返回数据
        scene_list = []
        for scene in scenes:
            scene_list.append({
                'id': scene.id,
                'space_name': scene.space_name,
                'description': scene.description,
                'image': scene.image,
                'space_use': scene.space_use
            })
            
        return json({
            'scenes': scene_list,
            'all_page': all_page,
            'current_page': page
        }, status=200)
        
    except Exception as e:
        return json({'error': f'查询场景列表失败: {str(e)}'}, status=500)
    finally:
        await request.ctx.db.close()

@manages_bp.post('/savesescene')
@login_required
async def savesescene(request):
    """
    保存场景数据，如果ID为空则新增数据，如果不为空则更新数据
    参数：
        - sceneinfo 
        type:object
        Examples:{
            "id": "2",
            "book_id":"13",
            "space_name": "场景名称",
            "description": "场景描述",
            "image": "场景图片URL",
            "space_use": "场景用途"
        }
    响应：
        - message: 操作结果消息
        type: str
        - id: 场景ID
        type: int
    """
    try:
        data = request.json
        required_fields = ['book_id', 'space_name']
        if not all(field in data for field in required_fields):
            return json({'error': '缺少必要参数'}, status=400)

        db = request.ctx.db
        
        # 更新或创建场景
        if 'id' in data and data['id']:
            # 更新现有场景
            scene = await db.execute(
                select(Locations).where(Locations.id == data['id']))
            scene = scene.scalar_one_or_none()
            
            if not scene:
                return json({'error': '场景不存在'}, status=404)
                
            scene.space_name = data['space_name']
            scene.description = data.get('description')
            scene.image = data.get('image')
            scene.space_use = data.get('space_use')
            
            scene_id = data['id']
        else:
            # 创建新场景
            scene = Locations(
                book_id=data['book_id'],
                space_name=data['space_name'],
                description=data.get('description'),
                image=data.get('image'),
                space_use=data.get('space_use')
            )
            db.add(scene)
            await db.flush()
            scene_id = scene.id

        await db.commit()
        # 删除场景相关的redis缓存
        RedisManager().delete_pattern(f"querysescene:book_id=['{data['book_id']}']:page=['*']")
        RedisManager().delete_pattern(f"querysescene:book_id=['{data['book_id']}']:page=['*']:query=['*']")
        return json({'message': '场景保存成功', 'id': scene_id}, status=200)
        
    except Exception as e:
        await request.ctx.db.rollback()
        return json({'error': f'保存场景失败: {str(e)}'}, status=500)
    finally:
        await request.ctx.db.close()

@manages_bp.post('/deletesescene')
@login_required
async def deletesescene(request):
    """
    删除指定场景
    参数:
        id (int): 场景ID
        book_id(ing):书籍ID
    返回:
        json: 操作结果
    """
    try:
        data = request.json
        scene_id = data.get('id')
        book_id = data.get('book_id')
        
        if not scene_id:
            return json({'error': '缺少场景ID参数'}, status=400)
        
        if not book_id:
            return json({'error': '缺少书籍ID参数'}, status=400)
            
        # 检查场景是否存在
        scene = await request.ctx.db.execute(
            select(Locations).where(Locations.id == scene_id)
        )
        scene = scene.scalar_one_or_none()
        
        if not scene:
            return json({'error': '场景不存在'}, status=404)
            
        # 执行删除操作
        await request.ctx.db.execute(
            delete(Locations).where(Locations.id == scene_id))
        await request.ctx.db.commit()
        
        # 删除场景相关的redis缓存
        RedisManager().delete_pattern(f"querysescene:book_id=['{book_id}']:page=['*']")
        RedisManager().delete_pattern(f"querysescene:book_id=['{book_id}']:page=['*']:query=['*']")
        return json({'message': '场景删除成功'}, status=200)
        
    except Exception as e:
        await request.ctx.db.rollback()
        return json({'error': f'删除场景失败: {str(e)}'}, status=500)
    finally:
        await request.ctx.db.close()

@manages_bp.get('/get-volumes-chapters')
@login_required
@query_decorator(usefuncname = True, ex=3600)
async def getvolumeschapters(request):
    """
    查询书籍的卷-章结构：
    [
        {
            id: 1,
            label: '英雄崛起',
            num: 1,
            type: 'volume',
            stage: '起始阶段',
            summary: '这是一个关于年轻剑客成长的故事，讲述了主角从默默无闻到成为一代宗师的历程。',
            children: [ //当前卷的章节列表（分页）
            {
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
            }
            ],
            total_chapters: 章节总数,
            current_page: 当前页码,
            total_pages: 总页数
        }
    ]
    参数：
        - bookid
        type:int
        - page: 分页页码，不传则查询最后一页
        type:int
    响应：
        - message: 操作结果消息
        type: str
        - volumeschaptersinfo: 查询结果
        type: object
    """
    try:
        book_id = request.args.get('bookid')
        page = request.args.get('page')
        per_page = 10  # 每页显示10个章节
        
        if not book_id:
            return json({'error': '缺少书籍ID参数'}, status=400)
            
        # 查询所有卷
        volumes = await request.ctx.db.execute(
            select(Volumes).where(
                Volumes.book_id == book_id
            ).order_by(Volumes.num))
        volumes = volumes.scalars().all()
        
        if not volumes:
            return json({'volumeschaptersinfo': []}, status=200)
        
        # 构建返回数据结构
        result = []
        
        for volume in volumes:
            # 计算该卷的章节总数
            total_chapters = await request.ctx.db.execute(
                select(func.count(Chapters.id)).where(
                    Chapters.volume_id == volume.id
                )
            )
            total_chapters = total_chapters.scalar()
            
            if total_chapters == 0:
                result.append({
                    'id': volume.id,
                    'label': volume.title,
                    'num': volume.num,
                    'type': 'volume',
                    'stage': volume.phase,
                    'summary': volume.overview,
                    'children': [],
                    'total_chapters': 0,
                    'current_page': 1,
                    'total_pages': 0
                })
                continue
            
            # 计算总页数
            total_pages = (total_chapters + per_page - 1) // per_page
            
            # 确定当前页码
            if page is None:
                # 不传page参数则查询最后一页
                current_page = total_pages
            else:
                current_page = int(page)
                # 确保页码在有效范围内
                if current_page < 1:
                    current_page = 1
                elif current_page > total_pages:
                    current_page = total_pages
            
            # 计算偏移量
            offset = (current_page - 1) * per_page
            
            # 分页查询当前卷的章节
            chapters = await request.ctx.db.execute(
                select(Chapters).where(
                    Chapters.volume_id == volume.id
                ).order_by(Chapters.chapter_number)
                .offset(offset)
                .limit(per_page)
            )
            chapters = chapters.scalars().all()
            
            chapter_list = []
            
            for chapter in chapters:
                # 获取章节所属的书籍ID
                chapter_book_id = await request.ctx.db.execute(
                    select(Volumes.book_id).where(Volumes.id == chapter.volume_id)
                )
                chapter_book_id = chapter_book_id.scalar()
                
                chapter_list.append({
                    'id': chapter.id,
                    'chapter_number': chapter.chapter_number,
                    'title': chapter.title,
                    'overview': chapter.overview if chapter.overview is not None else '',
                    'plots_text': chapter.plots_text if chapter.plots_text is not None else '',
                    'ai_creation': chapter.ai_creation if chapter.ai_creation is not None else '',
                    'human_creation': chapter.human_creation if chapter.human_creation is not None else '',
                    'status': chapter.status if chapter.status is not None else 0,
                    'ai_plots_text': chapter.ai_plots_text if chapter.ai_plots_text is not None else '',
                    'book_id': chapter_book_id
                })
            
            result.append({
                'id': volume.id,
                'label': volume.title,
                'num': volume.num,
                'type': 'volume',
                'stage': volume.phase,
                'summary': volume.overview,
                'children': chapter_list,
                'total_chapters': total_chapters,
                'current_page': current_page,
                'total_pages': total_pages
            })
        
        return json({
            'message': '查询成功',
            'volumeschaptersinfo': result
        }, status=200)
        
    except Exception as e:
        return json({'error': f'查询卷章结构失败: {str(e)}'}, status=500)
    finally:
        await request.ctx.db.close()
    
@manages_bp.post('/savechapters')
@login_required
async def savechapters(request):
    """
    保存章节信息：
        1. 查询书籍是否有卷，如果没有则创建一个卷
        2. 如果有卷，则查询该卷下是否存在该章节，如果存在则更新，不存在则新增
    参数：
        - chaptersinfo: 章节信息
        type: object
        Examples: {
            "id": null,
            "title": 章节标题,
            "chapter_number": 章节序号,
            "overview": 章节概述,
            "status": 章节状态,// 0-待创作，1-ai创作完成， 2-人工编辑完成
            "plots_text": 情节描述,
            "ai_plots_text": ai 情节设计信息,
            "ai_creation": AI 创作内容,
            "human_creation": 人工创作内容,
            "book_id":所属书籍id
        } 
    响应：
        - message: 操作结果消息
        type: str
        - id: 章节ID
        type: int
    """
    data = request.json
    if not data or 'chaptersinfo' not in data:
        return json({'error': '缺少章节信息参数'}, status=400)
    
    try:
        chapter_info = data['chaptersinfo']
        book_id = chapter_info.get('book_id')
        
        if not book_id:
            return json({'error': '缺少书籍ID参数'}, status=400)
        
        # 1. 查询书籍是否有卷，如果没有则创建一个卷
        existing_volume = await request.ctx.db.execute(
            select(Volumes).where(Volumes.book_id == book_id).limit(1)
        )
        existing_volume = existing_volume.scalar()
        
        if not existing_volume:
            # 创建默认卷
            new_volume = Volumes(
                book_id=book_id,
                title='第一卷',
                phase='起始阶段',
                overview='默认卷概述',
                num=1
            )
            request.ctx.db.add(new_volume)
            await request.ctx.db.flush()  # 确保卷ID被生成
            target_volume_id = new_volume.id
        else:
            # 使用第一个卷或指定的卷
            target_volume_id = chapter_info.get('volume_id', existing_volume.id)
        
        c_id = None
        
        # 2. 更新已有章节
        if 'id' in chapter_info and chapter_info['id']:
            chapter = await request.ctx.db.execute(
                select(Chapters).where(Chapters.id == chapter_info['id'])
            )
            chapter = chapter.scalar()
            
            if not chapter:
                return json({'error': '章节不存在'}, status=404)
                
            # 更新章节信息
            chapter.title = chapter_info.get('title', chapter.title)
            chapter.overview = chapter_info.get('overview', chapter.overview)
            chapter.plots_text = chapter_info.get('plots_text', chapter.plots_text)
            chapter.ai_plots_text = chapter_info.get('ai_plots_text', chapter.ai_plots_text)
            chapter.status = chapter_info.get('status', chapter.status)
            chapter.ai_creation = chapter_info.get('ai_creation', chapter.ai_creation)
            chapter.human_creation = chapter_info.get('human_creation', chapter.human_creation)
            
            request.ctx.db.add(chapter)
            message = '章节更新成功'
            c_id = chapter.id
        # 3. 创建新章节
        else:
            # 检查是否已存在相同章节号的章节
            existing_chapter = await request.ctx.db.execute(
                select(Chapters).where(
                    (Chapters.volume_id == target_volume_id) &
                    (Chapters.chapter_number == chapter_info.get('chapter_number', 1))
                )
            )
            existing_chapter = existing_chapter.scalar()
            
            if existing_chapter:
                # 如果存在相同章节号的章节，则更新它
                existing_chapter.title = chapter_info.get('title', existing_chapter.title)
                existing_chapter.overview = chapter_info.get('overview', existing_chapter.overview)
                existing_chapter.plots_text = chapter_info.get('plots_text', existing_chapter.plots_text)
                existing_chapter.ai_plots_text = chapter_info.get('ai_plots_text', existing_chapter.ai_plots_text)
                existing_chapter.status = chapter_info.get('status', existing_chapter.status)
                existing_chapter.ai_creation = chapter_info.get('ai_creation', existing_chapter.ai_creation)
                existing_chapter.human_creation = chapter_info.get('human_creation', existing_chapter.human_creation)
                
                request.ctx.db.add(existing_chapter)
                message = '章节更新成功'
                c_id = existing_chapter.id
            else:
                # 创建新章节
                new_chapter = Chapters(
                    volume_id=target_volume_id,
                    chapter_number=chapter_info.get('chapter_number', 1),
                    title=chapter_info.get('title', ''),
                    overview=chapter_info.get('overview', ''),
                    plots_text=chapter_info.get('plots_text', ''),
                    ai_plots_text=chapter_info.get('ai_plots_text', ''),
                    ai_creation=chapter_info.get('ai_creation', ''),
                    human_creation=chapter_info.get('human_creation', ''),
                    status=chapter_info.get('status', 0)
                )
                
                request.ctx.db.add(new_chapter)
                await request.ctx.db.flush()  # 确保ID被生成
                c_id = new_chapter.id
                message = '章节创建成功'
            
        await request.ctx.db.commit()
        
        # 清除Redis缓存
        RedisManager().delete_pattern(f"getvolumeschapters:bookid=['{book_id}']")
        RedisManager().delete_pattern(f"getvolumeschapters:bookid=['{book_id}']:page=['*']")
        
        return json({
            'message': message,
            'id': c_id
        }, status=200)

    except Exception as e:
        await request.ctx.db.rollback()
        return json({'error': f'保存章节失败: {str(e)}'}, status=500)
    finally:
        await request.ctx.db.close()

@manages_bp.delete('/chapters')
@login_required
async def delchapters(request):
    """
    删除章节信息
    参数：
        - chapter_id: 章节ID
        type: int
        - book_id: 所属书籍ID
        type: int
    响应：
        - message: 操作结果消息
        type: str
    """
    try:
        data = request.json
        chapter_id = data.get('chapter_id')
        if not chapter_id:
            return json({'error': 'Missing required parameter: chapter_id'}, 400)
        try:
            chapter_id = int(chapter_id)
        except ValueError:
            return json({'error': 'chapter_id must be an integer'}, 400)
        # 查询章节是否存在
        chapter = await request.ctx.db.execute(
            select(Chapters).where(Chapters.id == chapter_id)
        )
        chapter = chapter.scalar_one_or_none()
        if not chapter:
            return json({'error': 'Chapter not found'}, 404)
        # 删除章节及其关联的情节
        await request.ctx.db.delete(chapter)
        # 将删除章节之后的章节的序号减1
        await request.ctx.db.execute(
            Chapters.__table__.update()
           .where(
                Chapters.volume_id == chapter.volume_id,
                Chapters.chapter_number > chapter.chapter_number
            )
           .values(chapter_number=Chapters.chapter_number - 1)
        )
        await request.ctx.db.commit()
        # 清除Redis缓存
        RedisManager().delete_pattern(f"getvolumeschapters:bookid=['{data['book_id']}']")
        RedisManager().delete_pattern(f"getvolumeschapters:bookid=['{data['book_id']}']:page=['*']")
        return json({'message': 'Chapter and plots deleted successfully'}, 200)
    except Exception as e:
        await request.ctx.db.rollback()
        return json({'error': f'Failed to delete chapter: {str(e)}'}, 500)
    finally:
        await request.ctx.db.close()
    
# 获取模型配置
@manages_bp.get('/get-model-config')
@login_required
async def get_model_config(request):
    """
    获取模型配置
    响应：
        - model_config: 模型配置
        type: object
    """
    try:
        # 从配置文件中获取模型配置
        # model_config = await get_model_conf()
        # config_dict = pack_json.loads(model_config)
        # # 移除uuid字段
        # if 'uuid' in config_dict:
        #     del config_dict['uuid']

        # 从配置数据库中获取模型配置
        conf_t = get_model_config_sqlite()
        return json({
            'model_config': {
                "creations":{
                    "model": f"{next(t for t in conf_t if t[3] == 2)[0]}",
                    "api_key": f"{next(t for t in conf_t if t[3] == 2)[2]}",
                    "base_url": f"{next(t for t in conf_t if t[3] == 2)[1]}"
                },
                "chat":{
                    "model": f"{next(t for t in conf_t if t[3] == 0)[0]}",
                    "api_key": f"{next(t for t in conf_t if t[3] == 0)[2]}",
                    "base_url": f"{next(t for t in conf_t if t[3] == 0)[1]}"
                },
                "plots":{
                    "model": f"{next(t for t in conf_t if t[3] == 1)[0]}",
                    "api_key": f"{next(t for t in conf_t if t[3] == 1)[2]}",
                    "base_url": f"{next(t for t in conf_t if t[3] == 1)[1]}"
                },
                "img":{
                    "model": "cogview-3-flash",
                    "api_key": f"{next(t for t in conf_t if t[3] == 3)[2]}",
                    "base_url": "https://open.bigmodel.cn/api/paas/v4/images/generations"
                }
            }    
        }, status=200)
        
    except Exception as e:
        return json({'error': f'获取模型配置失败: {str(e)}'}, status=500)

# 修改模型配置
@manages_bp.post('/update-model-config')
@login_required
async def update_model_config(request):
    """
    更新模型配置
    参数：
        - model_config: 模型配置
        type: object
    响应：
        - message: 更新成功消息
        type: string
        Example: 模型配置已更新
    """
    try:
        data = request.json
        if not data or 'model_config' not in data:
            return json({'error': '缺少模型配置参数'}, status=400)
        model_config = data['model_config']
        # 验证配置格式
        if not isinstance(model_config, dict):
            return json({'error': '模型配置必须是一个对象'}, status=400)
        # 更新配置文件
        # await encrypt_config(model_config)
        # 更新数据库
        conn  = sqlite3.connect(Config.sqlite3.file_path)
        cursor = conn.cursor()
        for i in model_config:
            sql = f"""UPDATE model_config SET model_code = '{
                model_config[i]['model'] if model_config[i]['model'] else ''
                }', base_url = '{
                model_config[i]['base_url'] if model_config[i]['base_url'] else ''
                }', api_key = '{
                model_config[i]['api_key'] if model_config[i]['api_key'] else ''
                }' WHERE type = {
                (2 if i == 'creations' else 0 if i == 'chat' else 1 if i == 'plots' else 3)
                }"""
            cursor.execute(sql)
        conn.commit()
        return json({'message': '模型配置已更新'}, status=200)
    except Exception as e:
        return json({'error': f'更新模型配置失败: {str(e)}'}, status=500)

@manages_bp.get('/get-chapter-info')
@login_required
async def get_chapter_info(request):
    """
    查询某章信息
    参数：
        - bookid: 书籍ID
        type: int
        - chapternumber: 章节序号
        type: int
    响应：
        {
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
        }
    """
    try:
        book_id = request.args.get('bookid')
        chapter_number = request.args.get('chapternumber')
        
        if not book_id or not chapter_number:
            return json({'error': '缺少书籍ID或章节序号参数'}, status=400)
            
        # 查询章节信息，需要通过书籍ID和章节序号定位到具体章节
        chapter = await request.ctx.db.execute(
            select(Chapters)
            .join(Volumes, Volumes.id == Chapters.volume_id)
            .where(
                (Volumes.book_id == book_id) &
                (Chapters.chapter_number == chapter_number)
            )
        )
        chapter = chapter.scalar()
        
        if not chapter:
            return json({'error': '章节不存在'}, status=404)
            
        return json({
            'id': chapter.id,
            'chapter_number': chapter.chapter_number,
            'title': chapter.title,
            'overview': chapter.overview if chapter.overview is not None else '',
            'plots_text': chapter.plots_text if chapter.plots_text is not None else '',
            'ai_creation': chapter.ai_creation if chapter.ai_creation is not None else '',
            'human_creation': chapter.human_creation if chapter.human_creation is not None else '',
            'status': chapter.status if chapter.status is not None else 0,
            'ai_plots_text': chapter.ai_plots_text if chapter.ai_plots_text is not None else '',
            'book_id': book_id
        }, status=200)
        
    except Exception as e:
        return json({'error': f'查询章节信息失败: {str(e)}'}, status=500)
    finally:
        await request.ctx.db.close()

@manages_bp.get('/get-end-human-creation')
@login_required
async def get_end_human_creation(request):
    """
    获取最后一个状态为2的章节之后的章节所在的分页数据
    参数：
        - bookid: 书籍ID
        type: int
    响应：
        [
            {
                id: 1,
                label: '英雄崛起',
                num: 1,
                type: 'volume',
                stage: '起始阶段',
                summary: '这是一个关于年轻剑客成长的故事，讲述了主角从默默无闻到成为一代宗师的历程。',
                children: [ //当前卷的章节列表（分页）
                {
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
                }
                ],
                total_chapters: 章节总数,
                current_page: 当前页码,
                total_pages: 总页数
            }
        ]
    """
    try:
        book_id = request.args.get('bookid')
        if not book_id:
            return json({'error': '缺少书籍ID参数'}, status=400)
            
        per_page = 10  # 每页显示10个章节
        
        # 1. 查找最后一个状态为2的章节
        last_completed_chapter = await request.ctx.db.execute(
            select(Chapters)
            .join(Volumes, Volumes.id == Chapters.volume_id)
            .where(
                (Volumes.book_id == book_id) &
                (Chapters.status == 2)
            )
            .order_by(Volumes.num.desc(), Chapters.chapter_number.desc())
            .limit(1)
        )
        last_completed_chapter = last_completed_chapter.scalar()
        
        # 2. 如果没有状态为2的章节，则从第一个卷的第一个章节开始
        if not last_completed_chapter:
            # 获取第一个卷
            first_volume = await request.ctx.db.execute(
                select(Volumes)
                .where(Volumes.book_id == book_id)
                .order_by(Volumes.num)
                .limit(1)
            )
            first_volume = first_volume.scalar()
            
            if not first_volume:
                return json({'volumeschaptersinfo': []}, status=200)
                
            # 获取第一个卷的第一个章节
            first_chapter = await request.ctx.db.execute(
                select(Chapters)
                .where(Chapters.volume_id == first_volume.id)
                .order_by(Chapters.chapter_number)
                .limit(1)
            )
            first_chapter = first_chapter.scalar()
            
            if not first_chapter:
                return json({'volumeschaptersinfo': []}, status=200)
                
            target_volume_id = first_volume.id
            target_chapter_number = first_chapter.chapter_number
            
        else:
            # 3. 找到最后一个状态为2的章节的下一个章节
            # 先尝试在同一卷中查找下一个章节
            next_chapter = await request.ctx.db.execute(
                select(Chapters)
                .where(
                    (Chapters.volume_id == last_completed_chapter.volume_id) &
                    (Chapters.chapter_number > last_completed_chapter.chapter_number)
                )
                .order_by(Chapters.chapter_number)
                .limit(1)
            )
            next_chapter = next_chapter.scalar()
            
            if next_chapter:
                target_volume_id = next_chapter.volume_id
                target_chapter_number = next_chapter.chapter_number
            else:
                # 如果在同一卷中没有找到，则查找下一卷的第一个章节
                current_volume = await request.ctx.db.execute(
                    select(Volumes)
                    .where(Volumes.id == last_completed_chapter.volume_id)
                )
                current_volume = current_volume.scalar()
                
                if not current_volume:
                    return json({'volumeschaptersinfo': []}, status=400)
                    
                next_volume = await request.ctx.db.execute(
                    select(Volumes)
                    .where(
                        (Volumes.book_id == book_id) &
                        (Volumes.num > current_volume.num)
                    )
                    .order_by(Volumes.num)
                    .limit(1)
                )
                next_volume = next_volume.scalar()
                
                if not next_volume:
                    return json({'volumeschaptersinfo': []}, status=200)
                    
                # 获取下一卷的第一个章节
                first_chapter_next_volume = await request.ctx.db.execute(
                    select(Chapters)
                    .where(Chapters.volume_id == next_volume.id)
                    .order_by(Chapters.chapter_number)
                    .limit(1)
                )
                first_chapter_next_volume = first_chapter_next_volume.scalar()
                
                if not first_chapter_next_volume:
                    return json({'volumeschaptersinfo': []}, status=200)
                    
                target_volume_id = next_volume.id
                target_chapter_number = first_chapter_next_volume.chapter_number
        
        # 4. 获取目标卷的信息
        target_volume = await request.ctx.db.execute(
            select(Volumes)
            .where(Volumes.id == target_volume_id)
        )
        target_volume = target_volume.scalar()
        
        if not target_volume:
            return json({'volumeschaptersinfo': []}, status=400)
            
        # 5. 计算目标章节在卷中的页码
        total_chapters = await request.ctx.db.execute(
            select(func.count(Chapters.id))
            .where(Chapters.volume_id == target_volume_id)
        )
        total_chapters = total_chapters.scalar()
        
        if total_chapters == 0:
            return json({'volumeschaptersinfo': []}, status=200)
            
        # 计算目标章节所在的页码
        target_page = (target_chapter_number - 1) // per_page + 1
        
        # 6. 获取目标卷的分页章节数据
        offset = (target_page - 1) * per_page
        
        chapters = await request.ctx.db.execute(
            select(Chapters)
            .where(Chapters.volume_id == target_volume_id)
            .order_by(Chapters.chapter_number)
            .offset(offset)
            .limit(per_page)
        )
        chapters = chapters.scalars().all()
        
        chapter_list = []
        
        for chapter in chapters:
            chapter_list.append({
                'id': chapter.id,
                'chapter_number': chapter.chapter_number,
                'title': chapter.title,
                'overview': chapter.overview if chapter.overview is not None else '',
                'plots_text': chapter.plots_text if chapter.plots_text is not None else '',
                'ai_creation': chapter.ai_creation if chapter.ai_creation is not None else '',
                'human_creation': chapter.human_creation if chapter.human_creation is not None else '',
                'status': chapter.status if chapter.status is not None else 0,
                'ai_plots_text': chapter.ai_plots_text if chapter.ai_plots_text is not None else '',
                'book_id': book_id
            })
        
        # 7. 构建返回数据
        result = [{
            'id': target_volume.id,
            'label': target_volume.title,
            'num': target_volume.num,
            'type': 'volume',
            'stage': target_volume.phase,
            'summary': target_volume.overview,
            'children': chapter_list,
            'total_chapters': total_chapters,
            'current_page': target_page,
            'total_pages': (total_chapters + per_page - 1) // per_page
        }]
        
        return json({
            'volumeschaptersinfo': result
        }, status=200)
        
    except Exception as e:
        return json({'error': f'获取后续章节数据失败: {str(e)}'}, status=500)
    finally:
        await request.ctx.db.close()