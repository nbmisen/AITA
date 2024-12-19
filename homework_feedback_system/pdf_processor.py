import streamlit as st
import os
import fitz  # PyMuPDF
import io
from PIL import Image
import tempfile
from llama_index.core import Document
import base64

class PDFProcessor:
    """PDF处理器类，用于提取PDF中的文本和图片"""
    
    def __init__(self):
        self.supported_formats = ['jpeg', 'jpg', 'png']
        self.max_image_size = 10 * 1024 * 1024  # 10MB
        self.min_image_dimension = 10
        self.max_image_dimension = 2000
        self.content_blocks = []
    
    def process_pdf(self, pdf_file):
        """处理PDF文件，按顺序提取文本和图片"""
        text_content = ""
        image_documents = []
        self.content_blocks = []
        
        if not pdf_file:
            st.error("请上传PDF文件")
            return "", []
        
        try:
            # 将上传的文件保存到临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(pdf_file.read())
                temp_path = temp_file.name
            
            # 使用PyMuPDF打开PDF
            doc = fitz.open(temp_path)
            
            # 遍历每一页
            for page in doc:
                # 获取文本块
                text_blocks = page.get_text("blocks")
                for block in text_blocks:
                    self.content_blocks.append({
                        'type': 'text',
                        'content': block[4]
                    })
                
                # 提取图片
                image_list = page.get_images()
                for img_num, img in enumerate(image_list, 1):
                    try:
                        image_doc = self._process_single_image(doc, img, 1, img_num)  # 页码设为1，因为我们不需要追踪页码
                        if image_doc:
                            self.content_blocks.append({
                                'type': 'image',
                                'content': image_doc
                            })
                            image_documents.append(image_doc)
                    except Exception as e:
                        print(f"处理图片时出错: {e}")
                        continue
            
            # 生成有序的文档内容
            ordered_content = []
            for block in self.content_blocks:
                if block['type'] == 'text':
                    ordered_content.append(block['content'])
                else:
                    # 在文本中标记图片位置
                    ordered_content.append(f"[IMAGE_{len(image_documents)}]")
            
            text_content = "\n".join(ordered_content)
            
            # 关闭文档
            doc.close()
            
            # 清理临时文件
            os.unlink(temp_path)
            
            if not image_documents:
                st.warning("未能从PDF中提取到任何有效图片")
            else:
                st.success(f"成功提取了 {len(image_documents)} 张图片")
            
            return text_content, image_documents
        
        except Exception as e:
            st.error(f"处理PDF文件时出错: {str(e)}")
            print(f"PDF处理错误: {e}")
            return "", []
    
    def _process_single_image(self, doc, img, page_num, img_num):
        """处理单张图片"""
        try:
            xref = img[0]
            base_image = doc.extract_image(xref)
            
            if base_image["ext"] not in self.supported_formats:
                print(f"不支持的图片格式: {base_image['ext']}")
                return None
            
            image_bytes = base_image["image"]
            
            # 检查图片大小
            if len(image_bytes) > self.max_image_size:
                print(f"第 {page_num} 页的图片 {img_num} 太大，跳过")
                return None
            
            # 使用PIL打开图片进行处理
            img_stream = io.BytesIO(image_bytes)
            pil_image = Image.open(img_stream)
            
            # 检查图片尺寸
            if pil_image.width < self.min_image_dimension or pil_image.height < self.min_image_dimension:
                print(f"第 {page_num} 页的图片 {img_num} 尺寸太小，跳过")
                return None
            
            # 确保图片是RGB模式
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # 限制图片最大尺寸
            if pil_image.width > self.max_image_dimension or pil_image.height > self.max_image_dimension:
                ratio = min(self.max_image_dimension/pil_image.width, 
                          self.max_image_dimension/pil_image.height)
                new_size = (int(pil_image.width * ratio), int(pil_image.height * ratio))
                pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
            
            # 将处理后的图片转换为base64
            output_buffer = io.BytesIO()
            pil_image.save(output_buffer, format='JPEG', quality=85, optimize=True)
            output_buffer.seek(0)
            img_data = output_buffer.getvalue()
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            
            # 创建图片文档，直接存储base64字符串
            image_doc = Document(
                text=img_base64,  # 存储base64编码的图片数据
                metadata_={
                    "page_number": page_num,
                    "image_number": img_num,
                    "size": (pil_image.width, pil_image.height),
                    "format": 'JPEG',
                    "original_format": base_image["ext"]
                }
            )
            
            # 显示处理后的图片
            st.image(img_data, caption=f"第 {page_num} 页 图片 {img_num}", use_container_width=True)
            
            return image_doc
            
        except Exception as e:
            print(f"处理图片时出错: {e}")
            return None
