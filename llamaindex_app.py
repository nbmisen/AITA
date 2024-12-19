import streamlit as st
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.callbacks import CallbackManager
from llama_index.llms.openai_like import OpenAILike
from llama_index.embeddings.anyscale import AnyscaleEmbedding
from llama_index.core.node_parser import SentenceSplitter

import os

# Create an instance of CallbackManager
callback_manager = CallbackManager()

#api_base_url =  "https://internlm-chat.intern-ai.org.cn/puyu/api/v1/"
#model = "internlm2.5-latest"
#api_key = os.getenv("INTERN_TOKEN")
siliconflow_api_key = os.getenv("SILICONFLOW_API_KEY")
api_base_url =  "https://api.siliconflow.cn/v1"
model = "deepseek-ai/deepseek-vl2"
api_key = siliconflow_api_key

llm =OpenAILike(model=model, api_base=api_base_url, api_key=api_key, is_chat_model=True,callback_manager=callback_manager)



st.set_page_config(page_title="llama_index_demo", page_icon="🦜🔗")
st.title("llama_index_demo")

# 初始化模型
@st.cache_resource
def init_models():
    embed_model = AnyscaleEmbedding(
        model="BAAI/bge-m3",
        api_base="https://api.siliconflow.cn/v1",
        api_key=siliconflow_api_key
    )
    Settings.embed_model = embed_model

    #用初始化llm
    Settings.llm = llm
    # Github上的教程
    documents1 = SimpleDirectoryReader(
        "./Tutorial", 
        recursive=True,
        filename_as_id=True,
        required_exts=[".txt", ".md"]  # 明确指定文件类型
    ).load_data()
    # 视频课程字幕
    documents2 = SimpleDirectoryReader(
        "./Polished_Data", 
        recursive=True,
        filename_as_id=True,
        required_exts=[".txt", ".md"]
    ).load_data()

    documents = documents1 + documents2

    # 配置文本分块器
    node_parser = SentenceSplitter(
        chunk_size=128,  # 减小块大小
        chunk_overlap=10,  # 减小重叠
        separator=" ",  # 明确指定分隔符
        paragraph_separator="\n\n",
        secondary_chunking_regex="[。！？.!?]",
    )

    # 分批处理文档
    index = VectorStoreIndex.from_documents(
        documents,
        node_parser=node_parser,
        embed_batch_size=10,  # 添加批处理大小限制
        show_progress=True,   # 显示进度
    )

    # 配置查询引擎
    query_engine = index.as_query_engine(
        similarity_top_k=3,  # 限制返回结果数量
        streaming=True
    )

    return query_engine

# 检查是否需要初始化模型
if 'query_engine' not in st.session_state:
    st.session_state['query_engine'] = init_models()

def greet2(question):
    response = st.session_state['query_engine'].query(question)
    return response

      
# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "你好，我是你的助手，有什么我可以帮助你的吗？"}]    

    # Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "你好，我是你的助手，有什么我可以帮助你的吗？"}]

st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Function to read file content
def read_file_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

# Display directory contents in sidebar
st.sidebar.markdown("### 教程文档目录")
st.sidebar.markdown("#### Tutorial 文件夹:")
for item in ["docs", "tools", "video_subtitles", "configs", "data"]:
    if st.sidebar.checkbox(f"📁 {item}", key=f"tutorial_{item}"):
        files = os.listdir(os.path.join("./Tutorial", item))
        for file in files:
            with st.sidebar.expander(f"📄 {file}"):
                file_path = os.path.join("./Tutorial", item, file)
                content = read_file_content(file_path)
                st.code(content, language="text")

st.sidebar.markdown("#### 课程字幕文件夹:")
files = os.listdir("./Polished_Data")
for file in files:
    if file.startswith("polished_"):
        display_name = file.replace("polished_", "").replace(".txt", "")
        with st.sidebar.expander(f"📄 {display_name}"):
            file_path = os.path.join("./Polished_Data", file)
            content = read_file_content(file_path)
            st.code(content, language="text")

# Function for generating LLaMA2 response
def generate_llama_index_response(prompt_input):
    return greet2(prompt_input)

# User-provided prompt
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Gegenerate_llama_index_response last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_llama_index_response(prompt)
            placeholder = st.empty()
            placeholder.markdown(response)
    message = {"role": "assistant", "content": response}
    st.session_state.messages.append(message)