import asyncio
import json
import re
from bilibili_api import video, Credential, settings, ass
import os
from datetime import datetime
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# 增加下面的代码避免网络报错
settings.http_client = settings.HTTPClient.HTTPX

lessons_urls = ["BV13U1VYmEUr",
"BV1u61jYSExg",
"BV15MShYkEgg",
"BV1XxStYYEH1",
"BV1CkSUYGE1v",
"BV1ExDQYyEAA",
"BV1tjS7YfEWJ",
"BV1YzDJY1E2i",
"BV1G9SJYGEtD",
"BV1dtD4YKENj",
"BV19RzcYaEFy",
"BV18aUHY3EEG",
"BV1nESCYWEnN"] 

def convert_ass_to_txt(ass_file_path):
    """将.ass字幕文件转换为纯文本格式"""
    dialogue_pattern = re.compile(r'Dialogue:.*,,(.+)$')
    clean_pattern = re.compile(r'\{.*?\}')
    
    with open(ass_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 提取对话内容
    dialogues = []
    for line in lines:
        if line.startswith('Dialogue:'):
            match = dialogue_pattern.match(line)
            if match:
                text = match.group(1)
                # 清理特殊格式标记
                text = clean_pattern.sub('', text)
                # 清理可能存在的\N换行标记
                text = text.replace('\\N', ' ').strip()
                if text:
                    dialogues.append(text)
    
    # 生成txt文件路径
    txt_file_path = os.path.splitext(ass_file_path)[0] + '.txt'
    
    # 保存为txt文件
    with open(txt_file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(dialogues))
    
    return txt_file_path

def sanitize_filename(filename):
    """清理文件名，移除非法字符"""
    # 替换 Windows 和类 Unix 系统中的非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    return re.sub(illegal_chars, '_', filename)

async def download_subtitle(video_url):
    # 支持多种URL格式的正则表达式
    bv_patterns = [
        r'BV\w{10}',  # 匹配纯BV号
        r'bilibili\.com/video/(BV\w{10})',  # 匹配标准网址中的BV号
        r'b23\.tv/(BV\w{10})'  # 匹配短链接中的BV号
    ]
    
    bv_id = None
    for pattern in bv_patterns:
        match = re.search(pattern, video_url)
        if match:
            bv_id = match.group(1) if '(' in pattern else match.group()
            print(f"找到BV号: {bv_id}")
            print(f"使用的匹配模式: {pattern}")
            break
    
    if not bv_id:
        raise ValueError("无效的B站视频URL，未找到BV号。请确保URL包含正确的BV号。")
    
    # 从环境变量中获取认证信息
    sessdata = os.getenv('BILIBILI_SESSDATA')
    bili_jct = os.getenv('BILIBILI_BILI_JCT')
    buvid3 = os.getenv('BILIBILI_BUVID3')
    
    if not all([sessdata, bili_jct, buvid3]):
        raise ValueError("缺少必要的认证信息，请检查.env文件是否包含所有必需的环境变量。")
    
    # 创建视频对象
    credential = Credential(sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3)
    v = video.Video(bvid=bv_id)
    
    try:
        # 获取视频信息
        video_info = await v.get_info()
        title = video_info['title']
        # 清理标题中的非法字符
        title = sanitize_filename(title)
        #cid = video_info['cid']
        print(title)
        # 确保Data目录存在
        os.makedirs('Data', exist_ok=True)
        
        # 直接在Data目录下保存文件
        ass_path = os.path.join('Data', f'{title}.ass')
        await ass.make_ass_file_subtitle(v, out=ass_path, credential=credential)
        print(f"ASS字幕已保存到: {ass_path}")
        
        # 转换为txt格式
        txt_path = convert_ass_to_txt(ass_path)
        print(f"TXT字幕已保存到: {txt_path}")
        
        # 删除原始ass文件
        os.remove(ass_path)
        print("已删除原始ASS文件")
        
    except Exception as e:
        print(f"下载字幕时出错: {str(e)}")

async def process_all_urls():
    # 逐个处理URL
    for i, url in enumerate(lessons_urls, 1):
        print(f"\n正在处理第 {i}/{len(lessons_urls)} 个视频...")
        try:
            await download_subtitle(url)
            # 如果不是最后一个视频，等待5秒
            if i < len(lessons_urls):
                print("等待5秒后继续下载下一个视频...")
                await asyncio.sleep(5)
        except Exception as e:
            print(f"处理视频 {url} 时出错: {str(e)}")
            # 即使出错也继续处理下一个
            continue

def main():
    # 直接处理预定义的URL列表
    asyncio.run(process_all_urls())

if __name__ == "__main__":
    main()
