# 智能作业反馈系统

这是一个基于 Streamlit 和 LlamaIndex 的智能作业反馈系统，使用多模态大模型处理 PDF 作业文件并提供智能反馈。

## 功能特点

- PDF文件上传和处理
- 文本提取和分析
- 图片内容识别（使用多模态大模型）
- 智能反馈生成
- 实时AI对话功能

## 安装要求

- Python 3.8+
- OpenAI API Key
- poppler-utils（用于PDF处理）

## 安装步骤

1. 克隆项目并进入项目目录：
```bash
cd homework_feedback_system
```

2. 创建并激活虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 安装系统依赖：
- Mac: `brew install poppler`
- Linux: `sudo apt-get install poppler-utils`
- Windows: 下载并安装 [poppler](http://blog.alivate.com.au/poppler-windows/)

## 使用方法

1. 设置环境变量：
   创建 `.env` 文件并添加你的 OpenAI API Key：
   ```
   OPENAI_API_KEY=你的API密钥
   ```

2. 运行应用：
```bash
streamlit run app.py
```

3. 在浏览器中打开显示的地址（通常是 http://localhost:8501）

## 使用说明

1. 在系统设置中输入 OpenAI API Key（如果未通过环境变量设置）
2. 上传 PDF 格式的作业文件
3. 系统会自动处理文件中的文本和图片内容
4. 使用多模态大模型分析作业内容并生成反馈
5. 可以通过聊天界面与 AI 助手进行交互

## 注意事项

- 请确保上传的 PDF 文件清晰可读
- 系统需要联网才能正常工作
- 请妥善保管你的 API Key
- 图片处理可能需要较长时间，请耐心等待