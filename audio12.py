import os
from docx import Document
from gtts import gTTS

# 定义文件夹及文件路径
folder_path = r"C:\Users\grace\VisualStudioProject\watermark-removal"
doc_path = os.path.join(folder_path, "Speaking.docx")
output_audio_path = os.path.join(folder_path, "Speaking_audio.mp3")

print("正在读取 Word 文档...")
doc = Document(doc_path)
full_text = []
for para in doc.paragraphs:
    if para.text.strip():
        full_text.append(para.text)

text = "\n".join(full_text)
print(f"提取完成，总字符数: {len(text)}")

# gTTS 单次请求有字符限制，按约 4000 字符分块
def split_text(text, max_length=4000):
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    for word in words:
        if current_length + len(word) + 1 > max_length:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

chunks = split_text(text)
print(f"已将文本分为 {len(chunks)} 个片段进行语音合成...")

temp_files = []

for i, chunk in enumerate(chunks):
    print(f"正在处理第 {i+1}/{len(chunks)} 个片段...")
    temp_file = os.path.join(folder_path, f"temp_part_{i}.mp3")
    
    # slow=False 表示正常语速，lang='en' 表示英语（如果全文是中文可改为 'zh-cn'）
    tts = gTTS(text=chunk, lang='en', slow=False)
    tts.save(temp_file)
    temp_files.append(temp_file)

print(f"正在合并所有音频片段到: {output_audio_path}")
# 直接通过二进制追加合并 MP3 文件，无需安装 ffmpeg
with open(output_audio_path, 'wb') as outfile:
    for temp_file in temp_files:
        with open(temp_file, 'rb') as infile:
            outfile.write(infile.read())
        # 用完后删除临时文件
        os.remove(temp_file)

print("音频生成完毕！")