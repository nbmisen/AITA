import streamlit as st
import os
from dotenv import load_dotenv
from pdf_processor import PDFProcessor
import openai

# 加载环境变量
load_dotenv()

# Siliconflow配置
api_key = os.getenv("SILICONFLOW_API_KEY")
api_base = "https://api.siliconflow.cn/v1"
model = "Qwen/Qwen2-VL-72B-Instruct"

def init_client():
    """初始化API客户端"""
    client = openai.OpenAI(
        api_key=api_key,
        base_url=api_base
    )
    return client

def analyze_homework(pdf_processor, client, homework_requirements=None):
    """分析作业内容并提供反馈"""
    # 构建system prompt
    system_prompt = """你是一个专业的作业评价助手。
    
作业要求：
{}

请根据作业要求和内容提供详细的评价，包含以下方面：
1. 作业要求完成情况
2. 内容完整性评估
3. 作业质量评估
4. 具体的优点
5. 需要改进的地方
6. 建议和改进方向

请特别关注作业是否满足作业要求中的具体标准。""".format(homework_requirements if homework_requirements else "无具体要求")

    # 构建有序的内容列表
    content_items = []
    for block in pdf_processor.content_blocks:
        if block['type'] == 'text':
            content_items.append({
                "type": "text",
                "text": block['content']
            })
        else:
            img_base64 = block['content'].text.strip()
            content_items.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_base64}"
                }
            })
    
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": content_items
        }
    ]
    
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    return response.choices[0].message.content

def get_homework_requirements():
    """获取作业要求列表"""
    homework_dir = "Homeworks"
    homework_files = []
    
    # 确保目录存在
    if os.path.exists(homework_dir):
        # 获取所有markdown文件
        for file in os.listdir(homework_dir):
            if file.endswith('.md'):
                title = file[:-3]  # 移除.md后缀
                homework_files.append({
                    'title': title,
                    'path': os.path.join(homework_dir, file)
                })
    
    return homework_files

def read_homework_content(file_path):
    """取作业要求内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return f"读取作业要求出错: {str(e)}"

def main():
    st.title("📚 AITA 助教作业批改")
    
    client = init_client()
    pdf_processor = PDFProcessor()
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # 获取作业要求列表
    homework_files = get_homework_requirements()
    
    # 作业要求选择
    st.write("### 📋 选择作业要求")
    homework_titles = ["请选择作业"] + [hw['title'] for hw in homework_files]
    selected_title = st.selectbox("作业类型：", homework_titles)
    
    # 显示选中的作业要求
    selected_requirements = None
    if selected_title != "请选择作业":
        selected_file = next((hw for hw in homework_files if hw['title'] == selected_title), None)
        if selected_file:
            selected_requirements = read_homework_content(selected_file['path'])
            st.write("### 📝 作业要求")
            st.markdown(selected_requirements)
    
    # 文件上传
    st.write("### 📤 上传作业")
    uploaded_file = st.file_uploader("选择PDF文件", type=['pdf'])
    
    if uploaded_file is not None:
        st.write("### 📄 分析结果")
        
        with st.spinner('正在分析PDF文件...'):
            # 处理PDF文件
            pdf_processor.process_pdf(uploaded_file)
            
            if pdf_processor.content_blocks:
                # 分析作业内容
                analysis = analyze_homework(pdf_processor, client, selected_requirements)
                st.write("### ✍️ 作业评价")
                st.markdown(analysis)
            else:
                st.error("未能从PDF中提取到任何内容")

    # 交互式问答
    st.write("### 💬 追加问题")
    user_input = st.text_input("输入你的问题:")
    if user_input and uploaded_file:
        with st.spinner("AI思考中..."):
            # 构建包含历史记录的消息列表
            messages = []
            
            # 添加历史对话记录
            for role, content in st.session_state.chat_history[-6:]:  # 保留最近3轮对话
                messages.append({"role": role, "content": content})
                
            # 添加当前用户问题
            messages.append({"role": "user", "content": user_input})
            
            response = client.chat.completions.create(
                model=model,
                messages=messages
            )
            
            ai_response = response.choices[0].message.content
            st.session_state.chat_history.append(("user", user_input))
            st.session_state.chat_history.append(("assistant", ai_response))
        
        # 显示聊天历史
        for role, message in st.session_state.chat_history:
            if role == "user":
                st.write(f"👤 你: {message}")
            else:
                st.write(f"🤖 AI: {message}")

if __name__ == "__main__":
    main()