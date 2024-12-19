import time
from openai import OpenAI
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def setup_client():
    base_url = "https://internlm-chat.intern-ai.org.cn/puyu/api/v1/"
    api_key = os.getenv("SILICONFLOW_API_KEY")
    model = "internlm2.5-latest"
    return OpenAI(api_key=api_key, base_url=base_url), model

def polish_text(client, model, text):
    if not text.strip():
        return text
        
    prompt = f"""请润色以下文本，保持专业术语的准确性，使表达更加流畅自然：

{text}

注意：保留 InternLM, Lagent, MindSearch, LLamaIndex, OpenCompass, Xtuner, Multi-agent, 
书生浦语, InternVL2, transformer 等专业术语的原有形式。如果有类似这样的术语形式，但是却书写错误的，请修改为以上术语。"""
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            
            polished_text = response.choices[0].message.content
            
            # 验证返回的文本
            if not polished_text or polished_text.strip() == text.strip():
                print(f"警告：API 返回的文本与原文相同或为空")
                retry_count += 1
                time.sleep(2)
                continue
                
            return polished_text
            
        except Exception as e:
            print(f"处理出错 (尝试 {retry_count + 1}/{max_retries}): {str(e)}")
            retry_count += 1
            time.sleep(2)
            
    print("达到最大重试次数，返回原文本")
    return text

def process_text_in_batches(file_path, batch_size=100):
    client, model = setup_client()
    
    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # 按行分割
    lines = text.split('\n')
    batches = [lines[i:i + batch_size] for i in range(0, len(lines), batch_size)]
    
    polished_text = []
    
    for batch in batches:
        # 合并批次中的行
        batch_text = '\n'.join(batch)
        
        # 润色处理
        polished_batch = polish_text(client, model, batch_text)
        polished_text.append(polished_batch)
        
        # 延时6秒
        time.sleep(6)
    
    # 保存结果
    output_path = 'polished_' + os.path.basename(file_path)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(polished_text))
    
    return output_path

def process_data_folder(folder_path="Data", batch_size=100):
    """处理指定文件夹中的所有文本文件"""
    client, model = setup_client()
    
    # 确保文件夹存在
    if not os.path.exists(folder_path):
        print(f"错误：找不到文件夹 {folder_path}")
        return
    
    # 创建输出文件夹
    output_folder = "Polished_Data"
    os.makedirs(output_folder, exist_ok=True)
    
    # 获取所有文件
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    print(f"找到 {len(files)} 个文件待处理")
    
    for index, file_name in enumerate(files, 1):
        input_path = os.path.join(folder_path, file_name)
        print(f"\n处理第 {index}/{len(files)} 个文件: {file_name}")
        
        try:
            # 读取文件
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # 按行分割
            lines = text.split('\n')
            batches = [lines[i:i + batch_size] for i in range(0, len(lines), batch_size)]
            
            polished_text = []
            
            for batch_num, batch in enumerate(batches, 1):
                print(f"处理批次 {batch_num}/{len(batches)}")
                # 合并批次中的行
                batch_text = '\n'.join(batch)
                
                # 润色处理
                polished_batch = polish_text(client, model, batch_text)
                print(polished_batch)
                polished_text.append(polished_batch)
                
                # 延时6秒
                time.sleep(6)
            
            # 保存结果
            output_path = os.path.join(output_folder, f"polished_{file_name}")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(polished_text))
            
            print(f"文件 {file_name} 处理完成")
            
        except Exception as e:
            print(f"处理文件 {file_name} 时出错: {str(e)}")
            continue

# 使用示例
if __name__ == "__main__":
    process_data_folder("Data")  # 替换为你的Data文件夹路径
    print("所有文件处理完成！")