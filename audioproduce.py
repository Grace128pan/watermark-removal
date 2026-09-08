import asyncio
import os
import re
import subprocess
import imageio_ffmpeg
from edge_tts import Communicate

# 获取内置的 ffmpeg 路径，完全抛弃 pydub 和 ffprobe 依赖
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

DIALOGUE_TEXT = """
W: Morning, this is TGC!
M: Good morning, Walter Barry here, calling from London. Could I speak to Mr. Grand, please?
W: Who’s calling, please?
M: Walter Barry, from London.
W: What is it about, please?
M: Well,  I understand that your company has a chemical processing plant. My own company LCP, Liquid Control Products, is a leader in safety from leaks in the field of chemical processing. I’d like to speak to Mr. Grand to discuss ways in which we could help TGC protect itself from such problems and save money at the same time.
W: Yes, I see. Well, Mr. Grand is not available just now.
M: Can you tell me when I could reach him?
W: He’s very busy for the next few days. Then he’ll be away in New York. So it’s difficult to give you a time.
M: Could I speak to someone else, perhaps?
W: Who, in particular?
M: A colleague, for example?
W: You are speaking to his personal assistant. I can deal with calls for Mr. Grand.
M: Yes, well, could I ring him tomorrow?
W: No, I’m sorry. He won’t be free tomorrow. Listen, let me suggest something. You send us details of your products and services, together with references from other companies. And then we’ll contact you.
M: Yes, that’s very kind of you. I have your address.
W: Very good, Mr….?
M: Barry. Walter Barry, from LCP in London.
W: Right, Mr. Barry. We look forward to hearing from you.
M: Thank you. Goodbye.
W: Bye.
"""

OUTPUT_FILE = r"C:\Users\grace\VisualStudioProject\watermark-removal\dialogue_output.mp3"
LIST_FILE = r"C:\Users\grace\VisualStudioProject\watermark-removal\file_list.txt"

VOICE_FEMALE = "en-US-AriaNeural"
VOICE_MALE = "en-US-ChristopherNeural"

async def main():
    lines = DIALOGUE_TEXT.strip().split("\n")
    temp_files = []

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        match = re.match(r"^(W|M)\s*[:：]\s*(.*)$", line, re.IGNORECASE)
        if not match:
            continue

        speaker, text = match.groups()
        voice = VOICE_FEMALE if speaker.upper() == "W" else VOICE_MALE
        temp_file = os.path.join(r"C:\Users\grace\VisualStudioProject\watermark-removal", f"temp_{i}.mp3")
        temp_files.append(temp_file)

        print(f"正在生成 [{speaker.upper()}]: {text}")
        communicate = Communicate(text, voice)
        await communicate.save(temp_file)

    if not temp_files:
        print("错误：没有匹配到任何对话内容。")
        return

    print("正在合并音频文件...")
    with open(LIST_FILE, "w", encoding="utf-8") as f:
        for tf in temp_files:
            rel_name = os.path.basename(tf)
            f.write(f"file '{rel_name}'\n")

    cmd = [
        FFMPEG_EXE,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", LIST_FILE,
        "-c", "copy",
        OUTPUT_FILE
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"FFmpeg 拼接出错: {result.stderr}")
    else:
        print(f"对话音频生成成功，已保存至: {OUTPUT_FILE}")

    if os.path.exists(LIST_FILE):
        os.remove(LIST_FILE)
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)

if __name__ == "__main__":
    asyncio.run(main())