# -*- coding: utf-8 -*-
# ttf2png 生成书籍封面
import base64
import glob
from io import BytesIO
import random
import os, sys
project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
sys.path.insert(0,project_root_dir)
from PIL import Image, ImageDraw, ImageFont
from tools.ai_create_img import zhipuT2iApi
from openai import OpenAI
import os, requests, json
import numpy as np

def draw_text_to_png(text, font_path, output_file = None, direction='horizontal', text_color='black', font_size = None):
    """
    将指定文本使用给定字体渲染为PNG图片
    
    参数:
        text (str): 要渲染的文本内容
        font_path (str): 字体文件路径(.ttf)
        output_file (str): 输出图片路径(.png)
        direction (str): 文字排列方向，'horizontal'横向或'vertical'竖向，默认为横向
        text_color (str): 文字颜色，支持颜色名称或十六进制值，默认为黑色
        font_size(int): 最终生成的文字图像大小像素（单字）
    返回:
        None: 直接保存图片到指定路径
    """
    # 设置默认字体大小
    if font_size is None:
        font_size = 40

    font = ImageFont.truetype(font_path, size=font_size)

    # 定义单个字符的宽度和高度
    char_width = font_size
    char_height = font_size
    
    # 根据文字方向和字数动态计算图像大小
    if direction == 'horizontal':
        # 横向排列：宽度=文本总宽度+边距，高度=字符高度+边距
        text_bbox = font.getbbox(text)
        text_width = text_bbox[2] - text_bbox[0]
        img_width = text_width + 30
        img_height = char_height + 30
    else:
        # 竖向排列：宽度=字符宽度+边距，高度=字符数*字符高度+边距
        img_width = char_width + 30
        img_height = len(text) * char_height + 30
    
    # 创建透明图像对象
    img = Image.new('RGBA', (img_width, img_height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # 计算居中位置
    if direction == 'horizontal':
        x = (img_width - text_width) // 2
        y = (img_height - char_height) // 2
        draw.text((x, y), text, fill=text_color, font=font)
    else:
        x = (img_width - char_width) // 2
        y = (img_height - len(text) * char_height) // 2
        for char in text:
            draw.text((x, y), char, fill=text_color, font=font)
            y += char_height
    if output_file:
        img.save(output_file)
    return img

def evaluate_brightness(image):
    """评估图像亮度
    参数:
        image: PIL.Image对象
    
    返回:
        tuple: (平均亮度值, 亮度等级, 主色相)
    """
    # 将图像转为灰度图计算亮度
    gray = image.convert('L')
    gray_array = np.array(gray)
    mean = np.mean(gray_array)
    
    # 判断亮度结果
    if mean > 150:
        brightness = "明亮"
    elif mean < 80:
        brightness = "灰暗"
    else:
        brightness = "中等"
    
    # 计算主色相
    hsv = image.convert('HSV')
    hsv_array = np.array(hsv)
    hue = hsv_array[:,:,0]
    
    # 计算色相直方图
    hist = np.histogram(hue, bins=12, range=(0,255))[0]
    dominant_hue = np.argmax(hist) * 30  # 转换为0-360度色相
    
    # 将色相转换为描述性文字
    hue_names = ['红色', '橙红色', '橙色', '黄橙色', 
                '黄色', '黄绿色', '绿色', '青绿色',
                '青色', '蓝青色', '蓝色', '紫蓝色']
    hue_name = hue_names[dominant_hue // 30]
    
    return mean, brightness, hue_name

def getcolor(img):
    client = OpenAI(api_key="f934eba8f1875a6c32e8e8d31d26e6f9.iEAr5rRdW8uuwLIE", base_url="https://open.bigmodel.cn/api/paas/v4/")
    response = client.chat.completions.create(
        model="glm-4v-flash",  # 填写需要调用的模型名称
        messages=[
            {
            "role": "user", 
            "content": [
                {
                "type": "image_url",
                "image_url": {
                    "url" : img
                }
                },
                {
                "type": "text",
                "text": "这个图是生成的书籍方面图，分析图像颜色，给出合适的书名文字字体颜色建议，直接输出设置。例如：#000000"
                }
            ]
            },
        ],
    )
    return response.choices[0].message.content.replace(' ','')

def create_cover(
        prompt,
        book_name, 
        book_author
        ):
    '''
    生成书籍封面图
    '''
    # 提取书名，作者，生图prompt。
    # 默认按照2:3大小生成图像：864x1152。
    imgurl = zhipuT2iApi(prompt=prompt)
    if type(imgurl) != str:
        return imgurl
    # 下载生成的封面图片
    response = requests.get(imgurl)
    # 生成的封面图片
    cover_img = Image.open(BytesIO(response.content))
    ## 书名：最大8个字｜字体大小 100px
    ## 作者：最大10个字｜字体大小 40px
    direction = random.choice(['horizontal', 'vertical'])
    # 调用方法
    _, brightness, hue_name = evaluate_brightness(cover_img)
    # 将封面图片转为base64格式
    # buffered = BytesIO()
    # cover_img.save(buffered, format="PNG")
    # img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    # print(getcolor(img_base64))
    # print(_, brightness, hue_name)
    # 根据亮度和色相选择文字颜色
    if brightness == '明亮':  # 明亮背景使用深色文字
        if hue_name in ['红色', '橙红色', '橙色']:
            text_color = random.sample(['#131124', '#22202e', '#000000', '#2c3e50', '#1a1a2e', '#16213e', '#0f3460', '#1b1b2f'], 2)
        elif hue_name in ['黄色', '黄绿色', '绿色']:
            text_color = random.sample(['#35333c', '#2c3e50', '#000000', '#131124', '#1e272e', '#1e3799', '#0c2461', '#3c40c6'], 2)
        else:
            text_color = random.sample(['#000000', '#131124', '#22202e', '#2c3e50', '#1a237e', '#311b92', '#4a148c', '#880e4f'], 2)
    elif brightness == '中等':  # 中等亮度背景使用对比色
        if hue_name in ['红色', '橙红色']:
            text_color = random.sample(['#f1c40f', '#fffef9', '#fcd217', '#2ecc71', '#f39c12', '#e67e22', '#d35400', '#e74c3c'], 2)
        elif hue_name in ['黄色', '黄绿色']:
            text_color = random.sample(['#c02c38', '#e74c3c', '#9b59b6', '#3498db', '#8e44ad', '#2980b9', '#16a085', '#27ae60'], 2)
        else:
            text_color = random.sample(['#c02c38', '#fffef9', '#fcd217', '#fb9968', '#e74c3c', '#e67e22', '#d35400', '#f39c12'], 2)
    else:  # 灰暗背景使用亮色文字
        if hue_name in ['蓝色', '紫蓝色']:
            text_color = random.sample(['#fcd217', '#fb9968', '#fffef9', '#f1c40f', '#f6b93b', '#fa983a', '#e58e26', '#fad390'], 2)
        elif hue_name in ['青色', '蓝青色']:
            text_color = random.sample(['#c02c38', '#e74c3c', '#fffef9', '#f1c40f', '#e55039', '#eb2f06', '#fa983a', '#f6b93b'], 2)
        else:
            text_color = random.sample(['#c02c38', '#fffef9', '#fcd217', '#fb9968', '#e55039', '#eb2f06', '#f6b93b', '#fa983a'], 2)
    nameimg = draw_text_to_png(
        text=book_name,
        font_path=random.choice(glob.glob('static/name_ttf/*.ttf')),
        direction=direction, 
        text_color=text_color[0], 
        font_size = 100)
    # nameimg.show()
    authorimg = draw_text_to_png(
        text=f'{book_author}·著',
        font_path=random.choice(glob.glob('static/author_ttf/*.ttf')),
        direction=direction, 
        text_color=text_color[1], 
        font_size = 40)
    # authorimg.show()
    # 通过大模型结合文字图像大小给出合理布局。
    if direction == 'horizontal':
        # 计算合并位置
        cover_width, cover_height = cover_img.size
        name_width, name_height = nameimg.size
        author_width, author_height = authorimg.size

        # 书名放在封面顶部居中
        name_x = (cover_width - name_width) // 2
        name_y = 50  # 顶部留白50px
        
        # 作者放在封面底部居中
        author_x = (cover_width - author_width) // 2
        author_y = cover_height - author_height - 50  # 底部留白50px
    else:
        # 计算合并位置
        cover_width, cover_height = cover_img.size
        name_width, name_height = nameimg.size
        author_width, author_height = authorimg.size

        # 书名放在封面左上角
        name_x = 50  # 左侧留白50px
        name_y = 50  # 顶部留白50px
        
        # 作者放在封面右下角
        author_x = cover_width - author_width - 50  # 右侧留白50px
        author_y = cover_height - author_height - 50  # 底部留白50px
    
    # 合并图像
    cover_img.paste(nameimg, (name_x, name_y), nameimg)
    cover_img.paste(authorimg, (author_x, author_y), authorimg)
    # cover_img.show()
    # 将封面图像转为base64编码
    buffered = BytesIO()
    cover_img.save(buffered, format="PNG")
    cover_img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return cover_img_base64

# 示例用法
if __name__ == "__main__":
    # draw_text_to_png(
    #     text='暂无封面',
    #     output_file='./out.png',
    #     font_path='static/author_ttf/方正黑体-简体.TTF',
    #     direction='', 
    #     text_color='#EEEEEE', 
    #     font_size = 100)
    for i in range(4):
        img = create_cover(prompt='水墨风，古风，明朝背景，一位身着明朝盔甲的将军，面容坚毅，眼神凌厉，手持长枪，站在战马上，背景是古代战争场面，烽火连天，敌我双方厮杀，鲜血飞溅，色彩浓烈，具有史诗感，分辨率高，摄影风格，细节丰富，电影感，光线强烈，暗部细节丰富，杜尚风格，中外知名艺术家风格融合。',
                    book_name='大明战神李景隆',
                    book_author='杨叔儿1996')
    

    